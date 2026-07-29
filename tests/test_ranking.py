"""Deterministic fusion contracts."""

from __future__ import annotations

import pytest

from glosswise.ranking import reciprocal_rank_fusion


@pytest.mark.fast
def test_fusion_discloses_lexical_semantic_and_hybrid_signals() -> None:
    """Every fused result should retain both component explanations."""
    result = reciprocal_rank_fusion(
        [
            {"candidate_id": "hybrid", "priority": 8},
            {"candidate_id": "lexical", "priority": 3},
        ],
        [
            {"candidate_id": "hybrid", "score": 0.8},
            {"candidate_id": "semantic", "score": 0.7},
        ],
    )
    by_id = {item["candidate_id"]: item for item in result}
    assert by_id["hybrid"]["match_method"] == "hybrid"
    assert by_id["lexical"]["match_method"] == "lexical"
    assert by_id["semantic"]["match_method"] == "semantic"
    assert by_id["hybrid"]["signals"]["lexical"]["rank"] == 1
    assert by_id["hybrid"]["signals"]["semantic"]["rank"] == 1
    assert by_id["semantic"]["signals"]["lexical"] is None


@pytest.mark.fast
def test_fusion_ties_are_stable_by_semantic_priority_then_id() -> None:
    """Equivalent aggregate scores must have deterministic tie breakers."""
    lexical = reciprocal_rank_fusion(
        [
            {"candidate_id": "low", "priority": 1},
            {"candidate_id": "high", "priority": 9},
        ],
        [],
        rank_constant=10**12,
    )
    assert [item["candidate_id"] for item in lexical] == ["high", "low"]

    semantic = reciprocal_rank_fusion(
        [],
        [
            {"candidate_id": "b", "score": 0.5},
            {"candidate_id": "a", "score": 0.5},
        ],
        rank_constant=10**12,
    )
    assert [item["candidate_id"] for item in semantic] == ["a", "b"]

    exact_id_tie = reciprocal_rank_fusion(
        [{"candidate_id": "b"}, {"candidate_id": "a"}],
        [{"candidate_id": "a", "score": 1.0}, {"candidate_id": "b", "score": 1.0}],
        rank_constant=10**12,
    )
    assert [item["candidate_id"] for item in exact_id_tie] == ["a", "b"]


@pytest.mark.fast
def test_fusion_rejects_invalid_contract_values() -> None:
    """Malformed ranking inputs should fail before retrieval hydration."""
    with pytest.raises(ValueError, match="positive"):
        reciprocal_rank_fusion([], [], rank_constant=0)
    with pytest.raises(ValueError, match="candidate_id"):
        reciprocal_rank_fusion([{"candidate_id": ""}], [])
