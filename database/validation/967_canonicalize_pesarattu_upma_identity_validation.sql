DO $validate$
DECLARE
  v_canonical_id uuid;
  v_resolved_id uuid;
  v_resolved_name text;
BEGIN
  SELECT id INTO STRICT v_canonical_id
  FROM public.dishes
  WHERE name = 'Pesarattu Upma' AND is_active;

  IF EXISTS (SELECT 1 FROM public.dishes WHERE name = 'Pesarattu MLC') THEN
    RAISE EXCEPTION 'Pesarattu MLC remains a canonical dish name';
  END IF;
  IF NOT EXISTS (
    SELECT 1 FROM public.dishes
    WHERE name = 'Pesarattu MLC [retired duplicate]' AND NOT is_active
  ) THEN
    RAISE EXCEPTION 'retired Pesarattu duplicate is not preserved inactive';
  END IF;

  SELECT dish_id, canonical_name
  INTO v_resolved_id, v_resolved_name
  FROM public.resolve_canonical_dish_identity('Pesarattu MLC');
  IF v_resolved_id IS DISTINCT FROM v_canonical_id
     OR v_resolved_name IS DISTINCT FROM 'Pesarattu Upma' THEN
    RAISE EXCEPTION 'historical Pesarattu MLC alias does not resolve canonically';
  END IF;

  SELECT dish_id, canonical_name
  INTO v_resolved_id, v_resolved_name
  FROM public.resolve_canonical_dish_identity('MLA Pesarattu');
  IF v_resolved_id IS DISTINCT FROM v_canonical_id
     OR v_resolved_name IS DISTINCT FROM 'Pesarattu Upma' THEN
    RAISE EXCEPTION 'MLA Pesarattu alias does not resolve canonically';
  END IF;
END
$validate$;
