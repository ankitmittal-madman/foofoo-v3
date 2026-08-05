"""Compile Foofoo's checked-in catalogue/recipe evidence into normalized food intelligence SQL."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CATALOGUE = ROOT / "ghar_re_service/data/bundle/catalogue.json"
RECIPES = ROOT / "data/source/recipes_v1.json"
OUTPUT = ROOT / "database/seeds/147_seed_comprehensive_food_intelligence.sql"


def _json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def _code(value: object) -> str:
    text = re.sub(r"[^a-z0-9]+", "_", str(value).strip().casefold()).strip("_")
    return text or "unknown"


def build_seed() -> str:
    catalogue: list[dict[str, object]] = json.loads(CATALOGUE.read_text(encoding="utf-8"))
    recipes: dict[str, dict[str, object]] = json.loads(RECIPES.read_text(encoding="utf-8"))

    terms: set[tuple[str, str, str]] = set()
    aliases: list[dict[str, object]] = []
    constraints: list[dict[str, object]] = []
    regions: list[dict[str, object]] = []
    nutrients: list[dict[str, object]] = []
    feature_edges: list[dict[str, object]] = []
    recipe_rows: list[dict[str, object]] = []

    dimensions = {
        "cuisine": "cuisine",
        "cooking_method": "cooking_method",
        "texture": "texture",
        "richness": "richness",
        "weather_affinity": "weather_affinity",
        "meal_type": "slot",
        "hero_role": "item_role",
        "state_origin": "regional_affinity",
        "dish_category": "external_food_term",
        "primary_taste": "external_food_term",
        "aroma_profile": "external_food_term",
        "mouthfeel": "external_food_term",
    }
    predicate = {
        "cuisine": "has_tag",
        "cooking_method": "uses_technique",
        "texture": "has_tag",
        "richness": "has_tag",
        "weather_affinity": "suitable_in",
        "meal_type": "suitable_in",
        "hero_role": "has_tag",
        "state_origin": "originates_in",
        "dish_category": "has_tag",
        "primary_taste": "has_tag",
        "aroma_profile": "has_tag",
        "mouthfeel": "has_tag",
    }

    for dish in catalogue:
        name = str(dish["name"])
        for alias in sorted({str(x).strip() for key in ("synonyms", "alternate_names") for x in dish.get(key, []) if str(x).strip()}):
            if alias.casefold() != name.casefold():
                aliases.append({"dish": name, "alias": alias})

        diet = str(dish.get("diet") or "unknown")
        constraints.append({"dish": name, "code": f"diet:{_code(diet)}", "suitability": "allowed"})
        constraints.append({"dish": name, "code": "jain", "suitability": "allowed" if dish.get("jain_compatible") == "Y" else "excluded"})
        constraints.append({"dish": name, "code": "farali", "suitability": "allowed" if dish.get("farali_compatible") is True else "excluded"})

        if dish.get("state_origin"):
            regions.append({"dish": name, "region": _code(dish["state_origin"]), "score": 0.95})
        if dish.get("cuisine"):
            regions.append({"dish": name, "region": f"cuisine:{_code(dish['cuisine'])}", "score": 0.8})

        macro = dict(dish.get("macro") or {})
        macro.setdefault("calories", dish.get("calories"))
        for key, unit in (("calories", "kcal"), ("protein_g", "g"), ("carbs_g", "g"), ("fat_g", "g"), ("fibre_g", "g"), ("sodium_mg", "mg"), ("sugar_g", "g")):
            value = macro.get(key)
            if isinstance(value, (int, float)) and value >= 0:
                nutrients.append({"dish": name, "code": key, "unit": unit, "value": value, "basis": str(dish.get("serving_size") or "1 serving")})

        for field, dimension in dimensions.items():
            raw = dish.get(field)
            values = raw if isinstance(raw, list) else ([] if raw in (None, "") else [raw])
            for value in values:
                code = _code(value)
                terms.add((dimension, code, str(value)))
                feature_edges.append({"dish": name, "target": f"term:{dimension}:{code}", "predicate": predicate[field]})

        recipe = recipes.get(name)
        if recipe:
            recipe_rows.append({
                "dish": name,
                "title": name,
                "servings": 1,
                "total": recipe.get("total_mins"),
                "active": recipe.get("prep_mins"),
                "ingredients": recipe.get("ingredients", []),
                "steps": recipe.get("steps", []),
                "source": recipe.get("method_source", "unknown"),
            })

    return f"""-- Seed: 147_seed_comprehensive_food_intelligence.sql
-- Generated deterministically from catalogue.json and recipes_v1.json after migration 061.

