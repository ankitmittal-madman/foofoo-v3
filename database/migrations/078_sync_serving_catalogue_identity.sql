-- Close the identity drift between the immutable 810-item RE bundle and public.dishes (802 rows).
--
-- These eight dishes were already eligible for serving from the baked recommendation catalogue,
-- but feedback could not resolve them to a UUID. They are inserted as INACTIVE identity shells:
-- feedback and aliases can reference a canonical row immediately, while no database-backed
-- serving path may treat them as eligible until the existing enrichment workflow verifies their
-- ingredients and activates them. This avoids fabricating derived allergen/Jain fields.

WITH missing_dishes(name, meal_occasion, cook_time_minutes, difficulty, cuisine, calories, serving_size) AS (
  VALUES
    ('Chholar Dal with Luchi', ARRAY['breakfast','lunch']::text[], 40, 'beginner', 'bengali', 400, '1 plate'),
    ('Daal Bafla', ARRAY['lunch','dinner']::text[], 60, 'intermediate', 'madhya_pradesh', 500, '1 plate'),
    ('Dal Pakwan', ARRAY['breakfast']::text[], 45, 'intermediate', 'sindhi', 400, '1 plate'),
    ('Pithla Bhakri', ARRAY['lunch','dinner']::text[], 20, 'beginner', 'maharashtrian', 300, '1 plate'),
    ('Poha Jalebi (Indori)', ARRAY['breakfast']::text[], 25, 'beginner', 'indori', 400, '1 plate'),
    ('Sadya Thali', ARRAY['lunch']::text[], 120, 'advanced', 'kerala', 800, '1 thali'),
    ('Thali Meals (South Indian)', ARRAY['lunch','dinner']::text[], 60, 'intermediate', 'tamil', 650, '1 thali'),
    ('Zunka Bhakri', ARRAY['lunch','dinner']::text[], 30, 'beginner', 'maharashtrian', 300, '1 plate')
)
INSERT INTO public.dishes (
  name,
  description,
  meal_occasion,
  cook_time_minutes,
  difficulty,
  cuisine_id,
  calories,
  serving_size,
  is_active,
  ontology_status
)
SELECT
  source.name,
  'Canonical identity synchronized from the active recommendation serving catalogue; pending ingredient enrichment.',
  source.meal_occasion,
  source.cook_time_minutes,
  source.difficulty,
  cuisine.id,
  source.calories,
  source.serving_size,
  false,
  'pending'
FROM missing_dishes source
LEFT JOIN public.cuisines cuisine ON lower(cuisine.name) = source.cuisine
ON CONFLICT (name) DO NOTHING;
