"""Database access layer: connection, batched transactions, and upsert helpers.

Uses psycopg2 (add to your environment: `pip install psycopg2-binary`). Reads the connection
string from DATABASE_URL or SUPABASE_DB_URL, matching this repo's existing convention
(ops/quality/runner/orchestrator.py Phase 7).

Every write function here is written to be safe to call twice with the same input (upsert on a
natural/stable key, or explicit ON CONFLICT DO NOTHING for append-only evidence tables) — see the
runbook's "Idempotency" section for the exact key used per table.
"""

from __future__ import annotations

import json
import logging
import os
from contextlib import contextmanager
from typing import Any, Iterator

logger = logging.getLogger("dish_ingestion.db")


def get_connection_string() -> str:
    conn = os.environ.get("DATABASE_URL") or os.environ.get("SUPABASE_DB_URL")
    if not conn:
        raise RuntimeError(
            "DATABASE_URL / SUPABASE_DB_URL not set. This ETL will not fabricate a connection — "
            "set one of these env vars to a reachable Postgres (e.g. `supabase start` locally) "
            "before running with --apply. --dry-run does not require a database connection at all."
        )
    return conn


class Database:
    """Thin wrapper around a psycopg2 connection with helper methods used by pipeline.py.

    Import of psycopg2 is deferred to __init__ so `--dry-run` mode (and unit tests of the
    normalize/dedupe/adapter modules) never require the dependency to be installed at all.
    """

    def __init__(self, dsn: str | None = None):
        import psycopg2  # deferred import, see docstring
        import psycopg2.extras

        self._psycopg2 = psycopg2
        self._extras = psycopg2.extras
        self.conn = psycopg2.connect(dsn or get_connection_string())
        self.conn.autocommit = False

    def close(self) -> None:
        self.conn.close()

    @contextmanager
    def transaction(self) -> Iterator[Any]:
        """One transaction boundary per batch. Rolls back the whole batch on any exception so a
        partially-applied batch never lands in the DB — resumability then relies on re-running
        the same batch of rows, which is safe because every write below is upsert/ON CONFLICT.
        """
        cur = self.conn.cursor(cursor_factory=self._extras.RealDictCursor)
        try:
            yield cur
            self.conn.commit()
        except Exception:
            self.conn.rollback()
            raise
        finally:
            cur.close()

    # -- reference data loads (read-only, used to build in-memory indexes/adapters) -----------
    def load_cuisines(self, cur) -> dict[str, str]:
        cur.execute("SELECT id, name FROM public.cuisines")
        return {row["name"].strip().lower(): str(row["id"]) for row in cur.fetchall()}

    def load_meal_classes(self, cur) -> list[dict]:
        cur.execute("SELECT class_code, slot, display_name FROM public.meal_classes WHERE is_active")
        return [dict(row) for row in cur.fetchall()]

    def load_existing_dishes(self, cur) -> list[dict]:
        """Existing dishes plus their most recent import fingerprint, if any (for idempotent
        reruns to recognize a dish this ETL created previously)."""
        cur.execute(
            """
            SELECT d.name, d.id,
                   (SELECT dsr.row_fingerprint FROM public.dish_source_rows dsr
                      JOIN public.import_row_results r ON r.source_row_id = dsr.id
                     WHERE r.dish_id = d.id ORDER BY dsr.created_at DESC LIMIT 1) AS fingerprint
            FROM public.dishes d
            """
        )
        return [dict(row) for row in cur.fetchall()]

    # -- import_runs ----------------------------------------------------------------------------
    def start_import_run(self, cur, source_name: str, source_checksum: str, run_mode: str) -> str:
        cur.execute(
            """
            INSERT INTO public.import_runs (source_name, source_checksum, run_mode, status)
            VALUES (%s, %s, %s, 'running') RETURNING id
            """,
            (source_name, source_checksum, run_mode),
        )
        return str(cur.fetchone()["id"])

    def complete_import_run(self, cur, run_id: str, counters: dict, summary_report: dict) -> None:
        cur.execute(
            """
            UPDATE public.import_runs
               SET status = 'completed', completed_at = now(), total_rows = %(total_rows)s,
                   rows_matched_existing = %(matched)s, rows_created_dish = %(created)s,
                   rows_routed_review = %(review)s, rows_errored = %(errored)s,
                   summary_report = %(summary)s
             WHERE id = %(run_id)s
            """,
            {
                "run_id": run_id,
                "total_rows": counters.get("total_rows", 0),
                "matched": counters.get("matched_existing", 0),
                "created": counters.get("created_new", 0),
                "review": counters.get("routed_review", 0),
                "errored": counters.get("errored", 0),
                "summary": json.dumps(summary_report),
            },
        )

    def fail_import_run(self, cur, run_id: str, summary_report: dict) -> None:
        cur.execute(
            "UPDATE public.import_runs SET status = 'failed', completed_at = now(), summary_report = %s WHERE id = %s",
            (json.dumps(summary_report), run_id),
        )

    # -- per-row persistence --------------------------------------------------------------------
    def insert_source_row(self, cur, run_id: str, srno: int, fingerprint: str, raw: dict, normalized: dict) -> str:
        cur.execute(
            """
            INSERT INTO public.dish_source_rows (import_run_id, source_srno, row_fingerprint, raw_payload, normalized_payload)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (import_run_id, source_srno) DO UPDATE SET row_fingerprint = EXCLUDED.row_fingerprint
            RETURNING id
            """,
            (run_id, srno, fingerprint, json.dumps(raw), json.dumps(normalized)),
        )
        return str(cur.fetchone()["id"])

    def upsert_dish(self, cur, name: str, description: str, meal_occasion: list[str],
                     cook_time_minutes: int, cuisine_id: str | None) -> str:
        """Natural key: dishes.name (already UNIQUE per migration 008). Safe to call twice."""
        cur.execute(
            """
            INSERT INTO public.dishes (name, description, meal_occasion, cook_time_minutes, difficulty, cuisine_id, is_active)
            VALUES (%s, %s, %s, %s, 'beginner', %s, true)
            ON CONFLICT (name) DO UPDATE SET description = COALESCE(public.dishes.description, EXCLUDED.description)
            RETURNING id
            """,
            (name, description, meal_occasion, cook_time_minutes, cuisine_id),
        )
        return str(cur.fetchone()["id"])

    def get_dish_id_by_name(self, cur, name: str) -> str | None:
        cur.execute("SELECT id FROM public.dishes WHERE name = %s", (name,))
        row = cur.fetchone()
        return str(row["id"]) if row else None

    def upsert_ingredient(self, cur, name: str, is_veg: bool) -> str:
        cur.execute(
            """
            INSERT INTO public.ingredients (name, is_veg) VALUES (%s, %s)
            ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name
            RETURNING id
            """,
            (name, is_veg),
        )
        return str(cur.fetchone()["id"])

    def link_dish_ingredient(self, cur, dish_id: str, ingredient_id: str) -> None:
        cur.execute(
            """
            INSERT INTO public.dish_ingredients (dish_id, ingredient_id) VALUES (%s, %s)
            ON CONFLICT (dish_id, ingredient_id) DO NOTHING
            """,
            (dish_id, ingredient_id),
        )

    def insert_alias(self, cur, dish_id: str, alias_text: str, alias_source: str, run_id: str, confidence: float | None) -> None:
        cur.execute(
            """
            INSERT INTO public.dish_aliases (dish_id, alias_text, alias_source, import_run_id, confidence)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (dish_id, alias_text) DO NOTHING
            """,
            (dish_id, alias_text, alias_source, run_id, confidence),
        )

    def insert_regional_affinity(self, cur, dish_id: str, region_code: str, score: float, confidence: float,
                                  source_name: str, source_type: str, model_name: str | None = None) -> None:
        # dish_regional_affinities_ml_model_name (migration 065) requires model_name whenever
        # source_type='ml_model' -- the caller must pass the real model that produced the value.
        cur.execute(
            """
            INSERT INTO public.dish_regional_affinities
              (dish_id, region_code, affinity_score, confidence, source_name, source_type, model_name)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (dish_id, region_code) DO UPDATE
              SET affinity_score = EXCLUDED.affinity_score, confidence = EXCLUDED.confidence,
                  source_name = EXCLUDED.source_name, model_name = EXCLUDED.model_name, updated_at = now()
              WHERE public.dish_regional_affinities.review_status <> 'accepted'
            """,
            (dish_id, region_code, score, confidence, source_name, source_type, model_name),
        )

    def insert_meal_class_mapping(self, cur, dish_id: str, class_code: str, slot: str, confidence: float, source_name: str, method: str, source_type: str) -> None:
        cur.execute(
            """
            INSERT INTO public.dish_meal_class_mappings
              (dish_id, class_code, slot, item_role, confidence, source_name, classification_method, source_type)
            VALUES (%s, %s, %s, 'primary', %s, %s, %s, %s)
            ON CONFLICT (dish_id, class_code, slot) DO UPDATE
              SET confidence = EXCLUDED.confidence, updated_at = now()
              WHERE public.dish_meal_class_mappings.review_status <> 'accepted'
            """,
            (dish_id, class_code, slot, confidence, source_name, method, source_type),
        )

    def insert_food_source_record(self, cur, dish_id: str, provider: str, query_text: str, payload: dict, checksum: str) -> str:
        cur.execute(
            """
            INSERT INTO public.food_source_records (provider, dish_id, query_text, source_payload, payload_sha256)
            VALUES (%s, %s, %s, %s, %s) RETURNING id
            """,
            (provider, dish_id, query_text, json.dumps(payload), checksum),
        )
        return str(cur.fetchone()["id"])

    def insert_taxonomy_assertion(self, cur, dish_id: str, field_key: str, value_text: str | None,
                                   confidence: float, source_name: str, source_type: str,
                                   source_record_id: str | None, model_name: str | None) -> str:
        cur.execute(
            """
            INSERT INTO public.dish_taxonomy_assertions
              (dish_id, field_key, value_text, confidence, source_name, source_type, source_record_id, model_name)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
            """,
            (dish_id, field_key, value_text, confidence, source_name, source_type, source_record_id, model_name),
        )
        return str(cur.fetchone()["id"])

    def insert_image_asset(self, cur, source_url: str | None, checksum: str | None, fetch_status: str,
                            storage_path: str | None = None, content_type: str | None = None,
                            prompt_text: str | None = None, prompt_backend: str | None = None,
                            prompt_model_name: str | None = None, image_gen_backend: str | None = None,
                            image_gen_seed: int | None = None) -> str:
        """Idempotent on checksum_sha256 when known (migration 076 UNIQUE constraint) — a re-run
        that regenerates a byte-identical PNG (unlikely with a random seed, but defensively
        handled) updates in place rather than duplicating. Rows with no checksum (e.g. a failed
        generation attempt) always get a fresh row, matching the pre-existing behavior."""
        if checksum:
            cur.execute(
                """
                INSERT INTO public.image_assets
                  (source_url, checksum_sha256, fetch_status, storage_path, content_type,
                   prompt_text, prompt_backend, prompt_model_name, image_gen_backend, image_gen_seed)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (checksum_sha256) DO UPDATE SET fetch_status = EXCLUDED.fetch_status,
                  storage_path = EXCLUDED.storage_path
                RETURNING id
                """,
                (source_url, checksum, fetch_status, storage_path, content_type,
                 prompt_text, prompt_backend, prompt_model_name, image_gen_backend, image_gen_seed),
            )
        else:
            cur.execute(
                """
                INSERT INTO public.image_assets
                  (source_url, fetch_status, storage_path, content_type,
                   prompt_text, prompt_backend, prompt_model_name, image_gen_backend, image_gen_seed)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
                """,
                (source_url, fetch_status, storage_path, content_type,
                 prompt_text, prompt_backend, prompt_model_name, image_gen_backend, image_gen_seed),
            )
        return str(cur.fetchone()["id"])

    def load_dish_ids_with_image(self, cur) -> set[str]:
        """Every dish_id that already has at least one dish_images row — the idempotency guard
        for Stage 5: a dish in this set is never regenerated/re-uploaded on rerun (task brief
        rule 3)."""
        cur.execute("SELECT DISTINCT dish_id FROM public.dish_images")
        return {str(row["dish_id"]) for row in cur.fetchall()}

    def link_dish_image(self, cur, dish_id: str, image_asset_id: str, alt_text: str | None, is_primary: bool, source_type: str, confidence: float | None) -> None:
        cur.execute(
            """
            INSERT INTO public.dish_images (dish_id, image_asset_id, alt_text, is_primary, source_type, confidence)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (dish_id, image_asset_id) DO NOTHING
            """,
            (dish_id, image_asset_id, alt_text, is_primary, source_type, confidence),
        )

    def insert_row_result(self, cur, source_row_id: str, dish_id: str | None, status: str,
                           match_method: str | None, match_score: float | None,
                           ontology_confidence: float | None, meal_class_code: str | None) -> None:
        cur.execute(
            """
            INSERT INTO public.import_row_results
              (source_row_id, dish_id, status, match_method, match_score, ontology_confidence, meal_class_code)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (source_row_id) DO UPDATE
              SET dish_id = EXCLUDED.dish_id, status = EXCLUDED.status, match_method = EXCLUDED.match_method,
                  match_score = EXCLUDED.match_score, ontology_confidence = EXCLUDED.ontology_confidence,
                  meal_class_code = EXCLUDED.meal_class_code, processed_at = now()
            """,
            (source_row_id, dish_id, status, match_method, match_score, ontology_confidence, meal_class_code),
        )

    def insert_row_error(self, cur, source_row_id: str, stage: str, error_code: str, error_detail: str) -> None:
        cur.execute(
            "INSERT INTO public.import_row_errors (source_row_id, stage, error_code, error_detail) VALUES (%s, %s, %s, %s)",
            (source_row_id, stage, error_code, error_detail),
        )

    def insert_review_queue_entry(self, cur, source_row_id: str, dish_id: str | None, reason_code: str, detail: dict) -> None:
        cur.execute(
            """
            INSERT INTO public.dish_ingestion_review_queue (source_row_id, dish_id, reason_code, detail)
            VALUES (%s, %s, %s, %s)
            """,
            (source_row_id, dish_id, reason_code, json.dumps(detail)),
        )