WITH rows AS (SELECT * FROM jsonb_to_recordset($json${_json([{"dimension": d, "code": c, "name": n} for d,c,n in sorted(terms)])}$json$::jsonb) AS x(dimension text, code text, name text))
INSERT INTO public.taxonomy_terms(dimension, code, display_name)
SELECT dimension, code, name FROM rows ON CONFLICT (dimension, code) DO UPDATE SET display_name=excluded.display_name;

WITH rows AS (SELECT * FROM jsonb_to_recordset($json${_json(aliases)}$json$::jsonb) AS x(dish text, alias text))
INSERT INTO public.dish_name_synonyms(dish_id,synonym,data_source,alias_type,confidence)
SELECT d.id, rows.alias, 'ai_generated', 'common_name', 0.800 FROM rows JOIN public.dishes d ON lower(d.name)=lower(rows.dish)
ON CONFLICT (dish_id,synonym) DO NOTHING;

WITH rows AS (SELECT * FROM jsonb_to_recordset($json${_json(constraints)}$json$::jsonb) AS x(dish text, code text, suitability text))
INSERT INTO public.dish_constraints(dish_id,constraint_code,suitability,confidence,source_name,source_type,review_status)
SELECT d.id,rows.code,rows.suitability,0.900,'bundle/catalogue.json','internal_research','provisional' FROM rows JOIN public.dishes d ON lower(d.name)=lower(rows.dish)
ON CONFLICT (dish_id,constraint_code) DO UPDATE SET suitability=excluded.suitability,confidence=excluded.confidence,updated_at=now() WHERE public.dish_constraints.review_status<>'accepted';

WITH rows AS (SELECT * FROM jsonb_to_recordset($json${_json(regions)}$json$::jsonb) AS x(dish text, region text, score numeric))
INSERT INTO public.dish_regional_affinities(dish_id,region_code,affinity_score,confidence,source_name,source_type,review_status)
SELECT d.id,rows.region,rows.score,0.900,'bundle/catalogue.json','internal_research','provisional' FROM rows JOIN public.dishes d ON lower(d.name)=lower(rows.dish)
ON CONFLICT (dish_id,region_code) DO UPDATE SET affinity_score=excluded.affinity_score,confidence=excluded.confidence,updated_at=now() WHERE public.dish_regional_affinities.review_status<>'accepted';

INSERT INTO food.nutrients(nutrient_code,display_name,unit_code,source_name,source_version) VALUES
('calories','Energy','kcal','bundle/catalogue.json','v1'),('protein_g','Protein','g','bundle/catalogue.json','v1'),('carbs_g','Carbohydrate','g','bundle/catalogue.json','v1'),('fat_g','Fat','g','bundle/catalogue.json','v1'),('fibre_g','Fibre','g','bundle/catalogue.json','v1'),('sodium_mg','Sodium','mg','bundle/catalogue.json','v1'),('sugar_g','Sugar','g','bundle/catalogue.json','v1') ON CONFLICT (nutrient_code) DO NOTHING;

WITH rows AS (SELECT * FROM jsonb_to_recordset($json${_json(nutrients)}$json$::jsonb) AS x(dish text,code text,unit text,value numeric,basis text))
INSERT INTO food.nutrient_assertions(id,dish_id,nutrient_id,expected_value,serving_basis,method_code,source_name,confidence,review_status)
SELECT md5('catalogue-nutrient:'||d.id||':'||rows.code)::uuid,d.id,n.id,rows.value,rows.basis,'catalogue_estimate','bundle/catalogue.json',0.700,'provisional' FROM rows JOIN public.dishes d ON lower(d.name)=lower(rows.dish) JOIN food.nutrients n ON n.nutrient_code=rows.code
ON CONFLICT (id) DO UPDATE SET expected_value=excluded.expected_value,serving_basis=excluded.serving_basis;

