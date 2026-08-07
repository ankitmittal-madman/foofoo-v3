-- Canonical dish IDs added to historical feedback are factual and intentionally retained.
-- Application rollback must precede dropping the resolver RPC.
DROP FUNCTION IF EXISTS public.resolve_canonical_dish_identity(text);
