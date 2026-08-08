import pytest

from aux_re_service import auth


def test_signature_verifies_exact_raw_body():
    body = b'{"household_id":"h","meal_slot":"dinner"}'
    timestamp = 1_700_000_000
    header = f"t={timestamp},v1={auth.signature('secret', timestamp, body)}"
    auth.verify(body, header, "secret", timestamp + 10)

    with pytest.raises(auth.AuthError, match="invalid_signature"):
        auth.verify(body + b" ", header, "secret", timestamp + 10)


@pytest.mark.parametrize(
    ("header", "now", "reason"),
    [
        (None, 1_700_000_000, "missing_signature"),
        ("v1=abc", 1_700_000_000, "malformed_signature"),
        ("t=1,v1=abc", 1_700_000_000, "stale_signature"),
    ],
)
def test_signature_failures_are_safe_tokens(header, now, reason):
    with pytest.raises(auth.AuthError, match=reason):
        auth.verify(b"{}", header, "secret", now)