INSERT INTO food.ontology_nodes(node_code,node_type,canonical_entity_id,label,status,source_name,source_version,confidence,review_status)
SELECT 'dish:'||d.id,'dish',d.id,d.name,'active','public.dishes','live',1,'accepted' FROM public.dishes d ON CONFLICT(node_code) DO NOTHING;
INSERT INTO food.ontology_nodes(node_code,node_type,canonical_entity_id,label,status,source_name,source_version,confidence,review_status)
SELECT 'ingredient:'||i.id,'ingredient',i.id,i.name,'active','public.ingredients','live',1,'accepted' FROM public.ingredients i ON CONFLICT(node_code) DO NOTHING;
INSERT INTO food.ontology_nodes(node_code,node_type,label,status,source_name,source_version,confidence,review_status)
SELECT 'term:'||t.dimension||':'||t.code, CASE WHEN t.dimension='cuisine' THEN 'cuisine' WHEN t.dimension='cooking_method' THEN 'technique' WHEN t.dimension='regional_affinity' THEN 'region' WHEN t.dimension='slot' THEN 'meal_role' ELSE 'genome_tag' END,t.display_name,'active','public.taxonomy_terms','v1',0.9,'provisional' FROM public.taxonomy_terms t ON CONFLICT(node_code) DO NOTHING;
INSERT INTO food.ontology_nodes(node_code,node_type,label,status,source_name,source_version,confidence,review_status)
SELECT 'class:'||c.class_code,'meal_class',c.display_name,'active','public.meal_classes','live',1,'accepted' FROM public.meal_classes c ON CONFLICT(node_code) DO NOTHING;
INSERT INTO food.ontology_nodes(node_code,node_type,canonical_entity_id,label,status,source_name,source_version,confidence,review_status)
SELECT 'alias:'||s.dish_id||':'||md5(lower(s.synonym)),'dish_variant',s.dish_id,s.synonym,'active','public.dish_name_synonyms','live',coalesce(s.confidence,0.7),CASE WHEN s.data_source='real' THEN 'accepted' ELSE 'provisional' END FROM public.dish_name_synonyms s ON CONFLICT(node_code) DO NOTHING;

WITH rows AS (SELECT * FROM jsonb_to_recordset($json${_json(feature_edges)}$json$::jsonb) AS x(dish text,target text,predicate text))
INSERT INTO food.ontology_edges(subject_node_id,predicate_code,object_node_id,confidence,source_name,source_version,review_status)
SELECT dn.id,rows.predicate,tn.id,0.9,'bundle/catalogue.json','v1','provisional' FROM rows JOIN public.dishes d ON lower(d.name)=lower(rows.dish) JOIN food.ontology_nodes dn ON dn.node_code='dish:'||d.id JOIN food.ontology_nodes tn ON tn.node_code=rows.target ON CONFLICT DO NOTHING;
INSERT INTO food.ontology_edges(subject_node_id,predicate_code,object_node_id,confidence,source_name,source_version,review_status)
SELECT dn.id,CASE WHEN di.is_main_ingredient THEN 'main_ingredient' ELSE 'contains' END,inn.id,1,'public.dish_ingredients','live','accepted' FROM public.dish_ingredients di JOIN food.ontology_nodes dn ON dn.node_code='dish:'||di.dish_id JOIN food.ontology_nodes inn ON inn.node_code='ingredient:'||di.ingredient_id ON CONFLICT DO NOTHING;
INSERT INTO food.ontology_edges(subject_node_id,predicate_code,object_node_id,scope_region_code,confidence,source_name,source_version,review_status)
SELECT dn.id,'belongs_to_class',cn.id,m.slot,m.confidence,m.source_name,'v1',m.review_status FROM public.dish_meal_class_mappings m JOIN food.ontology_nodes dn ON dn.node_code='dish:'||m.dish_id JOIN food.ontology_nodes cn ON cn.node_code='class:'||m.class_code ON CONFLICT DO NOTHING;
INSERT INTO food.ontology_edges(subject_node_id,predicate_code,object_node_id,confidence,source_name,source_version,review_status)
SELECT an.id,'alias_of',dn.id,an.confidence,an.source_name,an.source_version,an.review_status FROM food.ontology_nodes an JOIN food.ontology_nodes dn ON dn.node_code='dish:'||an.canonical_entity_id WHERE an.node_type='dish_variant' ON CONFLICT DO NOTHING;

WITH rows AS (SELECT * FROM jsonb_to_recordset($json${_json(recipe_rows)}$json$::jsonb) AS x(dish text,title text,servings numeric,total integer,active integer,ingredients jsonb,steps jsonb,source text)), inserted AS (
INSERT INTO food.recipes(id,dish_id,title,servings,total_time_minutes,active_time_minutes,instructions_status,data_origin,source_version,confidence,review_status,version)
SELECT md5('recipe-v1:'||d.id)::uuid,d.id,rows.title,rows.servings,rows.total,rows.active,'draft','ai_generated',rows.source,0.55,'draft',1 FROM rows JOIN public.dishes d ON lower(d.name)=lower(rows.dish)
ON CONFLICT(dish_id,locale,version) DO UPDATE SET total_time_minutes=excluded.total_time_minutes,active_time_minutes=excluded.active_time_minutes RETURNING id,dish_id)
SELECT count(*) FROM inserted;

