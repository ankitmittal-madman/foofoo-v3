"""Fail-closed project and identity checks for protected production operations."""

from __future__ import annotations

from urllib.parse import urlparse
from uuid import UUID


def supabase_project_ref(supabase_url: str) -> str:
    """Extract the project reference from a canonical ``https://<ref>.supabase.co`` URL."""
    parsed = urlparse(supabase_url)
    labels = (parsed.hostname or "").split(".")
    if parsed.scheme != "https" or len(labels) < 3 or labels[-2:] != ["supabase", "co"]:
        raise RuntimeError("SUPABASE_URL does not identify a canonical Supabase project")
    project_ref = labels[0]
    if not project_ref or project_ref in {"api", "db", "pooler"}:
        raise RuntimeError("SUPABASE_URL does not contain a usable project reference")
    return project_ref


def database_identifies_project(database_url: str, project_ref: str) -> bool:
    """Return whether a direct or pooler PostgreSQL URL names the expected Supabase project."""
    parsed = urlparse(database_url)
    hostname = parsed.hostname or ""
    username = parsed.username or ""
    direct_match = hostname == f"db.{project_ref}.supabase.co"
    pooler_match = hostname.endswith(".pooler.supabase.com") and username.endswith(
        f".{project_ref}"
    )
    return parsed.scheme in {"postgres", "postgresql"} and (direct_match or pooler_match)


def existing_auth_email(connection, expected_profile_id: UUID, *, lock: bool) -> str:
    """Return the verified existing Auth email for an exact UUID and linked public profile."""
    lock_clause = " for update" if lock else ""
    with connection.cursor() as cursor:
        cursor.execute("set local statement_timeout = '15s'")
        cursor.execute(
            f"""
            select users.email,
                   exists(select 1 from public.profiles where profiles.id = users.id)
              from auth.users as users
             where users.id = %s
             {lock_clause}
            """,
            (str(expected_profile_id),),
        )
        rows = cursor.fetchall()
    if len(rows) != 1:
        raise RuntimeError("Expected profile UUID must resolve to exactly one existing Auth user")
    email, has_profile = rows[0]
    if not isinstance(email, str) or not email.strip() or not has_profile:
        raise RuntimeError(
            "Expected Auth identity must have an email and linked production profile"
        )
    return email.strip()
