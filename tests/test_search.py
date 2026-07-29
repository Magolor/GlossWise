"""Semantic retrieval and translation-brief contracts."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import pytest

import heavenbase as hb
from glosswise import HeavenBaseEmbedder, is_glosswise_error

from conftest import SEMANTIC_POLICY
from test_entities import active_term, preferred_form


def fixture_mock_embed(
    *,
    inputs: Sequence[str],
    **_: Any,
) -> dict[str, object]:
    """Return deterministic semantic axes through HeavenBase's mock gateway."""
    vectors = []
    for text in inputs:
        value = str(text).casefold()
        if any(token in value for token in ("redis", "cache")):
            vector = [1.0, 0.0, 0.0]
        elif any(token in value for token in ("legal", "contract")):
            vector = [0.0, 1.0, 0.0]
        elif any(token in value for token in ("click", "button", "interface")):
            vector = [0.0, 0.0, 1.0]
        elif any(token in value for token in ("billing", "invoice")):
            vector = [0.7, 0.7, 0.0]
        else:
            vector = [0.2, 0.2, 0.2]
        vectors.append(vector)
    return {
        "data": [{"index": index, "embedding": vector} for index, vector in enumerate(vectors)],
        "usage": {},
    }


def semantic_embedder(context: hb.Context) -> HeavenBaseEmbedder:
    """Build the context-bound offline fixture adapter."""
    return HeavenBaseEmbedder(
        context,
        embedding_space=str(SEMANTIC_POLICY["embedding_space"]),
        dimension=int(SEMANTIC_POLICY["dimension"]),
        preset="mock",
        gateway="mock",
        cache=False,
        mock_embed=fixture_mock_embed,
    )


def seed_semantic_data(workspace: hb.HeavenBase) -> None:
    """Attach the mock gateway and store semantically distinct fixtures."""
    if workspace.get("term-redis", entity="glosswise-term") is not None:
        return
    service = workspace.glosswise
    adapter = semantic_embedder(workspace.context)
    assert adapter.client.spec.gateway == "mock"
    service.configure_embedder(adapter)
    service.put_term(
        {
            **active_term("term-redis", "redis"),
            "definition": "Redis cache query performance",
            "domains": ["technology"],
            "priority": 9,
        },
        [
            preferred_form("form-redis-en", "Redis Query"),
            preferred_form("form-redis-ja", "Redisクエリ", lang="ja"),
        ],
    )
    service.put_term(
        {
            **active_term("term-cache", "cache"),
            "definition": "Cache invalidation performance",
            "domains": ["technology"],
            "priority": 7,
        },
        [preferred_form("form-cache-en", "cache invalidation")],
    )
    service.put_term(
        {
            **active_term("term-contract", "contract"),
            "definition": "Legal contract language",
            "domains": ["legal"],
            "priority": 8,
        },
        [preferred_form("form-contract-en", "contract")],
    )
    service.put_rule(
        {
            "object_id": "rule-cache",
            "title": "Keep cache terminology",
            "instruction": "Use approved Redis cache terminology.",
            "trigger_mode": "hybrid",
            "triggers": ["Redis Query"],
            "source_langs": ["en"],
            "target_langs": ["ja"],
            "topics": ["technology"],
            "styles": ["plain"],
            "priority": 8,
            "status": "active",
        }
    )
    service.put_rule(
        {
            "object_id": "rule-legal",
            "title": "Legal formality",
            "instruction": "Preserve formal legal contract language.",
            "trigger_mode": "semantic",
            "triggers": [],
            "source_langs": ["en"],
            "target_langs": ["ja"],
            "topics": ["legal"],
            "styles": ["formal"],
            "priority": 9,
            "status": "active",
        }
    )
    service.put_rule(
        {
            "object_id": "rule-always",
            "title": "Preserve structure",
            "instruction": "Preserve the source structure.",
            "trigger_mode": "always",
            "triggers": [],
            "source_langs": ["*"],
            "target_langs": ["*"],
            "topics": ["technology"],
            "styles": ["plain"],
            "priority": 1,
            "status": "active",
        }
    )
    service.put_example(
        {
            "object_id": "example-cache",
            "source_text": "Improve Redis cache performance.",
            "target_text": "Redisキャッシュの性能を改善します。",
            "source_lang": "en",
            "target_lang": "ja",
            "topic": "technology",
            "style": "plain",
            "tags": ["approved"],
            "notes": "Approved cache example.",
            "status": "active",
        }
    )
    service.put_example(
        {
            "object_id": "example-legal",
            "source_text": "The contract remains binding.",
            "target_text": "本契約は引き続き拘束力を有します。",
            "source_lang": "en",
            "target_lang": "ja",
            "topic": "legal",
            "style": "formal",
            "tags": ["approved"],
            "notes": "Approved legal example.",
            "status": "active",
        }
    )