WITH rows AS (SELECT * FROM jsonb_to_recordset($json${_json(recipe_rows)}$json$::jsonb) AS x(dish text,title text,servings numeric,total integer,active integer,ingredients jsonb,steps jsonb,source text))
INSERT INTO food.recipe_steps(recipe_id,step_number,instruction)
SELECT r.id,(s.ordinality)::smallint,s.value #>> '{{}}' FROM rows JOIN public.dishes d ON lower(d.name)=lower(rows.dish) JOIN food.recipes r ON r.dish_id=d.id AND r.version=1 CROSS JOIN LATERAL jsonb_array_elements(rows.steps) WITH ORDINALITY s(value,ordinality)
ON CONFLICT(recipe_id,step_number) DO UPDATE SET instruction=excluded.instruction;

WITH rows AS (SELECT * FROM jsonb_to_recordset($json${_json(recipe_rows)}$json$::jsonb) AS x(dish text,title text,servings numeric,total integer,active integer,ingredients jsonb,steps jsonb,source text)), parsed AS (
SELECT rows.dish,trim(split_part(v.value #>> '{{}}',' — ',1)) AS ingredient_name,trim(split_part(v.value #>> '{{}}',' — ',2)) AS preparation FROM rows CROSS JOIN LATERAL jsonb_array_elements(rows.ingredients) v(value))
INSERT INTO food.recipe_ingredients(recipe_id,ingredient_id,preparation,is_optional)
SELECT r.id,i.id,coalesce(nullif(parsed.preparation,''),'unspecified'),false FROM parsed JOIN public.dishes d ON lower(d.name)=lower(parsed.dish) JOIN food.recipes r ON r.dish_id=d.id AND r.version=1 JOIN public.ingredients i ON lower(regexp_replace(i.name,'[^a-z0-9]+','_','g'))=lower(regexp_replace(parsed.ingredient_name,'[^a-z0-9]+','_','g'))
ON CONFLICT(recipe_id,ingredient_id,preparation) DO NOTHING;

INSERT INTO food.plate_grammars(id,grammar_code,display_name,locale_scope,meal_slots,intent_codes,required_roles,optional_roles,burden_prior,data_origin,confidence,review_status,version)
VALUES (md5('grammar:single-primary:v1')::uuid,'SINGLE_PRIMARY','Single primary',ARRAY['IN'],ARRAY['breakfast','lunch','dinner','snack'],ARRAY['ordinary','quick'],jsonb_build_object('primary',1),'{{}}',0.35,'hybrid',0.9,'published',1),
(md5('grammar:base-with-sides:v1')::uuid,'BASE_WITH_SIDES','Base with sides',ARRAY['IN'],ARRAY['lunch','dinner'],ARRAY['ordinary','comfort'],jsonb_build_object('primary',1),jsonb_build_object('side','0..3'),0.55,'hybrid',0.9,'published',1),
(md5('grammar:thali:v1')::uuid,'THALI','Thali',ARRAY['IN'],ARRAY['lunch','dinner'],ARRAY['special','festive'],jsonb_build_object('primary',1),jsonb_build_object('side','1..8'),0.8,'hybrid',0.9,'published',1)
ON CONFLICT(grammar_code) DO NOTHING;

INSERT INTO food.grammar_component_rules(grammar_id,component_role,min_count,max_count,compatibility_expression,sequence,data_origin,confidence,review_status)
SELECT g.id,x.role,x.min_count,x.max_count,x.expression,x.sequence,'hybrid',0.9,'published' FROM food.plate_grammars g JOIN (VALUES
('SINGLE_PRIMARY','primary',1::smallint,1::smallint,'{{}}'::jsonb,0::smallint),
('BASE_WITH_SIDES','primary',1::smallint,1::smallint,'{{}}'::jsonb,0::smallint),
('BASE_WITH_SIDES','side',0::smallint,3::smallint,'{{"distinct_from_primary":true}}'::jsonb,1::smallint),
('THALI','primary',1::smallint,1::smallint,'{{}}'::jsonb,0::smallint),
('THALI','side',1::smallint,8::smallint,'{{"distinct_from_primary":true}}'::jsonb,1::smallint)
) AS x(grammar_code,role,min_count,max_count,expression,sequence) ON x.grammar_code=g.grammar_code
ON CONFLICT(grammar_id,component_role,sequence) DO NOTHING;

INSERT INTO food.meal_episodes(id,episode_code,episode_hash,grammar_id,shared_base_dish_id,intent_codes,richness_prior,effort_prior,catalog_status,data_origin,source_version,confidence,review_status,version)
SELECT md5('single-episode:'||d.id)::uuid,'SINGLE_'||replace(d.id::text,'-',''),md5('single-episode:'||d.id::text),g.id,d.id,ARRAY['ordinary'],least(1,greatest(0,coalesce(d.cook_time_minutes,30)/120.0)),least(1,greatest(0,coalesce(d.cook_time_minutes,30)/120.0)),'published','hybrid','v1',coalesce(d.ontology_confidence,0.7),CASE WHEN d.ontology_status='enriched' THEN 'accepted' ELSE 'provisional' END,1 FROM public.dishes d JOIN food.plate_grammars g ON g.grammar_code='SINGLE_PRIMARY' AND g.version=1
ON CONFLICT(episode_code) DO NOTHING;
INSERT INTO food.meal_episode_components(episode_id,dish_id,recipe_id,component_role,is_required,sequence,adaptation_scope,data_origin,confidence,review_status)
SELECT e.id,e.shared_base_dish_id,r.id,'primary',true,0,'shared','hybrid',e.confidence,e.review_status FROM food.meal_episodes e LEFT JOIN food.recipes r ON r.dish_id=e.shared_base_dish_id AND r.version=1 WHERE e.episode_code LIKE 'SINGLE_%' ON CONFLICT DO NOTHING;

INSERT INTO food.meal_episodes(id,episode_code,episode_hash,grammar_id,intent_codes,richness_prior,effort_prior,catalog_status,data_origin,source_version,confidence,review_status,version)
SELECT md5('combo-episode:'||c.id)::uuid,'COMBO_'||replace(c.id::text,'-',''),md5('combo-episode:'||c.id::text),g.id,ARRAY['ordinary'],CASE WHEN c.combo_type='thali' THEN 0.8 ELSE 0.55 END,CASE WHEN c.combo_type='thali' THEN 0.8 ELSE 0.55 END,'published','hybrid','v1',0.9,'accepted',1 FROM public.dish_combos c JOIN food.plate_grammars g ON g.grammar_code=CASE WHEN c.combo_type='thali' THEN 'THALI' ELSE 'BASE_WITH_SIDES' END AND g.version=1 WHERE c.is_active ON CONFLICT(episode_code) DO NOTHING;
INSERT INTO food.meal_episode_components(episode_id,dish_id,recipe_id,component_role,is_required,sequence,adaptation_scope,data_origin,confidence,review_status)
SELECT e.id,i.dish_id,r.id,i.role,i.is_default,i.sort_order,'shared','hybrid',0.9,'accepted' FROM public.dish_combos c JOIN food.meal_episodes e ON e.episode_code='COMBO_'||replace(c.id::text,'-','') JOIN public.dish_combo_items i ON i.combo_id=c.id LEFT JOIN food.recipes r ON r.dish_id=i.dish_id AND r.version=1 ON CONFLICT DO NOTHING;

INSERT INTO food.episode_workload_features(episode_id,recipe_variant_hash,active_minutes,critical_path_minutes,vessel_count,burner_peak,ingredient_count,rare_ingredient_count,cleanup_score,batchability,leftover_value,feature_version)
SELECT e.id,e.episode_hash,coalesce(sum(r.active_time_minutes),0)::integer,coalesce(max(r.total_time_minutes),0)::integer,greatest(1,count(DISTINCT c.recipe_id))::smallint,least(2,greatest(1,count(DISTINCT c.recipe_id)))::smallint,count(DISTINCT ri.ingredient_id)::smallint,0,least(1,0.2+count(DISTINCT c.recipe_id)*0.15),0.5,0.5,'episode-workload-v1' FROM food.meal_episodes e JOIN food.meal_episode_components c ON c.episode_id=e.id LEFT JOIN food.recipes r ON r.id=c.recipe_id LEFT JOIN food.recipe_ingredients ri ON ri.recipe_id=r.id GROUP BY e.id,e.episode_hash ON CONFLICT DO NOTHING;

INSERT INTO food.episode_cadence(episode_id,region_code,household_type_code,cadence_tier,frequency_prior,richness_dimensions,confidence)
SELECT e.id,'IN','all',CASE WHEN e.richness_prior>=0.75 THEN 'occasional' WHEN e.richness_prior>=0.55 THEN 'weekly_rich' ELSE 'regular_rotation' END,CASE WHEN e.richness_prior>=0.75 THEN 0.2 WHEN e.richness_prior>=0.55 THEN 0.45 ELSE 0.8 END,jsonb_build_object('richness',e.richness_prior,'effort',e.effort_prior),e.confidence FROM food.meal_episodes e ON CONFLICT DO NOTHING;
"""


if __name__ == "__main__":
    OUTPUT.write_text(build_seed(), encoding="utf-8")
