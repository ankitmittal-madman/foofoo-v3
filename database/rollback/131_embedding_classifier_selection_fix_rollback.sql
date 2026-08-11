-- Rollback for 131_embedding_classifier_selection_fix.sql
DROP FUNCTION IF EXISTS public.dishes_pending_embedding_classification(integer);
