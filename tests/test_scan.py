"""SparseGram text and authorized-file scanning contracts."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

import heavenbase as hb
from glosswise import is_glosswise_error
from glosswise.contracts import MAX_TEXT_CHARS

from test_entities import active_term, preferred_form


def seed_multilingual_scan_data(workspace: hb.HeavenBase) -> None:
    """Store representative multilingual terms and scoped rules."""
    if workspace.get("term-api", entity="glosswise-term") is not None:
        return
    service = workspace.glosswise
    payloads = [
        (
            {**active_term("term-api", "api"), "domains": ["technology"], "priority": 8},
            [
                {
                    **preferred_form("form-api-en", "API"),
                    "role": "alias",
                },
                preferred_form("form-api-ja", "API", lang="ja"),
            ],
        ),
        (
            {**active_term("term-database", "database"), "domains": ["technology"], "priority": 7},
            [preferred_form("form-database-ru", "база данных", lang="ru")],
        ),
        (
            {**active_term("term-terminology", "terminology"), "domains": ["technology"], "priority": 6},
            [
                preferred_form("form-terminology-zh", "术语", lang="zh-CN"),
                preferred_form("form-terminology-ja", "用語", lang="ja"),
            ],
        ),
        (
            {**active_term("term-query", "query"), "domains": ["technology"], "priority": 4},
            [preferred_form("form-query-en", "query")],
        ),
        (
            {**active_term("term-query-engine", "query-engine"), "domains": ["technology"], "priority": 5},
            [preferred_form("form-query-engine-en", "query engine")],
        ),
        (
            {**active_term("term-redis", "redis"), "domains": ["technology"], "priority": 9},
            [preferred_form("form-redis-en", "Redis-Query")],
        ),
        (
            {**active_term("term-street", "street"), "domains": ["general"], "priority": 3},
            [preferred_form("form-street-de", "Straße", lang="de")],
        ),
        (
            {**active_term("term-literal", "literal"), "domains": ["general"], "priority": 2},
            [preferred_form("form-literal-en", "Literal")],
        ),
    ]
    for term, forms in payloads:
        service.put_term(term, forms)
    service.put_rule(
        {
            "object_id": "rule-click",
            "title": "Use approved click wording",
            "instruction": "Use the approved target action verb.",
            "trigger_mode": "lexical",
            "triggers": ["Click"],
            "source_langs": ["en"],
            "target_langs": ["*"],
            "topics": ["ui"],
            "styles": ["plain"],
            "priority": 10,
            "status": "active",
        }
    )
    service.put_rule(
        {
            "object_id": "rule-always",
            "title": "Be concise",
            "instruction": "Keep the translation concise.",
            "trigger_mode": "always",
            "source_langs": ["*"],
            "target_langs": ["*"],
            "topics": ["ui"],
            "styles": ["plain"],
            "priority": 1,
            "status": "active",
        }
    )
    service.put_rule(
        {
            "object_id": "rule-other-topic",
            "title": "Legal-only rule",
            "instruction": "Use formal legal language.",
            "trigger_mode": "lexical",
            "triggers": ["Click"],
            "source_langs": ["en"],
            "target_langs": ["*"],
            "topics": ["legal"],
            "styles": ["formal"],
            "priority": 20,
            "status": "active",
        }
    )


@pytest.mark.fast
def test_multilingual_repeats_and_overlaps_preserve_raw_spans(
    glosswise_sql_workspace: hb.HeavenBase,
) -> None:
    """Latin, Cyrillic, Han, and Japanese hits should retain every occurrence."""
    workspace = glosswise_sql_workspace
    seed_multilingual_scan_data(workspace)
    text = "API и база данных; 术语・用語. API. query engine"
    result = workspace.glosswise.scan_text(
        text,
        text_lang="auto",
        target_lang="ja",
        include_rules=False,
        domain="technology",
    )

    ids = [item["object_id"] for item in result["items"]]
    assert ids.count("term-api") == 2
    assert {
        "term-database",
        "term-terminology",
        "term-query",
        "term-query-engine",
    } <= set(ids)
    api_spans = [item["raw_span"] for item in result["items"] if item["object_id"] == "term-api"]
    assert api_spans == [
        [text.find("API"), text.find("API") + 3],
        [text.rfind("API"), text.rfind("API") + 3],
    ]
    overlap = {item["object_id"]: item["raw_span"] for item in result["items"] if item["object_id"] in {"term-query", "term-query-engine"}}
    assert overlap["term-query"][0] == overlap["term-query-engine"][0]
    assert result["truncated"] is False
    assert result["next_cursor"] is None
    assert result["warnings"]
    assert "text_sha256" in result["request"]
    assert "text" not in result["request"]


@pytest.mark.fast
def test_precision_scope_and_always_rule_contract(
    glosswise_sql_workspace: hb.HeavenBase,
) -> None:
    """Literal, casefolded, normalized, scoped, and always evidence is explicit."""
    workspace = glosswise_sql_workspace
    seed_multilingual_scan_data(workspace)
    text = "CLICK STRASSE, redis query, and Literal."
    result = workspace.glosswise.scan_text(
        text,
        text_lang="en",
        target_lang="ja",
        topic="ui",
        style="plain",
    )
    by_id = {}
    for item in result["items"]:
        by_id.setdefault(item["object_id"], []).append(item)

    assert by_id["rule-click"][0]["match_precision"] == "casefolded"
    assert by_id["rule-click"][0]["raw_span"] == [0, 5]
    assert by_id["rule-always"][0]["match_method"] == "always"
    assert by_id["rule-always"][0]["raw_span"] is None
    assert "rule-other-topic" not in by_id
    assert by_id["term-redis"][0]["match_precision"] == "normalized"
    assert by_id["term-literal"][0]["match_precision"] == "literal"
    assert "term-street" not in by_id
    assert result["warnings"] == []
    assert result["detected_language"] == {
        "tag": "en",
        "confidence": 1.0,
        "method": "caller",
    }


@pytest.mark.fast
def test_scan_pagination_is_deterministic_and_request_bound(
    glosswise_sql_workspace: hb.HeavenBase,
) -> None:
    """Cursors should page every occurrence and reject changed input."""
    workspace = glosswise_sql_workspace
    seed_multilingual_scan_data(workspace)
    text = "API API API"
    first = workspace.glosswise.scan_text(
        text,
        text_lang="en",
        include_rules=False,
        limit=1,
    )
    second = workspace.glosswise.scan_text(
        text,
        text_lang="en",
        include_rules=False,
        limit=1,
        cursor=first["next_cursor"],
    )
    third = workspace.glosswise.scan_text(
        text,
        text_lang="en",
        include_rules=False,
        limit=1,
        cursor=second["next_cursor"],
    )
    assert [first["items"][0]["raw_span"], second["items"][0]["raw_span"], third["items"][0]["raw_span"]] == [
        [0, 3],
        [4, 7],
        [8, 11],
    ]
    assert first["truncated"] is True
    assert second["truncated"] is True
    assert third["truncated"] is False

    with pytest.raises(Exception) as stale:
        workspace.glosswise.scan_text(
            "API changed",
            text_lang="en",
            include_rules=False,
            limit=1,
            cursor=first["next_cursor"],
        )
    assert is_glosswise_error(stale.value)
    assert stale.value.code == "invalid_cursor"
    with pytest.raises(Exception) as malformed:
        workspace.glosswise.scan_text(
            text,
            text_lang="en",
            include_rules=False,
            limit=1,
            cursor="W10",
        )
    assert malformed.value.code == "invalid_cursor"


@pytest.mark.fast
def test_sparse_strategy_and_filters_resolve_native_on_sql(
    glosswise_sql_workspace: hb.HeavenBase,
) -> None:
    """Trigger normalizers and co-located scalar/scope filters must stay native."""
    workspace = glosswise_sql_workspace
    seed_multilingual_scan_data(workspace)
    TermForm = workspace.entities["glosswise-term-form"]
    Rule = workspace.entities["glosswise-rule"]

    for entity, trigger in ((TermForm, "triggers"), (Rule, "triggers")):
        binding = workspace.storage_plans[entity.schema().entity_id].first(trigger)
        assert binding.strategy == hb.SparseGramIndex.identifier
        assert binding.strategy_options["normalizer"] == "default"
    for entity, fields in (
        (TermForm, ("domains",)),
        (Rule, ("source_langs", "target_langs", "topics", "styles", "tags")),
    ):
        for field in fields:
            binding = workspace.storage_plans[entity.schema().entity_id].first(field)
            assert binding.strategy == hb.SideTable.identifier

    term_query = (
        workspace.query(TermForm)
        .where(TermForm.triggers.contained_in("API"))
        .where(TermForm.lang == "en")
        .where(TermForm.status == "active")
        .where(TermForm.domains.array_contains("technology"))
    )
    rule_query = (
        workspace.query(Rule)
        .where(Rule.triggers.contained_in("Click"))
        .where(Rule.status == "active")
        .where(Rule.source_langs.array_contains("en"))
        .where(Rule.topics.array_contains("ui"))
    )
    for query in (term_query, rule_query):
        steps = [step for step in query.explain()["steps"] if step.get("node") == "filter"]
        assert steps
        assert {step["backend"] for step in steps} == {"main"}
        assert {step["type"] for step in steps} == {"sqlite"}
        sparse = [step for step in steps if step.get("strategy_adapter") == "sql_sparse_gram"]
        assert len(sparse) == 1
        assert sparse[0]["handler_mode"] == "native"
        for field in ("lang", "status"):
            matching = [step for step in steps if step["field"] == field]
            if matching:
                assert matching[0]["handler_mode"] == "native"
        assert query.execute().rows()


@pytest.mark.fast
def test_scan_file_enforces_roots_types_decoding_and_size(
    glosswise_sql_workspace: hb.HeavenBase,
    tmp_path: Path,
) -> None:
    """Local scanning must fail closed around filesystem authority."""
    workspace = glosswise_sql_workspace
    seed_multilingual_scan_data(workspace)
    allowed = tmp_path / "allowed"
    allowed.mkdir()
    source = allowed / "source.txt"
    source.write_text("API", encoding="utf-8")
    service = workspace.glosswise
    service.configure_file_access(
        [allowed],
        max_bytes=10,
        encodings=["utf-8"],
    )

    result = service.scan_file(
        source,
        text_lang="en",
        include_rules=False,
    )
    assert [item["object_id"] for item in result["items"]] == ["term-api"]
    assert result["request"]["file"]["name"] == "source.txt"
    assert str(allowed) not in str(result)

    outside = tmp_path / "outside.txt"
    outside.write_text("API", encoding="utf-8")
    escaped = allowed / "escaped.txt"
    escaped.symlink_to(outside)
    escaped_parent = allowed / "escaped-parent"
    escaped_parent.symlink_to(tmp_path, target_is_directory=True)
    undecodable = allowed / "binary.txt"
    undecodable.write_bytes(b"\xff\xfe")
    oversized = allowed / "large.txt"
    oversized.write_text("API API API", encoding="utf-8")
    ranged = allowed / "ranged.txt"
    ranged.write_text(
        "ignored ignored\nAPI\ntrailing trailing\n",
        encoding="utf-8",
    )
    directory = allowed / "directory"
    directory.mkdir()

    denied = [
        allowed / "directory" / ".." / "source.txt",
        outside,
        escaped,
        escaped_parent / "outside.txt",
        directory,
    ]
    if hasattr(os, "mkfifo"):
        fifo = allowed / "pipe"
        os.mkfifo(fifo)
        denied.append(fifo)
    for candidate in denied:
        with pytest.raises(Exception) as failure:
            service.scan_file(candidate, text_lang="en", include_rules=False)
        assert is_glosswise_error(failure.value)
        assert failure.value.code == "file_access_denied"

    with pytest.raises(Exception) as decode:
        service.scan_file(
            undecodable,
            text_lang="en",
            include_rules=False,
        )
    assert decode.value.code == "decode_failed"
    with pytest.raises(Exception) as encoding:
        service.scan_file(
            source,
            encoding="latin-1",
            text_lang="en",
            include_rules=False,
        )
    assert encoding.value.code == "decode_failed"
    with pytest.raises(Exception) as size:
        service.scan_file(
            oversized,
            text_lang="en",
            include_rules=False,
        )
    assert size.value.code == "input_too_large"

    ranged_scan = service.scan_file(
        ranged,
        text_lang="en",
        include_rules=False,
        start_line=2,
        end_line=2,
    )
    assert [item["object_id"] for item in ranged_scan["items"]] == ["term-api"]
    assert ranged_scan["request"]["file"]["source_bytes"] > 10
    assert ranged_scan["request"]["file"]["selection"] == {
        "start_line": 2,
        "end_line": 2,
        "has_more": True,
        "chars": 4,
        "bytes": 4,
    }
    brief = service.prepare_file(
        ranged,
        target_lang="ja",
        source_lang="en",
        start_line=2,
        end_line=2,
    )
    assert "term-api" in {item["object_id"] for item in brief["items"]}
    assert brief["request"]["file"]["selection"]["start_line"] == 2

    with pytest.raises(Exception) as invalid_range:
        service.scan_file(
            ranged,
            start_line=4,
            end_line=4,
        )
    assert invalid_range.value.code == "invalid_line_range"


@pytest.mark.fast
def test_scan_text_rejects_unbounded_input(
    glosswise_sql_workspace: hb.HeavenBase,
) -> None:
    """The transient source-text boundary must be explicit and stable."""
    with pytest.raises(Exception) as failure:
        glosswise_sql_workspace.glosswise.scan_text(
            "x" * (MAX_TEXT_CHARS + 1),
            include_rules=False,
        )
    assert is_glosswise_error(failure.value)
    assert failure.value.code == "input_too_large"
