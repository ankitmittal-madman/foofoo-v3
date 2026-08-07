"""Run a fail-closed, privacy-minimized prospective recommendation/refresh check.

Identity-only mode authenticates the protected test credential and verifies its JWT user UUID.
Recommendation mode additionally requests baseline and refreshed meal-episode slates. It never
submits feedback: an automated check must not manufacture a human preference signal.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from uuid import UUID, uuid4

from ops.recommendation.protected_identity import (
    database_identifies_project,
    existing_auth_email,
    supabase_project_ref,
)

EXECUTE_CONFIRMATION = "EXECUTE_USER_RECOMMENDATION_REFRESH"
SLOTS = ("breakfast", "lunch", "dinner")
OpenUrl = Callable[..., Any]


def safe_http_error_code(error: HTTPError) -> str | None:
    """Extract only a bounded machine code; never echo provider messages or response bodies."""
    try:
        body = json.loads(error.read().decode())
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    if not isinstance(body, Mapping):
        return None
    code = body.get("error_code") or body.get("code")
    if not isinstance(code, str) or not 1 <= len(code) <= 80:
        return None
    return code if all(character.isalnum() or character in "_.-" for character in code) else None


def required_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"Required environment variable is missing: {name}")
    return value


def post_json(
    url: str,
    payload: Mapping[str, Any],
    headers: Mapping[str, str],
    *,
    opener: OpenUrl = urlopen,
) -> dict[str, Any]:
    request = Request(
        url,
        data=json.dumps(payload, separators=(",", ":")).encode(),
        headers={"Content-Type": "application/json", **headers},
        method="POST",
    )
    try:
        with opener(request, timeout=45) as response:
            body = json.loads(response.read().decode())
    except HTTPError as error:
        provider_code = safe_http_error_code(error)
        suffix = f" ({provider_code})" if provider_code else ""
        raise RuntimeError(f"Request failed with HTTP {error.code}{suffix}") from error
    if not isinstance(body, dict):
        raise RuntimeError("Endpoint returned a non-object JSON response")
    return body


def authenticate(
    supabase_url: str,
    anon_key: str,
    email: str,
    password: str,
    expected_profile_id: UUID,
    *,
    opener: OpenUrl = urlopen,
) -> str:
    response = post_json(
        f"{supabase_url.rstrip('/')}/auth/v1/token?grant_type=password",
        {"email": email, "password": password},
        {"apikey": anon_key, "Authorization": f"Bearer {anon_key}"},
        opener=opener,
    )
    user = response.get("user")
    actual_id = user.get("id") if isinstance(user, Mapping) else None
    token = response.get("access_token")
    if actual_id != str(expected_profile_id):
        raise RuntimeError("Protected sign-in credential does not belong to the expected profile")
    if not isinstance(token, str) or not token:
        raise RuntimeError("Authentication response did not include an access token")
    return token


def episode_identities(response: Mapping[str, Any]) -> tuple[str, ...]:
    episodes = response.get("episodes")
    if not isinstance(episodes, list) or not episodes:
        raise RuntimeError("Meal-episode response did not contain any episodes")
    identities: list[str] = []
    for episode in episodes:
        if not isinstance(episode, Mapping):
            raise RuntimeError("Meal-episode response contains a malformed episode")
        identity = episode.get("episode_hash") or episode.get("display_name")
        if not isinstance(identity, str) or not identity.strip():
            raise RuntimeError("Meal episode has no stable identity")
        identities.append(identity.strip())
    if len(set(identities)) != len(identities):
        raise RuntimeError("Meal-episode response contains duplicate identities")
    if not isinstance(response.get("slate_id"), str) or not response["slate_id"]:
        raise RuntimeError("Meal-episode response is missing modern slate lineage")
    return tuple(identities)


def digest_identities(identities: tuple[str, ...]) -> str:
    material = "\n".join(sorted(identities)).encode()
    return f"sha256:{hashlib.sha256(material).hexdigest()[:16]}"


def jaccard(left: tuple[str, ...], right: tuple[str, ...]) -> float:
    a, b = set(left), set(right)
    return len(a & b) / len(a | b) if a or b else 0.0


def run_refresh_cycle(
    supabase_url: str,
    anon_key: str,
    token: str,
    *,
    opener: OpenUrl = urlopen,
) -> dict[str, Any]:
    endpoint = f"{supabase_url.rstrip('/')}/functions/v1/plan"
    headers = {"apikey": anon_key, "Authorization": f"Bearer {token}"}
    raw: dict[str, dict[int, tuple[str, ...]]] = {}
    report: dict[str, Any] = {}
    for slot in SLOTS:
        raw[slot] = {}
        for generation in (0, 1):
            response = post_json(
                endpoint,
                {
                    "surface": "meal_episodes",
                    "slot": slot,
                    "count": 4,
                    "refresh_generation": generation,
                    "exclude_recently_served": True,
                    "request_id": str(uuid4()),
                },
                headers,
                opener=opener,
            )
            try:
                raw[slot][generation] = episode_identities(response)
            except RuntimeError as error:
                raise RuntimeError(
                    f"{slot} refresh generation {generation}: {error}"
                ) from error
        baseline, refreshed = raw[slot][0], raw[slot][1]
        report[slot] = {
            "baseline_count": len(baseline),
            "refreshed_count": len(refreshed),
            "baseline_set": digest_identities(baseline),
            "refreshed_set": digest_identities(refreshed),
            "set_changed": set(baseline) != set(refreshed),
            "first_changed": baseline[0] != refreshed[0],
            "overlap": round(jaccard(baseline, refreshed), 4),
        }
    for slot, result in report.items():
        if not result["set_changed"]:
            raise RuntimeError(f"Refresh did not change the {slot} episode set")
    cross_slot = {
        f"{left}_{right}": round(jaccard(raw[left][1], raw[right][1]), 4)
        for index, left in enumerate(SLOTS)
        for right in SLOTS[index + 1 :]
    }
    return {"slots": report, "refreshed_cross_slot_overlap": cross_slot}


def write_report(path: Path, report: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=path.parent, prefix=f".{path.name}.", delete=False
    ) as handle:
        json.dump(report, handle, indent=2, sort_keys=True)
        handle.write("\n")
        temporary = handle.name
    os.chmod(temporary, 0o600)
    os.replace(temporary, path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expected-profile-id", type=UUID, required=True)
    parser.add_argument("--mode", choices=("identity-only", "recommend-refresh"), required=True)
    parser.add_argument("--confirm-production-write", default="")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)

    supabase_url = required_env("SUPABASE_URL")
    anon_key = required_env("SUPABASE_ANON_KEY")
    database_url = required_env("DATABASE_URL")
    project_ref = supabase_project_ref(supabase_url)
    if not database_identifies_project(database_url, project_ref):
        raise RuntimeError("Database URL does not identify the public Supabase project")
    import psycopg2

    application_name = f"foofoo-prospective-identity-{os.environ.get('GITHUB_RUN_ID', 'local')}"
    with psycopg2.connect(
        database_url,
        application_name=application_name[:63],
        connect_timeout=10,
    ) as connection:
        email = existing_auth_email(connection, args.expected_profile_id, lock=False)
    token = authenticate(
        supabase_url,
        anon_key,
        email,
        required_env("TEST_USER_PASSWORD"),
        args.expected_profile_id,
    )
    report: dict[str, Any] = {
        "identity_verified": True,
        "mode": args.mode,
        "feedback_submitted": False,
    }
    if args.mode == "recommend-refresh":
        if args.confirm_production_write != EXECUTE_CONFIRMATION:
            raise RuntimeError(
                "Recommendation mode requires the exact explicit production-write confirmation"
            )
        report["refresh_cycle"] = run_refresh_cycle(supabase_url, anon_key, token)
    write_report(args.output, report)
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
