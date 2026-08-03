-- Rollback: 048_re_states_public_read_policy.sql
DROP POLICY IF EXISTS re_states_public_read ON public.re_states;