def seed_no_embedder_data(workspace: hb.HeavenBase) -> None:
    """Store lexical fixtures without attaching any live embedder."""
    if workspace.get("term-redis", entity="glosswise-term") is not None:
        return
    service = workspace.glosswise
    service.put_term(
        {
            **active_term("term-redis", "redis"),
            "definition": "Redis cache query performance",
            "domains": ["technology"],
            "priority": 9,
        },
        [preferred_form("form-redis-en", "Redis Query")],
    )
    service.put_rule(
        {
            "object_id": "rule-cache",
            "title": "Keep cache terminology",
            "instruction": "Use approved Redis cache terminology.",
            "trigger_mode": "lexical",
            "triggers": ["Redis Query"],
            "source_langs": ["en"],
            "target_langs": ["ja"],
            "topics": ["technology"],
            "styles": ["plain"],
            "priority": 8,
            "status": "active",
        }
    )


@pytest.mark.fast
def test_term_and_rule_search_disclose_hybrid_signals(
    glosswise_semantic_workspace: hb.HeavenBase,
) -> None:
    """Lexical and vector evidence should fuse without losing components."""
    workspace = glosswise_semantic_workspace
    seed_semantic_data(workspace)

    terms = workspace.glosswise.search_terms(
        "Redis Query cache performance",
        query_lang="en",
        target_lang="ja",
        domain="technology",
        limit=10,
    )
    by_term = {item["object_id"]: item for item in terms["items"]}
    assert by_term["term-redis"]["match_method"] == "hybrid"
    assert by_term["term-redis"]["signals"]["lexical"] is not None
    assert by_term["term-redis"]["signals"]["semantic"] is not None
    assert by_term["term-cache"]["match_method"] == "semantic"
    assert by_term["term-redis"]["target_forms"][0]["lang"] == "ja"
    assert "term-contract" not in by_term

    unscoped = workspace.glosswise.search_terms(
        "Redis performance",
        query_lang="en",
        target_lang="ja",
    )
    assert "term-contract" not in {item["object_id"] for item in unscoped["items"]}

    rules = workspace.glosswise.search_rules(
        "Redis Query cache performance",
        source_lang="en",
        target_lang="ja",
        topic="technology",
        style="plain",
    )
    by_rule = {item["object_id"]: item for item in rules["items"]}
    assert by_rule["rule-cache"]["match_method"] == "hybrid"
    assert by_rule["rule-always"]["match_method"] == "lexical"
    assert "rule-legal" not in by_rule


@pytest.mark.fast
def test_example_filters_and_stale_embedding_space_are_enforced(
    glosswise_semantic_workspace: hb.HeavenBase,
) -> None:
    """Only current-space examples satisfying all filters may rank."""
    workspace = glosswise_semantic_workspace
    seed_semantic_data(workspace)
    Example = workspace.entities["glosswise-example"]
    workspace.upsert(
        Example,
        {
            "object_id": "example-stale",
            "source_text": "Redis cache performance.",
            "target_text": "古い例",
            "source_lang": "en",
            "target_lang": "ja",
            "topic": "technology",
            "style": "plain",
            "tags": ["approved"],
            "notes": "Stale vector.",
            "status": "active",
            "search_text": "Redis cache performance.",
            "embedding": [1.0, 0.0, 0.0],
            "embedding_space": "stale/model/space",
            "referenced_terms": [],
            "referenced_rules": [],
        },
    )

    result = workspace.glosswise.search_examples(
        "Redis cache performance",
        source_lang="en",
        target_lang="ja",
        topic="technology",
        style="plain",
        tag="approved",
    )
    assert [item["object_id"] for item in result["items"]] == ["example-cache"]
    assert result["items"][0]["match_method"] == "semantic"
    assert result["items"][0]["score"] > 0


