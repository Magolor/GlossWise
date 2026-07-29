"""Deterministic project-owned lexical/vector fusion."""

from __future__ import annotations

__all__ = ["reciprocal_rank_fusion"]

from collections.abc import Mapping, Sequence


def reciprocal_rank_fusion(
    lexical: Sequence[Mapping[str, object]],
    semantic: Sequence[Mapping[str, object]],
    *,
    rank_constant: int = 60,
) -> list[dict[str, object]]:
    """Fuse ranked signals while retaining inspectable components.

    Each input row requires `candidate_id`. Semantic rows may carry a
    normalized provider `score`; lexical rows may carry a `priority`.

    Args:
        lexical (Sequence[Mapping[str, object]]): Best-first lexical rows.
        semantic (Sequence[Mapping[str, object]]): Best-first semantic rows.
        rank_constant (int): Positive RRF stability constant.

    Returns:
        list[dict[str, object]]: Best-first fused candidates with component
        ranks, scores, and a deterministic `match_method`.

    Raises:
        ValueError: If the rank constant is not positive or a candidate id is
            blank.
    """
    if int(rank_constant) < 1:
        raise ValueError("rank_constant must be positive")
    candidates: dict[str, dict[str, object]] = {}

    for rank, row in enumerate(lexical, start=1):
        candidate_id = _candidate_id(row)
        candidate = candidates.setdefault(
            candidate_id,
            _empty_candidate(candidate_id),
        )
        candidate["lexical_rank"] = min(
            rank,
            int(candidate["lexical_rank"] or rank),
        )
        candidate["lexical_priority"] = max(
            int(candidate["lexical_priority"]),
            int(row.get("priority", 0)),
        )
        candidate["lexical_score"] = 1.0 / (rank_constant + rank)

    for rank, row in enumerate(semantic, start=1):
        candidate_id = _candidate_id(row)
        candidate = candidates.setdefault(
            candidate_id,
            _empty_candidate(candidate_id),
        )
        score = float(row.get("score", 0.0))
        if candidate["semantic_rank"] is None or rank < int(candidate["semantic_rank"]):
            candidate["semantic_rank"] = rank
        candidate["semantic_score"] = max(
            float(candidate["semantic_score"]),
            score,
        )
        candidate["semantic_rrf"] = max(
            float(candidate["semantic_rrf"]),
            max(0.0, score) / (rank_constant + rank),
        )

    output = []
    for candidate in candidates.values():
        lexical_present = candidate["lexical_rank"] is not None
        semantic_present = candidate["semantic_rank"] is not None
        candidate["match_method"] = "hybrid" if lexical_present and semantic_present else "lexical" if lexical_present else "semantic"
        candidate["score"] = round(
            float(candidate["lexical_score"]) + float(candidate["semantic_rrf"]),
            12,
        )
        candidate["signals"] = {
            "lexical": (
                {
                    "rank": candidate["lexical_rank"],
                    "priority": candidate["lexical_priority"],
                    "rrf": candidate["lexical_score"],
                }
                if lexical_present
                else None
            ),
            "semantic": (
                {
                    "rank": candidate["semantic_rank"],
                    "score": candidate["semantic_score"],
                    "rrf": candidate["semantic_rrf"],
                }
                if semantic_present
                else None
            ),
        }
        output.append(candidate)
    output.sort(
        key=lambda item: (
            -float(item["score"]),
            -float(item["semantic_score"]),
            -int(item["lexical_priority"]),
            str(item["candidate_id"]),
        )
    )
    return output


def _candidate_id(row: Mapping[str, object]) -> str:
    value = str(row.get("candidate_id", "")).strip()
    if not value:
        raise ValueError("candidate_id must not be blank")
    return value


def _empty_candidate(candidate_id: str) -> dict[str, object]:
    return {
        "candidate_id": candidate_id,
        "lexical_rank": None,
        "lexical_priority": 0,
        "lexical_score": 0.0,
        "semantic_rank": None,
        "semantic_score": 0.0,
        "semantic_rrf": 0.0,
    }
