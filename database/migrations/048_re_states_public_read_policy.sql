-- Migration: 048_re_states_public_read_policy.sql
-- WP-20 follow-up (found by /audit-rls immediately after 046 shipped): public.re_states was
-- re-homed by migration 046 as "reference vocabulary... left readable like other public reference
-- data" (046's own comment), but 046 only cloned the table (`LIKE ... INCLUDING ALL`) and never
-- created a SELECT policy for it. Supabase's platform `ensure_rls` event trigger auto-enables RLS
-- on every newly created public table — so re_states landed with RLS ON and ZERO policies, which
-- means (Postgres RLS semantics: no policy = no rows) it was silently unreadable by anon/
-- authenticated/public despite the stated intent, immediately upon creation. Every other reference
-- table in public (cuisines, dish_tags, ingredients, meal_classes) has exactly this policy —
-- re_states was simply missing it. This does not change any access this table ever actually had in
-- production (the gap existed from the moment 046 ran); it completes 046's own stated intent.

CREATE POLICY re_states_public_read ON public.re_states FOR SELECT USING (true);