@pytest.mark.fast
def test_filtered_near_plan_returns_eligible_rows_below_ineligible_neighbors(
    glosswise_semantic_workspace: hb.HeavenBase,
) -> None:
    """Co-located exhaustive top-K should preserve filtered correctness."""
    workspace = glosswise_semantic_workspace
    seed_semantic_data(workspace)
    Example = workspace.entities["glosswise-example"]
    policy = workspace.glosswise.embedding_policy()
    for object_id, topic, vector in (
        ("example-special", "special", [0.8, 0.2, 0.0]),
        ("example-distractor-a", "other", [1.0, 0.0, 0.0]),
        ("example-distractor-b", "other", [0.99, 0.01, 0.0]),
    ):
        workspace.upsert(
            Example,
            {
                "object_id": object_id,
                "source_text": object_id,
                "target_text": object_id,
                "source_lang": "en",
                "target_lang": "ja",
                "topic": topic,
                "style": "plain",
                "tags": [],
                "notes": "",
                "status": "active",
                "search_text": object_id,
                "embedding": vector,
                "embedding_space": policy["embedding_space"],
                "referenced_terms": [],
                "referenced_rules": [],
            },
        )
    candidate_count = len(workspace.query(Example).where(Example.status == "active").where(Example.embedding_space == policy["embedding_space"]).execute().ids)
    query = (
        workspace.query(Example)
        .where(Example.status == "active")
        .where(Example.embedding_space == policy["embedding_space"])
        .where(Example.topic == "special")
        .near(
            Example.embedding,
            [1.0, 0.0, 0.0],
            top_k=candidate_count,
        )
    )
    rows = query.execute().rows()
    plan = query.explain()
    near = [step for step in plan["steps"] if step.get("node") == "near"]
    filters = [step for step in plan["steps"] if step.get("node") == "filter"]
    assert [row["object_id"] for row in rows] == ["example-special"]
    assert len(near) == 1
    assert near[0]["backend"] == "main"
    assert near[0]["strategy"] == hb.VectorIndex.identifier
    assert near[0]["near_filter_mode"] == "combined_scan"
    assert {step["backend"] for step in filters} == {"main"}


@pytest.mark.fast
def test_prepare_translation_builds_complete_bounded_brief(
    glosswise_semantic_workspace: hb.HeavenBase,
) -> None:
    """One call should merge terms, rules, and examples for agent use."""
    workspace = glosswise_semantic_workspace
    seed_semantic_data(workspace)
    brief = workspace.glosswise.prepare_translation(
        "Improve Redis Query cache performance.",
        source_lang="en",
        target_lang="ja",
        domain="technology",
        topic="technology",
        style="plain",
        term_limit=5,
        rule_limit=5,
        example_limit=5,
    )
    kinds = {item["kind"] for item in brief["items"]}
    ids = {item["object_id"] for item in brief["items"]}
    assert kinds == {"term", "rule", "example"}
    assert {"term-redis", "rule-cache", "example-cache"} <= ids
    assert brief["error"] is None
    assert brief["warnings"] == []
    assert brief["next_cursor"] is None
    assert "text" not in brief["request"]


