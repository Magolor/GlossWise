"""Graph-edge integrity contracts."""

from __future__ import annotations

import pytest

import heavenbase as hb

from test_entities import active_term, preferred_form


def seed_linkable_terms(workspace: hb.HeavenBase) -> None:
    """Store two active concepts that graph tests can connect."""
    workspace.glosswise.put_term(
        active_term("term-source", "source"),
        [preferred_form("form-source", "Source")],
    )
    workspace.glosswise.put_term(
        active_term("term-target", "target"),
        [preferred_form("form-target", "Target")],
    )


@pytest.mark.fast
def test_graph_write_rejects_missing_target_and_restores_prior_links(
    glosswise_workspace: hb.HeavenBase,
) -> None:
    """A failed relationship replacement must leave the prior graph intact."""
    workspace = glosswise_workspace
    seed_linkable_terms(workspace)
    service = workspace.glosswise
    service.put_term(
        {
            **active_term("term-source", "source"),
            "related_terms": [{"term": "term-target", "relation": "see-also"}],
        },
        [],
    )

    with pytest.raises(Exception) as failure:
        service.put_term(
            {
                **active_term("term-source", "source"),
                "related_terms": [{"term": "term-missing", "relation": "see-also"}],
            },
            [],
        )
    assert failure.value.code == "term_conflict"
    assert failure.value.object_ids == ("term-missing",)

    assert service.get_term("term-source")["related_terms"] == [{"term": "term-target", "relation": "see-also"}]


@pytest.mark.fast
def test_restrictive_graph_edge_blocks_target_deletion(
    glosswise_workspace: hb.HeavenBase,
) -> None:
    """Schema-directed deletion should honor the declared restrict policy."""
    workspace = glosswise_workspace
    seed_linkable_terms(workspace)
    workspace.glosswise.put_term(
        {
            **active_term("term-source", "source"),
            "related_terms": [{"term": "term-target", "relation": "see-also"}],
        },
        [],
    )

    with pytest.raises(hb.GraphDeleteRestrictedError, match="Delete restricted"):
        workspace.delete(
            ("glosswise-term", "term-target"),
            edges="schema",
        )
    assert workspace.get("term-target", entity="glosswise-term") is not None


@pytest.mark.fast
def test_rule_and_example_links_validate_existing_targets(
    glosswise_workspace: hb.HeavenBase,
) -> None:
    """Rules and examples should share HeavenBase graph integrity."""
    workspace = glosswise_workspace
    seed_linkable_terms(workspace)
    rule = workspace.glosswise.put_rule(
        {
            "object_id": "rule-ui",
            "title": "Keep UI labels",
            "instruction": "Use the approved target label.",
            "trigger_mode": "lexical",
            "triggers": ["button"],
            "status": "active",
            "referenced_terms": [
                {"term": "term-target", "relation": "governs"},
            ],
        }
    )
    assert rule["referenced_terms"][0]["term"] == "term-target"

    example = workspace.glosswise.put_example(
        {
            "object_id": "example-ui",
            "source_text": "Click Source.",
            "target_text": "Click Target.",
            "source_lang": "en-us",
            "target_lang": "ja",
            "status": "active",
            "referenced_terms": [
                {"term": "term-target", "relation": "illustrates"},
            ],
            "referenced_rules": [
                {"rule": "rule-ui", "relation": "illustrates"},
            ],
        }
    )
    assert example["source_lang"] == "en-US"
    assert example["target_lang"] == "ja"
