"""Rotate and verify the protected prospective-user credential against production Supabase.

The operation updates only the existing Auth user's password after proving the database project,
Auth identity, and linked production profile. It never creates an account or recommendation data.
"""

from __future__ import annotations

import argparse
import json
import os
from collections.abc import Sequence
from urllib.parse import urlparse
from uuid import UUID

from ops.recommendation.prospective_user_cycle import authenticate, required_env

CONFIRMATION = "ROTATE_PROSPECTIVE_CREDENTIAL"


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


def rotate_existing_credential(
    connection,
    email: str,
    password: str,
    expected_profile_id: UUID,
) -> None:
    """Rotate one existing Auth password after locking and validating its production profile.

    @param connection - psycopg connection to the verified production project
    @param email - protected account email supplied only through repository secrets
    @param password - replacement password supplied only through repository secrets
    @param expected_profile_id - exact existing Auth/profile UUID authorized for rotation
    @throws RuntimeError when identity, profile linkage, or update cardinality is unsafe
    """
    if len(password) < 20:
        raise RuntimeError("Replacement credential does not meet the 20-character minimum")
    with connection.cursor() as cursor:
        cursor.execute("set local statement_timeout = '15s'")
        cursor.execute(
            """
            select users.id::text,
                   exists(select 1 from public.profiles where profiles.id = users.id)
              from auth.users as users
             where lower(users.email) = lower(%s)
             for update
            """,
            (email,),
        )
        rows: Sequence[tuple[str, bool]] = cursor.fetchall()
        if len(rows) != 1:
            raise RuntimeError("Protected email must resolve to exactly one existing Auth user")
        actual_id, has_profile = rows[0]
        if actual_id != str(expected_profile_id) or not has_profile:
            raise RuntimeError("Protected Auth identity does not match the linked expected profile")
        cursor.execute(
            """
            update auth.users
               set encrypted_password = crypt(%s, gen_salt('bf')),
                   updated_at = now()
             where id = %s
             returning id::text
            """,
            (password, str(expected_profile_id)),
        )
        updated = cursor.fetchall()
        if updated != [(str(expected_profile_id),)]:
            raise RuntimeError("Credential rotation did not update exactly the expected Auth user")


def main(argv: list[str] | None = None) -> int:
    """Validate scope, rotate the existing credential, and prove live Auth accepts it."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expected-profile-id", type=UUID, required=True)
    parser.add_argument("--confirm", required=True)
    args = parser.parse_args(argv)
    if args.confirm != CONFIRMATION:
        raise RuntimeError("Credential rotation requires the exact explicit confirmation")

    database_url = required_env("DATABASE_URL")
    supabase_url = required_env("SUPABASE_URL")
    anon_key = required_env("SUPABASE_ANON_KEY")
    email = required_env("TEST_USER_EMAIL")
    password = required_env("TEST_USER_PASSWORD")
    project_ref = supabase_project_ref(supabase_url)
    if not database_identifies_project(database_url, project_ref):
        raise RuntimeError("Database URL does not identify the public Supabase project")

    import psycopg2

    application_name = f"foofoo-credential-rotation-{os.environ.get('GITHUB_RUN_ID', 'local')}"
    with psycopg2.connect(
        database_url,
        application_name=application_name[:63],
        connect_timeout=10,
    ) as connection:
        rotate_existing_credential(connection, email, password, args.expected_profile_id)

    authenticate(supabase_url, anon_key, email, password, args.expected_profile_id)
    print(json.dumps({"credential_rotated": True, "identity_verified": True}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
