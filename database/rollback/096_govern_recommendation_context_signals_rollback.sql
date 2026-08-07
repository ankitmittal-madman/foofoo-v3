DROP FUNCTION IF EXISTS public.correct_governed_context_signal(uuid, text, text, jsonb);
DROP FUNCTION IF EXISTS public.get_governed_context_signals(uuid);
DROP FUNCTION IF EXISTS public.materialize_governed_context_signals(uuid, jsonb);
DROP TABLE IF EXISTS re_engine.governed_context_signals;