@pytest.mark.fast
def test_prepare_translation_surfaces_equal_priority_target_conflicts(
    glosswise_semantic_workspace: hb.HeavenBase,
) -> None:
    """A brief must expose incompatible preferred forms instead of choosing."""
    workspace = glosswise_semantic_workspace
    seed_semantic_data(workspace)
    service = workspace.glosswise
    service.put_term(
        {
            **active_term("term-redis-conflict", "redis-conflict"),
            "definition": "Alternative Redis policy",
            "domains": ["technology"],
            "priority": 9,
        },
        [
            preferred_form("form-redis-conflict-en", "Redis Query"),
            preferred_form(
                "form-redis-conflict-ja",
                "Redis検索",
                lang="ja",
            ),
        ],
    )

    brief = service.prepare_translation(
        "Redis Query",
        source_lang="en",
        target_lang="ja",
        domain="technology",
        topic="technology",
        style="plain",
    )
    assert len(brief["conflicts"]) == 1
    conflict = brief["conflicts"][0]
    assert conflict["kind"] == "term_target_form"
    assert set(conflict["object_ids"]) == {
        "term-redis",
        "term-redis-conflict",
    }
    assert {form["text"] for form in conflict["target_forms"]} == {
        "Redisクエリ",
        "Redis検索",
    }
    conflicted = [item for item in brief["items"] if item.get("object_id") in conflict["object_ids"] and item.get("raw_span") == conflict["raw_span"]]
    assert len(conflicted) == 2
    assert all(conflict["id"] in item["conflict_ids"] for item in conflicted)


@pytest.mark.fast
def test_no_embedder_mode_keeps_lexical_utility(
    glosswise_no_embedder_workspace: hb.HeavenBase,
) -> None:
    """Missing semantic capability should warn instead of failing."""
    workspace = glosswise_no_embedder_workspace
    seed_no_embedder_data(workspace)
    terms = workspace.glosswise.search_terms(
        "Redis Query",
        query_lang="en",
        domain="technology",
    )
    assert [item["object_id"] for item in terms["items"]] == ["term-redis"]
    assert terms["items"][0]["match_method"] == "lexical"
    assert terms["warnings"]

    partial = workspace.glosswise.search_terms(
        "query",
        query_lang="en",
        domain="technology",
    )
    assert [item["object_id"] for item in partial["items"]] == ["term-redis"]
    assert partial["items"][0]["source_forms"][0]["text"] == "Redis Query"

    examples = workspace.glosswise.search_examples(
        "Redis Query",
        source_lang="en",
        target_lang="ja",
    )
    assert examples["items"] == []
    assert examples["warnings"]

    brief = workspace.glosswise.prepare_translation(
        "Redis Query",
        source_lang="en",
        target_lang="ja",
        domain="technology",
        topic="technology",
        style="plain",
    )
    ids = {item["object_id"] for item in brief["items"]}
    assert {"term-redis", "rule-cache"} <= ids
    assert brief["warnings"]


@pytest.mark.fast
def test_embedder_and_policy_mismatches_fail_before_search(
    glosswise_semantic_workspace: hb.HeavenBase,
) -> None:
    """Live and persisted embedding identity must remain immutable."""
    workspace = glosswise_semantic_workspace
    seed_semantic_data(workspace)

    class WrongDimension:
        embedding_space = SEMANTIC_POLICY["embedding_space"]
        dimension = 2

        @staticmethod
        def embed(inputs: Sequence[str]) -> list[list[float]]:
            return [[1.0, 0.0] for _ in inputs]

    with pytest.raises(Exception) as adapter:
        workspace.glosswise.configure_embedder(WrongDimension())
    assert is_glosswise_error(adapter.value)
    assert adapter.value.code == "embedding_space_mismatch"

    changed = {**SEMANTIC_POLICY, "revision": "fixture-2"}
    with pytest.raises(Exception) as policy:
        workspace.glosswise.configure_embedding(changed)
    assert is_glosswise_error(policy.value)
    assert policy.value.code == "embedding_space_mismatch"

    with pytest.raises(Exception) as target:
        workspace.glosswise.prepare_translation(
            "Redis Query",
            target_lang="auto",
        )
    assert target.value.code == "target_language_required"
