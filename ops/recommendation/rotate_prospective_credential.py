"""Rotate and verify the protected prospective-user credential against production Supabase.

The operation updates only the existing Auth user's password after proving the database project,
Auth identity, and linked production profile. It never creates an account or recommendation data.
"""

from __future__ import annotations

import argparse
import json
import os
from uuid import UUID

from ops.recommendation.prospective_user_cycle import authenticate, required_env
from ops.recommendation.protected_identity import (
    database_identifies_project,
    existing_auth_email,
    supabase_project_ref,
)

CONFIRMATION = "ROTATE_PROSPECTIVE_CREDENTIAL"


def rotate_existing_credential(
    connection,
    password: str,
    expected_profile_id: UUID,
) -> str:
    """Rotate one existing Auth password after locking and validating its production profile.

    @param connection - psycopg connection to the verified production project
    @param password - replacement password supplied only through repository secrets
    @param expected_profile_id - exact existing Auth/profile UUID authorized for rotation
    @throws RuntimeError when identity, profile linkage, or update cardinality is unsafe
    """
    if len(password) < 20:
        raise RuntimeError("Replacement credential does not meet the 20-character minimum")
    email = existing_auth_email(connection, expected_profile_id, lock=True)
    with connection.cursor() as cursor:
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
    return email


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
        email = rotate_existing_credential(connection, password, args.expected_profile_id)

    authenticate(supabase_url, anon_key, email, password, args.expected_profile_id)
    print(json.dumps({"credential_rotated": True, "identity_verified": True}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
