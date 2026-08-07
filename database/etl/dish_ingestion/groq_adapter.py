"""Stage 4: pluggable Groq enrichment adapter for missing-field inference.

Reads GROQ_API_KEY from env. If absent, runs in no-op/mock mode: returns low-confidence
heuristic guesses (or None) and clearly tags every result's source as 'mock' vs 'groq_api' so
downstream provenance columns (dish_taxonomy_assertions.source_type/model_name) are never
misrepresented as a real model call that did not happen.

This module never calls the network itself when GROQ_API_KEY is absent — `_call_groq` is the
single seam where a real HTTP call would go; it is invoked only when a key is configured.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass

GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.1-8b-instant")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"


@dataclass
class EnrichmentSuggestion:
    field_key: str
    value: str | None
    confidence: float
    source: str          # 'mock' | 'groq_api' | 'heuristic'
    model_name: str | None = None
    model_version: str | None = None
    raw_response: dict | None = None


class GroqAdapter:
    """Infers missing tags / regional affinity / class hints for a single dish.

    Only ever invoked for fields the CSV/ontology stage left unresolved (task brief rule 3).
    """

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key if api_key is not None else os.environ.get("GROQ_API_KEY")
        self.mock_mode = not bool(self.api_key)

    def infer_regional_affinity(self, dish_name: str, cuisine_raw: str) -> EnrichmentSuggestion:
        """Best-effort region guess from the cuisine text alone (state cuisines commonly imply a
        region directly, e.g. 'Bengali Recipes' -> 'east', 'Punjabi' -> 'north').
        """
        heuristic_map = {
            "punjabi": "north", "rajasthani": "north", "north indian": "north",
            "bengali": "east", "assamese": "east", "odia": "east",
            "south indian": "south", "andhra": "south", "kerala": "south",
            "tamil nadu": "south", "karnataka": "south", "chettinad": "south",
            "maharashtrian": "west", "gujarati": "west", "goan": "west",
            "hyderabadi": "south", "kashmiri": "north",
        }
        key = cuisine_raw.strip().lower()
        region = heuristic_map.get(key)
        if region:
            return EnrichmentSuggestion(
                field_key="regional_affinity", value=region, confidence=0.55,
                source="heuristic",
                raw_response={"method": "cuisine_keyword_map", "input": cuisine_raw},
            )
        if self.mock_mode:
            return EnrichmentSuggestion(
                field_key="regional_affinity", value=None, confidence=0.0, source="mock",
                raw_response={"note": "GROQ_API_KEY not set; mock mode returns no inference"},
            )
        return self._call_groq_region(dish_name, cuisine_raw)

    def infer_tags(self, dish_name: str, ingredients: list[str]) -> list[EnrichmentSuggestion]:
        """Lightweight ingredient-keyword tag heuristics, used whenever GROQ_API_KEY is absent or
        as a cheap pre-pass before a real model call.
        """
        text = " ".join(ingredients).lower() + " " + dish_name.lower()
        keyword_tags = {
            "spicy": ["chilli", "chili", "pepper"],
            "sweet": ["sugar", "jaggery", "honey"],
            "fried": ["fry", "fried", "deep fry"],
            "one_pot": ["pressure cook", "one pot"],
            "dairy": ["paneer", "curd", "yogurt", "ghee", "milk", "cream"],
        }
        suggestions: list[EnrichmentSuggestion] = []
        for tag, keywords in keyword_tags.items():
            if any(k in text for k in keywords):
                suggestions.append(
                    EnrichmentSuggestion(
                        field_key=f"tag:{tag}", value=tag, confidence=0.5, source="heuristic",
                        raw_response={"method": "keyword_scan", "matched_keywords": keywords},
                    )
                )
        if not suggestions and not self.mock_mode:
            suggestions.extend(self._call_groq_tags(dish_name, ingredients))
        return suggestions

    # -- network seam, only reached when self.mock_mode is False ------------------------------
    def _call_groq(self, prompt: str) -> dict:
        payload = {
            "model": GROQ_MODEL,
            "messages": [
                {"role": "system", "content": "Return concise JSON only, no prose."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.0,
            "max_tokens": 200,
        }
        req = urllib.request.Request(
            GROQ_API_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                # Cloudflare (fronting api.groq.com) blocks Python's default urllib
                # User-Agent ("Python-urllib/3.x") as bot traffic — a real 403 cause
                # confirmed on Groq's own community forum, independent of key validity.
                "User-Agent": "foofoo-dish-ingestion/1.0",
            },
            method="POST",
        )
        # Two calls per new row (region + tags) share this timeout -- a full-dataset run that
        # observed ~40s/row on genuinely new rows (vs the ~8s/row before Groq started actually
        # succeeding) is consistent with calls regularly running to the old 20s ceiling before
        # falling back, likely rate-limit queuing rather than a fast rejection. Cut to 8s so a
        # slow/rate-limited call fails fast onto the heuristic path instead of stalling a row.
        with urllib.request.urlopen(req, timeout=8) as resp:  # pragma: no cover - network
            return json.loads(resp.read().decode("utf-8"))

    def _call_groq_region(self, dish_name: str, cuisine_raw: str) -> EnrichmentSuggestion:
        prompt = (
            f"Indian dish '{dish_name}' (cuisine label: '{cuisine_raw}'). "
            "Which single Indian region is it most associated with: north, south, east, west, "
            "northeast, or pan_indian? Reply with just the region code."
        )
        try:
            raw = self._call_groq(prompt)
            content = raw["choices"][0]["message"]["content"].strip().lower()
            return EnrichmentSuggestion(
                field_key="regional_affinity", value=content, confidence=0.6, source="groq_api",
                model_name=GROQ_MODEL, raw_response=raw,
            )
        except (urllib.error.URLError, KeyError, IndexError, TimeoutError, ValueError) as exc:  # pragma: no cover
            return EnrichmentSuggestion(
                field_key="regional_affinity", value=None, confidence=0.0, source="groq_api_failed",
                model_name=GROQ_MODEL, raw_response={"error": str(exc)},
            )

    def _call_groq_tags(self, dish_name: str, ingredients: list[str]) -> list[EnrichmentSuggestion]:
        prompt = (
            f"Indian dish '{dish_name}' with ingredients: {', '.join(ingredients[:15])}. "
            "List up to 5 short lowercase descriptive tags as a JSON array of strings."
        )
        try:
            raw = self._call_groq(prompt)
            content = raw["choices"][0]["message"]["content"].strip()
            tags = json.loads(content)
            return [
                EnrichmentSuggestion(
                    field_key=f"tag:{t}", value=t, confidence=0.55, source="groq_api",
                    model_name=GROQ_MODEL, raw_response=raw,
                )
                for t in tags if isinstance(t, str)
            ]
        except (urllib.error.URLError, KeyError, IndexError, TimeoutError, ValueError, json.JSONDecodeError):  # pragma: no cover
            return []
