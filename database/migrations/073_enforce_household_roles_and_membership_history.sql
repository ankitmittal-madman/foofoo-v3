-- Expand the one-owner compatibility tenant into an enforceable household role model without
-- changing existing household/profile identifiers or recommendation storage contracts.

CREATE TABLE IF NOT EXISTS public.household_membership_events (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  household_id uuid NOT NULL REFERENCES public.households(id) ON DELETE CASCADE,
  user_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  event_type text NOT NULL CHECK (event_type IN (
    'backfilled','invited','activated','role_changed','revoked','left','owner_transferred'
  )),
  previous_role_code text,
  new_role_code text,
  previous_status text,
  new_status text,
  actor_user_id uuid REFERENCES auth.users(id) ON DELETE SET NULL,
  reason_code text,
  occurred_at timestamptz NOT NULL DEFAULT now(),
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_household_membership_events_household_time
  ON public.household_membership_events (household_id, occurred_at DESC);
CREATE INDEX IF NOT EXISTS idx_household_membership_events_user_time
  ON public.household_membership_events (user_id, occurred_at DESC);

INSERT INTO public.household_membership_events (
  household_id, user_id, event_type, new_role_code, new_status, occurred_at,
  metadata
)
SELECT hm.household_id, hm.user_id, 'backfilled', hm.role_code, hm.status, hm.joined_at,
       jsonb_build_object('source', 'migration_073')
FROM public.household_memberships hm
WHERE NOT EXISTS (
  SELECT 1 FROM public.household_membership_events e
  WHERE e.household_id = hm.household_id AND e.user_id = hm.user_id
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_household_one_active_owner
  ON public.household_memberships (household_id)
  WHERE role_code = 'owner' AND status = 'active';
CREATE INDEX IF NOT EXISTS idx_household_memberships_user_active
  ON public.household_memberships (user_id, household_id)
  WHERE status = 'active';

CREATE OR REPLACE FUNCTION public.assert_household_has_one_owner()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, public
AS $function$
DECLARE
  target_household_id uuid;
  household_exists boolean;
  active_owner_count integer;
BEGIN
  target_household_id := CASE
    WHEN TG_TABLE_NAME = 'households' THEN
      coalesce((to_jsonb(NEW)->>'id')::uuid, (to_jsonb(OLD)->>'id')::uuid)
    ELSE
      coalesce(
        (to_jsonb(NEW)->>'household_id')::uuid,
        (to_jsonb(OLD)->>'household_id')::uuid
      )
  END;

  SELECT EXISTS (
    SELECT 1 FROM public.households h
    WHERE h.id = target_household_id AND h.status <> 'deleting'
  ) INTO household_exists;
  IF NOT household_exists THEN
    RETURN coalesce(NEW, OLD);
  END IF;

  SELECT count(*) INTO active_owner_count
  FROM public.household_memberships hm
  WHERE hm.household_id = target_household_id
    AND hm.role_code = 'owner'
    AND hm.status = 'active';
  IF active_owner_count <> 1 THEN
    RAISE EXCEPTION 'household % must have exactly one active owner', target_household_id
      USING ERRCODE = '23514';
  END IF;
  IF TG_OP = 'DELETE' THEN RETURN OLD; END IF;
  RETURN NEW;
END
$function$;

REVOKE EXECUTE ON FUNCTION public.assert_household_has_one_owner()
  FROM PUBLIC, anon, authenticated;

DROP TRIGGER IF EXISTS household_memberships_one_owner ON public.household_memberships;
CREATE CONSTRAINT TRIGGER household_memberships_one_owner
AFTER INSERT OR UPDATE OR DELETE ON public.household_memberships
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION public.assert_household_has_one_owner();

DROP TRIGGER IF EXISTS households_one_owner ON public.households;
CREATE CONSTRAINT TRIGGER households_one_owner
AFTER INSERT OR UPDATE ON public.households
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION public.assert_household_has_one_owner();

CREATE OR REPLACE FUNCTION public.record_household_membership_event()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, public
AS $function$
DECLARE
  event_code text;
  actor_id uuid;
BEGIN
  actor_id := nullif(current_setting('app.actor_user_id', true), '')::uuid;
  IF TG_OP = 'INSERT' THEN
    event_code := CASE WHEN NEW.status = 'invited' THEN 'invited' ELSE 'activated' END;
  ELSIF TG_OP = 'DELETE' THEN
    event_code := CASE WHEN OLD.role_code = 'owner' THEN 'owner_transferred' ELSE 'left' END;
  ELSIF OLD.role_code IS DISTINCT FROM NEW.role_code THEN
    event_code := CASE WHEN NEW.role_code = 'owner' OR OLD.role_code = 'owner'
      THEN 'owner_transferred' ELSE 'role_changed' END;
  ELSIF OLD.status IS DISTINCT FROM NEW.status THEN
    event_code := CASE
      WHEN NEW.status = 'active' THEN 'activated'
      WHEN NEW.status = 'revoked' THEN 'revoked'
      ELSE 'left'
    END;
  ELSE
    RETURN NEW;
  END IF;

  INSERT INTO public.household_membership_events (
    household_id, user_id, event_type, previous_role_code, new_role_code,
    previous_status, new_status, actor_user_id
  ) VALUES (
    coalesce(NEW.household_id, OLD.household_id),
    coalesce(NEW.user_id, OLD.user_id),
    event_code,
    CASE WHEN TG_OP = 'INSERT' THEN NULL ELSE OLD.role_code END,
    CASE WHEN TG_OP = 'DELETE' THEN NULL ELSE NEW.role_code END,
    CASE WHEN TG_OP = 'INSERT' THEN NULL ELSE OLD.status END,
    CASE WHEN TG_OP = 'DELETE' THEN NULL ELSE NEW.status END,
    actor_id
  );
  IF TG_OP = 'DELETE' THEN RETURN OLD; END IF;
  RETURN NEW;
END
$function$;

REVOKE EXECUTE ON FUNCTION public.record_household_membership_event()
  FROM PUBLIC, anon, authenticated;

DROP TRIGGER IF EXISTS household_memberships_record_event ON public.household_memberships;
CREATE TRIGGER household_memberships_record_event
AFTER INSERT OR UPDATE OR DELETE ON public.household_memberships
FOR EACH ROW EXECUTE FUNCTION public.record_household_membership_event();

CREATE OR REPLACE FUNCTION public.has_household_role(
  p_household_id uuid,
  p_user_id uuid,
  p_allowed_roles text[] DEFAULT ARRAY['owner','planner','cook','member','viewer']::text[]
)
RETURNS boolean
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = pg_catalog, public
AS $function$
  SELECT EXISTS (
    SELECT 1 FROM public.household_memberships hm
    WHERE hm.household_id = p_household_id
      AND hm.user_id = p_user_id
      AND hm.status = 'active'
      AND hm.role_code = ANY (p_allowed_roles)
      -- Initial hardening retained here as deployed; migration 074 replaces
      -- this function because current_user is the definer inside this body.
      AND (
        current_user IN ('postgres', 'service_role', 'supabase_admin')
        OR p_user_id = (SELECT auth.uid())
      )
  )
$function$;

REVOKE ALL ON FUNCTION public.has_household_role(uuid, uuid, text[]) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.has_household_role(uuid, uuid, text[])
  TO authenticated, service_role;

CREATE OR REPLACE FUNCTION public.transfer_household_ownership(
  p_household_id uuid,
  p_actor_user_id uuid,
  p_new_owner_user_id uuid
)
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, public
AS $function$
DECLARE
  current_owner uuid;
BEGIN
  PERFORM set_config('app.actor_user_id', p_actor_user_id::text, true);
  SELECT h.owner_user_id INTO current_owner
  FROM public.households h WHERE h.id = p_household_id FOR UPDATE;
  IF current_owner IS NULL OR current_owner <> p_actor_user_id THEN
    RAISE EXCEPTION 'only the active owner may transfer ownership' USING ERRCODE = '42501';
  END IF;
  IF current_owner = p_new_owner_user_id THEN RETURN; END IF;
  IF NOT public.has_household_role(
    p_household_id, p_new_owner_user_id, ARRAY['planner','cook','member','viewer']::text[]
  ) THEN
    RAISE EXCEPTION 'new owner must be an active household member' USING ERRCODE = '23514';
  END IF;

  UPDATE public.household_memberships
  SET role_code = 'planner'
  WHERE household_id = p_household_id AND user_id = current_owner AND status = 'active';
  UPDATE public.household_memberships
  SET role_code = 'owner'
  WHERE household_id = p_household_id AND user_id = p_new_owner_user_id AND status = 'active';
  UPDATE public.households
  SET owner_user_id = p_new_owner_user_id, updated_at = now()
  WHERE id = p_household_id;
END
$function$;

CREATE OR REPLACE FUNCTION public.change_household_member_role(
  p_household_id uuid,
  p_actor_user_id uuid,
  p_target_user_id uuid,
  p_new_role_code text
)
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, public
AS $function$
BEGIN
  PERFORM set_config('app.actor_user_id', p_actor_user_id::text, true);
  IF NOT public.has_household_role(p_household_id, p_actor_user_id, ARRAY['owner']::text[]) THEN
    RAISE EXCEPTION 'only the active owner may change roles' USING ERRCODE = '42501';
  END IF;
  IF p_new_role_code NOT IN ('planner','cook','member','viewer') THEN
    RAISE EXCEPTION 'owner transfer uses transfer_household_ownership' USING ERRCODE = '23514';
  END IF;
  UPDATE public.household_memberships
  SET role_code = p_new_role_code
  WHERE household_id = p_household_id AND user_id = p_target_user_id
    AND status = 'active' AND role_code <> 'owner';
  IF NOT FOUND THEN RAISE EXCEPTION 'active non-owner membership not found' USING ERRCODE = 'P0002'; END IF;
END
$function$;

CREATE OR REPLACE FUNCTION public.revoke_household_membership(
  p_household_id uuid,
  p_actor_user_id uuid,
  p_target_user_id uuid
)
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, public
AS $function$
BEGIN
  PERFORM set_config('app.actor_user_id', p_actor_user_id::text, true);
  IF NOT public.has_household_role(p_household_id, p_actor_user_id, ARRAY['owner']::text[]) THEN
    RAISE EXCEPTION 'only the active owner may revoke memberships' USING ERRCODE = '42501';
  END IF;
  UPDATE public.household_memberships
  SET status = 'revoked', revoked_at = now()
  WHERE household_id = p_household_id AND user_id = p_target_user_id
    AND status = 'active' AND role_code <> 'owner';
  IF NOT FOUND THEN RAISE EXCEPTION 'active non-owner membership not found' USING ERRCODE = 'P0002'; END IF;
END
$function$;

CREATE OR REPLACE FUNCTION public.leave_household(
  p_household_id uuid,
  p_actor_user_id uuid
)
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, public
AS $function$
BEGIN
  PERFORM set_config('app.actor_user_id', p_actor_user_id::text, true);
  UPDATE public.household_memberships
  SET status = 'revoked', revoked_at = now()
  WHERE household_id = p_household_id AND user_id = p_actor_user_id
    AND status = 'active' AND role_code <> 'owner';
  IF NOT FOUND THEN
    RAISE EXCEPTION 'active owner must transfer ownership before leaving' USING ERRCODE = '23514';
  END IF;
END
$function$;

CREATE OR REPLACE FUNCTION public.create_household_invite(
  p_household_id uuid,
  p_actor_user_id uuid,
  p_token_hash text,
  p_invited_role text,
  p_expires_at timestamptz
)
RETURNS uuid
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, public
AS $function$
DECLARE invite_id uuid;
BEGIN
  IF NOT public.has_household_role(p_household_id, p_actor_user_id, ARRAY['owner']::text[]) THEN
    RAISE EXCEPTION 'only the active owner may invite members' USING ERRCODE = '42501';
  END IF;
  IF p_invited_role NOT IN ('planner','cook','member','viewer') OR p_expires_at <= now() THEN
    RAISE EXCEPTION 'invalid invite role or expiry' USING ERRCODE = '23514';
  END IF;
  INSERT INTO public.household_invites (
    household_id, token_hash, invited_role, invited_by, expires_at
  ) VALUES (p_household_id, p_token_hash, p_invited_role, p_actor_user_id, p_expires_at)
  RETURNING id INTO invite_id;
  RETURN invite_id;
END
$function$;

CREATE OR REPLACE FUNCTION public.accept_household_invite(
  p_token_hash text,
  p_actor_user_id uuid
)
RETURNS uuid
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, public
AS $function$
DECLARE invitation public.household_invites%ROWTYPE;
BEGIN
  PERFORM set_config('app.actor_user_id', p_actor_user_id::text, true);
  SELECT * INTO invitation FROM public.household_invites
  WHERE token_hash = p_token_hash AND accepted_at IS NULL AND revoked_at IS NULL
    AND expires_at > now()
  FOR UPDATE;
  IF invitation.id IS NULL THEN RAISE EXCEPTION 'invite not found or expired' USING ERRCODE = 'P0002'; END IF;

  INSERT INTO public.household_memberships (
    household_id, user_id, role_code, status, joined_at, revoked_at
  ) VALUES (
    invitation.household_id, p_actor_user_id, invitation.invited_role, 'active', now(), NULL
  )
  ON CONFLICT (household_id, user_id) DO UPDATE
    SET role_code = EXCLUDED.role_code, status = 'active', joined_at = now(), revoked_at = NULL;
  UPDATE public.household_invites SET accepted_at = now() WHERE id = invitation.id;
  RETURN invitation.household_id;
END
$function$;

DO $$
DECLARE signature text;
BEGIN
  FOREACH signature IN ARRAY ARRAY[
    'public.transfer_household_ownership(uuid,uuid,uuid)',
    'public.change_household_member_role(uuid,uuid,uuid,text)',
    'public.revoke_household_membership(uuid,uuid,uuid)',
    'public.leave_household(uuid,uuid)',
    'public.create_household_invite(uuid,uuid,text,text,timestamptz)',
    'public.accept_household_invite(text,uuid)'
  ] LOOP
    EXECUTE format('REVOKE ALL ON FUNCTION %s FROM PUBLIC, anon, authenticated', signature);
    EXECUTE format('GRANT EXECUTE ON FUNCTION %s TO service_role', signature);
  END LOOP;
END $$;

ALTER TABLE public.household_membership_events ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.household_membership_events FROM anon, authenticated;
GRANT SELECT ON public.household_membership_events TO authenticated;

DROP POLICY IF EXISTS households_select_member ON public.households;
CREATE POLICY households_select_member ON public.households FOR SELECT USING (
  public.has_household_role(id, (SELECT auth.uid()))
);
DROP POLICY IF EXISTS memberships_select_self ON public.household_memberships;
CREATE POLICY memberships_select_household ON public.household_memberships FOR SELECT USING (
  public.has_household_role(household_id, (SELECT auth.uid()))
);
DROP POLICY IF EXISTS invites_select_member ON public.household_invites;
CREATE POLICY invites_select_owner ON public.household_invites FOR SELECT USING (
  public.has_household_role(household_id, (SELECT auth.uid()), ARRAY['owner']::text[])
);
CREATE POLICY membership_events_select_household ON public.household_membership_events FOR SELECT USING (
  public.has_household_role(household_id, (SELECT auth.uid()))
);

CREATE OR REPLACE FUNCTION public.provision_profile_household()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, public
AS $function$
BEGIN
  PERFORM set_config('app.actor_user_id', NEW.id::text, true);
  INSERT INTO public.households (
    id, name, household_type_code, owner_user_id, created_at, updated_at
  ) VALUES (
    NEW.id, coalesce(nullif(NEW.primary_cook_name, ''), 'My household'), NULL,
    NEW.id, NEW.created_at, NEW.updated_at
  )
  ON CONFLICT (id) DO UPDATE SET
    updated_at = greatest(public.households.updated_at, EXCLUDED.updated_at);

  INSERT INTO public.household_memberships (
    household_id, user_id, role_code, status, joined_at, revoked_at
  ) VALUES (NEW.id, NEW.id, 'owner', 'active', NEW.created_at, NULL)
  ON CONFLICT (household_id, user_id) DO UPDATE SET
    role_code = 'owner', status = 'active', revoked_at = NULL;
  UPDATE public.households SET owner_user_id = NEW.id WHERE id = NEW.id;
  RETURN NEW;
END
$function$;
