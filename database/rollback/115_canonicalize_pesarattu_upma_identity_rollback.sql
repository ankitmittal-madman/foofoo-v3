DO $rollback$
DECLARE
  v_canonical_id uuid;
BEGIN
  SELECT id INTO v_canonical_id FROM public.dishes WHERE name = 'Pesarattu Upma';

  DELETE FROM public.dish_aliases
  WHERE dish_id = v_canonical_id
    AND alias_text = 'Pesarattu MLC'
    AND alias_source = 'dedupe_merge';
  DELETE FROM public.dish_name_synonyms
  WHERE dish_id = v_canonical_id
    AND synonym = 'MLA Pesarattu'
    AND source_url = 'https://www.slurrp.com/slurrp360/regional/pesarattu-1665403098313';

  UPDATE public.dishes
  SET name = 'Pesarattu MLC',
      is_active = true
  WHERE name = 'Pesarattu MLC [retired duplicate]'
    AND NOT is_active;
END
$rollback$;
