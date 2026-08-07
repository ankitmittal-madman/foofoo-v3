from ops.recommendation.auto_engine_inspector import AUDIT_QUERIES


def test_regions_audit_uses_rehomed_production_table() -> None:
    source_table, query = AUDIT_QUERIES["regions"]

    assert source_table == "public.re_states"
    assert "FROM public.re_states" in query
    assert "re_engine.re_states" not in query
