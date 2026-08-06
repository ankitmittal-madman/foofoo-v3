from __future__ import annotations

import json
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any, Protocol


class JsonTransport(Protocol):
    def __call__(self, url: str, headers: dict[str, str]) -> dict[str, Any]: ...


def fetch_json(url: str, headers: dict[str, str]) -> dict[str, Any]:
    request = urllib.request.Request(url, headers={"User-Agent": "FoofooOntology/1.0", **headers})
    with urllib.request.urlopen(request, timeout=15) as response:  # noqa: S310 - allowlisted URLs
        if response.status != 200:
            raise RuntimeError(f"provider_http_{response.status}")
        return json.loads(response.read(2_000_000))


@dataclass(frozen=True)
class ProviderFact:
    field_path: str
    value: Any
    confidence: float
    source_code: str
    source_record_id: str | None
    source_url: str
    extraction_method: str
    safety_critical: bool = False


class FoodOnProvider:
    endpoint = "https://www.ebi.ac.uk/ols4/api/search"

    def __init__(self, transport: JsonTransport = fetch_json):
        self.transport = transport

    def lookup(self, name: str) -> list[ProviderFact]:
        query = urllib.parse.urlencode({"q": name, "ontology": "foodon", "rows": 5})
        url = f"{self.endpoint}?{query}"
        payload = self.transport(url, {})
        docs = payload.get("response", {}).get("docs", [])
        if not docs:
            return []
        top = docs[0]
        label = str(top.get("label") or "")
        exact = label.casefold().strip() == name.casefold().strip()
        iri = str(top.get("iri") or top.get("obo_id") or "")
        facts = [
            ProviderFact(
                "external_ids/foodon",
                iri,
                0.9 if exact else 0.72,
                "foodon_ols4",
                iri or None,
                url,
                "ols4_search_exact" if exact else "ols4_search_top_match",
            )
        ]
        aliases = sorted(
            {str(value).strip() for value in top.get("synonym", []) if str(value).strip()}
        )
        if aliases:
            facts.append(
                ProviderFact(
                    "source_aliases/foodon",
                    aliases,
                    0.88 if exact else 0.7,
                    "foodon_ols4",
                    iri or None,
                    url,
                    "ols4_synonyms",
                )
            )
        return facts


class WikidataProvider:
    endpoint = "https://www.wikidata.org/w/api.php"

    def __init__(self, transport: JsonTransport = fetch_json):
        self.transport = transport

    def lookup(self, name: str) -> list[ProviderFact]:
        query = {
            "action": "wbsearchentities",
            "search": name,
            "language": "en",
            "uselang": "en",
            "type": "item",
            "limit": 5,
            "format": "json",
            "origin": "*",
        }
        url = f"{self.endpoint}?{urllib.parse.urlencode(query)}"
        rows = self.transport(url, {}).get("search", [])
        if not rows:
            return []
        top = rows[0]
        label = str(top.get("label") or "")
        exact = label.casefold().strip() == name.casefold().strip()
        entity_id = str(top.get("id") or "")
        facts = [
            ProviderFact(
                "external_ids/wikidata",
                entity_id,
                0.9 if exact else 0.7,
                "wikidata",
                entity_id or None,
                str(top.get("concepturi") or url),
                "wbsearchentities_exact" if exact else "wbsearchentities_top_match",
            )
        ]
        description = str(top.get("description") or "").strip()
        if description:
            facts.append(
                ProviderFact(
                    "source_descriptions/wikidata",
                    description,
                    0.82 if exact else 0.65,
                    "wikidata",
                    entity_id or None,
                    str(top.get("concepturi") or url),
                    "wbsearchentities_description",
                )
            )
        return facts


class UsdaProvider:
    endpoint = "https://api.nal.usda.gov/fdc/v1/foods/search"
    nutrient_codes = {
        "Energy": "nutrition/energy_kcal_per_100g",
        "Protein": "nutrition/protein_g_per_100g",
        "Total lipid (fat)": "nutrition/fat_g_per_100g",
        "Carbohydrate, by difference": "nutrition/carbohydrate_g_per_100g",
    }

    def __init__(self, api_key: str, transport: JsonTransport = fetch_json):
        self.api_key = api_key
        self.transport = transport

    def lookup(self, name: str) -> list[ProviderFact]:
        query = urllib.parse.urlencode({"api_key": self.api_key, "query": name, "pageSize": 5})
        url = f"{self.endpoint}?{query}"
        foods = self.transport(url, {}).get("foods", [])
        if not foods:
            return []
        top = foods[0]
        description = str(top.get("description") or "")
        # Nutrition must never transfer from a merely similar result.
        if description.casefold().strip() != name.casefold().strip():
            return []
        record_id = str(top.get("fdcId") or "")
        facts: list[ProviderFact] = []
        for nutrient in top.get("foodNutrients", []):
            path = self.nutrient_codes.get(str(nutrient.get("nutrientName")))
            value = nutrient.get("value")
            if path and isinstance(value, int | float):
                facts.append(
                    ProviderFact(
                        path,
                        {
                            "value": value,
                            "unit": str(nutrient.get("unitName") or ""),
                            "basis": "100g",
                        },
                        0.9,
                        "usda_fdc",
                        record_id or None,
                        f"https://fdc.nal.usda.gov/fdc-app.html#/food-details/{record_id}",
                        "fdc_exact_description_match",
                    )
                )
        return facts
