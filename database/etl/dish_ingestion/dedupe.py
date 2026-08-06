"""Stage 2: canonical lookup and dedupe.

Given a normalized SourceRow and a preloaded index of existing dishes (by exact name, exact
fingerprint, and a lowered-name index for fuzzy matching), decides whether the row:
  - matches an existing canonical dish exactly (fingerprint or exact name) -> 'matched_existing'
  - is a likely near-duplicate of an existing/already-seen-this-run dish -> 'merged_duplicate'
    (recorded as an alias against the earlier dish, not a new dish row)
  - is new -> 'created_new'

Near-duplicate detection uses a conservative difflib ratio threshold on the normalized name only
(never on ingredients/instructions, which vary too much between true near-duplicates and
unrelated dishes to be a safe signal on their own). Anything in the ambiguous band is routed to
review rather than auto-merged — task brief rule 4 spirit (never guess silently on uncertain
identity), applied here to identity as well as classification.
"""

from __future__ import annotations

import difflib
from dataclasses import dataclass

EXACT_THRESHOLD = 1.0
FUZZY_MERGE_THRESHOLD = 0.93   # only auto-merge near-certain typo-level duplicates
FUZZY_REVIEW_THRESHOLD = 0.80  # below this, don't even flag as ambiguous


@dataclass
class DedupeDecision:
    outcome: str                 # 'matched_existing' | 'merged_duplicate' | 'created_new' | 'ambiguous_review'
    target_key: str | None       # normalized name of the matched/merged-into dish, if any
    match_method: str
    score: float


def _block_key(normalized_name: str) -> str:
    """Blocking key for fuzzy dedupe: first alphanumeric token, first 4 chars.

    A full O(n^2) fuzzy scan across all ~16,500 dish names is computationally infeasible in a
    single ETL run (verified: it does not complete in a reasonable time — see runbook
    "Validated vs unexecuted" section). Standard record-linkage practice is to "block" candidates
    into small buckets by a cheap key before running the expensive pairwise comparison only
    within a bucket. Two dish names with materially different starts (e.g. "Masala Karela" vs
    "Karela Masala") will not block together and so cannot fuzzy-merge — an accepted, documented
    trade-off; exact-name and fingerprint matching (both O(1) hash lookups) still catch reordered
    or identical names regardless of blocking.
    """
    token = normalized_name.split(" ", 1)[0] if normalized_name else ""
    return token[:4]


class DedupeIndex:
    """In-memory index built once per run from existing dishes + rows already processed this run."""

    def __init__(self):
        self._by_fingerprint: dict[str, str] = {}   # fingerprint -> canonical key (normalized name)
        self._by_exact_name: dict[str, str] = {}    # lowered name -> canonical key
        self._blocks: dict[str, list[str]] = {}      # block key -> list of candidate lowered names

    def seed_existing(self, existing_dishes: list[dict]) -> None:
        """existing_dishes: [{'name': str, 'fingerprint': str | None}] from public.dishes /
        public.dish_source_rows already in the DB (empty list on a from-scratch DB)."""
        for d in existing_dishes:
            key = d["name"].strip().lower()
            self._by_exact_name[key] = key
            if d.get("fingerprint"):
                self._by_fingerprint[d["fingerprint"]] = key
            self._blocks.setdefault(_block_key(key), []).append(key)

    def decide(self, name: str, fingerprint: str) -> DedupeDecision:
        key = name.strip().lower()

        if fingerprint in self._by_fingerprint:
            return DedupeDecision("matched_existing", self._by_fingerprint[fingerprint], "fingerprint", 1.0)

        if key in self._by_exact_name:
            return DedupeDecision("matched_existing", self._by_exact_name[key], "exact_name", 1.0)

        best_key, best_score = None, 0.0
        for candidate in self._blocks.get(_block_key(key), []):
            score = difflib.SequenceMatcher(None, key, candidate).ratio()
            if score > best_score:
                best_key, best_score = candidate, score

        if best_key and best_score >= FUZZY_MERGE_THRESHOLD:
            self._register_new(key, fingerprint)
            return DedupeDecision("merged_duplicate", best_key, "fuzzy_name", round(best_score, 3))

        if best_key and best_score >= FUZZY_REVIEW_THRESHOLD:
            self._register_new(key, fingerprint)
            return DedupeDecision("ambiguous_review", best_key, "fuzzy_name", round(best_score, 3))

        self._register_new(key, fingerprint)
        return DedupeDecision("created_new", None, "no_match", 0.0)

    def _register_new(self, key: str, fingerprint: str) -> None:
        """Register a row as seen this run so later rows in the same file can dedupe against it
        too (within-file duplicates, not just against pre-existing DB rows)."""
        self._by_exact_name.setdefault(key, key)
        self._by_fingerprint.setdefault(fingerprint, key)
        block = self._blocks.setdefault(_block_key(key), [])
        if key not in block:
            block.append(key)
