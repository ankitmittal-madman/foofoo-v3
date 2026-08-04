from ops.quality.runner.offline_ranking_evaluation import evaluate


def test_offline_metrics_are_exact_and_segmented():
    result = evaluate(
        [
            {
                "request_id": "a",
                "segment": "cold",
                "ranked_ids": ["a", "b"],
                "relevant_ids": ["a"],
                "scores": [1, 0],
            },
            {
                "request_id": "b",
                "segment": "warm",
                "ranked_ids": ["c", "b"],
                "relevant_ids": ["b"],
                "scores": [0, 1],
            },
        ],
        k=2,
    )
    assert result["requests"] == 2
    assert result["recall_at_k"] == 1.0
    assert result["brier_score"] == 0.0
    assert set(result["segments"]) == {"cold", "warm"}


def test_offline_evaluation_rejects_empty_sets():
    try:
        evaluate([])
    except ValueError as error:
        assert "empty" in str(error)
    else:
        raise AssertionError("empty evaluation set should fail")
