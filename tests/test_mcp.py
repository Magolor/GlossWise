"""Safe MCP family, profile, curation, error, and concurrency contracts."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest
import yaml

import heavenbase as hb
import glosswise
from glosswise.contracts import MAX_TEXT_CHARS
from glosswise.mcp import (
    GENERIC_FULL_TOOL_NAMES,
    GENERIC_LOCAL_TOOL_NAMES,
    GENERIC_READ_TOOL_NAMES,
    GLOSSWISE_TOOL_NAMES,
    generic_tool_functions,
    generic_toolkit,
)

from conftest import isolated_context, restore_owner_permissions
from test_entities import active_term, preferred_form

TEXT_TOOLS = {
    "glosswise_workspace_info",
    "glosswise_prepare_translation",
    "glosswise_search_terms",
    "glosswise_search_rules",
    "glosswise_scan_text",
    "glosswise_search_examples",
}
CURATOR_TOOLS = {
    "glosswise_list_records",
    "glosswise_get_record",
    "glosswise_put_term",
    "glosswise_put_rule",
    "glosswise_put_example",
    "glosswise_archive",
}
SKILL_TOOLS = {"list_skills", "read_skill"}
LOCAL_DOCUMENT_TOOLS = {
    "glosswise_scan_file",
    "glosswise_prepare_file",
    "glosswise_ocr_pdf",
    "glosswise_list_documents",
    "glosswise_get_document",
    "glosswise_read_document",
    "glosswise_remove_document",
}


@pytest.mark.fast
def test_generic_full_mcp_selects_and_manages_workspaces(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """One default Toolkit should span every registered GlossWise workspace."""
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    context = isolated_context(tmp_path / "generic-context")
    directory = glosswise.GlossWiseWorkspaces(context)
    try:
        directory.configure_user_languages(["en"])
        directory.create("alpha", activate=True)
        directory.create("beta", activate=False)
        toolkit = generic_toolkit(directory)
        assert tuple(toolkit.tools) == GENERIC_FULL_TOOL_NAMES
        assert len(GENERIC_FULL_TOOL_NAMES) == 22
        assert len(GENERIC_LOCAL_TOOL_NAMES) == 29
        assert tuple(generic_tool_functions(directory, profile="read")) == (GENERIC_READ_TOOL_NAMES)
        assert tuple(generic_tool_functions(directory, profile="local")) == (GENERIC_LOCAL_TOOL_NAMES)
        assert "glosswise_set_workspace_languages" not in GENERIC_READ_TOOL_NAMES

        term = {
            "object_id": "term-generic",
            "key": "generic",
            "definition": "Stored in the explicitly selected workspace.",
            "status": "active",
        }
        forms = [
            {
                "object_id": "form-generic-en",
                "lang": "en",
                "role": "preferred",
                "text": "generic",
            }
        ]
        languages = asyncio.run(
            toolkit.arun(
                "glosswise_set_workspace_languages",
                languages_json='["en","zh","ru"]',
                workspace_id="beta",
            )
        )
        assert languages["items"][0]["default_languages"] == [
            "en",
            "zh",
            "ru",
        ]
        invalid_languages = asyncio.run(
            toolkit.arun(
                "glosswise_set_workspace_languages",
                languages_json='["*"]',
                workspace_id="beta",
            )
        )
        assert invalid_languages["error"]["code"] == "invalid_language_tag"
        assert directory.get("beta")["default_languages"] == [
            "en",
            "zh",
            "ru",
        ]
        stored = asyncio.run(
            toolkit.arun(
                "glosswise_put_term",
                term_json=json.dumps(term),
                forms_json=json.dumps(forms),
                workspace_id="beta",
            )
        )
        assert stored["error"] is None
        assert stored["warnings"] == [
            "Term is missing active preferred forms for workspace default languages: zh, ru. Defaults are advisory; the term was stored."
        ]
        beta = asyncio.run(
            toolkit.arun(
                "glosswise_list_records",
                kind="term",
                workspace_id="beta",
            )
        )
        alpha = asyncio.run(
            toolkit.arun(
                "glosswise_list_records",
                kind="term",
                workspace_id="alpha",
            )
        )
        assert [item["object_id"] for item in beta["items"]] == ["term-generic"]
        assert alpha["items"] == []
        alpha_workspace = asyncio.run(
            toolkit.arun(
                "glosswise_get_workspace",
                workspace_id="alpha",
            )
        )
        assert alpha_workspace["items"][0]["default_languages"] == ["en"]

        activated = asyncio.run(
            toolkit.arun(
                "glosswise_activate_workspace",
                workspace_id="beta",
            )
        )
        assert activated["items"][0]["active"] is True
        selected = asyncio.run(toolkit.arun("glosswise_workspace_info"))
        assert selected["items"][0]["workspace"] == "beta"

        workspaces = asyncio.run(toolkit.arun("glosswise_list_workspaces"))
        assert [item["id"] for item in workspaces["items"]] == [
            "alpha",
            "beta",
        ]
        missing = asyncio.run(
            toolkit.arun(
                "glosswise_get_record",
                kind="term",
                object_id="term-generic",
                workspace_id="missing",
            )
        )
        assert missing["error"]["code"] == "workspace_not_found"
    finally:
        context.close()
        restore_owner_permissions(tmp_path)


def seed_mcp_data(workspace: hb.HeavenBase) -> None:
    """Store multilingual lexical data for MCP tests."""
    if workspace.get("term-query", entity="glosswise-term") is not None:
        return
    workspace.glosswise.put_term(
        {
            **active_term("term-query", "query"),
            "definition": "A database query.",
            "domains": ["technology"],
            "priority": 8,
        },
        [
            preferred_form("form-query-en", "query"),
            preferred_form("form-query-ja", "クエリ", lang="ja"),
        ],
    )


@pytest.mark.fast
def test_declared_family_and_profiles_have_exact_safe_inventories(
    glosswise_mcp_workspace: hb.HeavenBase,
) -> None:
    """Manifest, factory, and profiles must agree without generic mutation."""
    workspace = glosswise_mcp_workspace
    manifest = yaml.safe_load((Path(__file__).resolve().parents[1] / "src" / "glosswise" / "meta.yaml").read_text(encoding="utf-8"))
    family = next(item for item in manifest["items"] if item["kind"] == "toolkit_family" and item["identifier"] == "glosswise")
    declared = family["meta"]["definition"]["tool_names"]
    all_declared = [name for item in manifest["items"] if item["kind"] == "toolkit_family" for name in item["meta"]["definition"]["tool_names"]]
    assert tuple(declared) == GLOSSWISE_TOOL_NAMES
    assert len(declared) == len(set(declared))
    assert len(all_declared) == len(set(all_declared))
    assert all(name.startswith("glosswise_") for name in declared)

    normal = workspace.glosswise.to_mcp(profile="glosswise")
    local = workspace.glosswise.to_mcp(profile="glosswise-local")
    curator = workspace.glosswise.to_mcp(profile="glosswise-curator")
    assert set(normal.tools) == TEXT_TOOLS | SKILL_TOOLS
    assert set(local.tools) == TEXT_TOOLS | SKILL_TOOLS | LOCAL_DOCUMENT_TOOLS
    assert set(curator.tools) == TEXT_TOOLS | SKILL_TOOLS | CURATOR_TOOLS
    assert not {
        "query",
        "get",
        "set",
        "upsert",
        "delete",
        "define_entity",
    }.intersection(curator.tools)
    assert getattr(normal, "_mcp_logging_attached", False) is False
    with pytest.raises(ValueError):
        workspace.glosswise.to_mcp(profile="full")


@pytest.mark.fast
def test_curator_profile_runs_domain_crud_and_brief(
    glosswise_mcp_workspace: hb.HeavenBase,
) -> None:
    """An agent should curate, inspect, use, update, and archive records."""
    toolkit = glosswise_mcp_workspace.glosswise.to_mcp(profile="glosswise-curator")
    term = {
        "object_id": "term-agent-query",
        "key": "agent-query",
        "definition": "A query curated through MCP.",
        "domains": ["technology"],
        "status": "active",
    }
    forms = [
        {
            "object_id": "form-agent-query-en",
            "lang": "en",
            "role": "preferred",
            "text": "agent query",
        },
        {
            "object_id": "form-agent-query-ja",
            "lang": "ja",
            "role": "preferred",
            "text": "エージェントクエリ",
        },
    ]
    stored = json.loads(
        asyncio.run(
            toolkit.arun_to_str(
                "glosswise_put_term",
                term_json=json.dumps(term),
                forms_json=json.dumps(forms),
            )
        )
    )
    assert stored["error"] is None
    assert stored["items"][0]["key"] == "agent-query"
    assert "term_key" not in stored["items"][0]

    listed = json.loads(
        asyncio.run(
            toolkit.arun_to_str(
                "glosswise_list_records",
                kind="term",
                status="active",
            )
        )
    )
    assert [item["object_id"] for item in listed["items"]] == ["term-agent-query"]

    fetched = json.loads(
        asyncio.run(
            toolkit.arun_to_str(
                "glosswise_get_record",
                kind="term",
                object_id="term-agent-query",
            )
        )
    )
    assert fetched["items"][0]["forms"][1]["lang"] == "ja"

    brief = json.loads(
        asyncio.run(
            toolkit.arun_to_str(
                "glosswise_prepare_translation",
                text="Run the agent query.",
                source_lang="en",
                target_lang="ja",
                domain="technology",
            )
        )
    )
    assert "term-agent-query" in {item["object_id"] for item in brief["items"]}

    term["definition"] = "An updated query curated through MCP."
    updated = json.loads(
        asyncio.run(
            toolkit.arun_to_str(
                "glosswise_put_term",
                term_json=json.dumps(term),
            )
        )
    )
    assert "updated" in updated["items"][0]["definition"]

    archived = json.loads(
        asyncio.run(
            toolkit.arun_to_str(
                "glosswise_archive",
                object_id="term-agent-query",
            )
        )
    )
    assert archived["items"][0]["status"] == "deprecated"
    assert archived["items"][0]["key"] == "agent-query"
    assert "term_key" not in archived["items"][0]

    invalid = json.loads(
        asyncio.run(
            toolkit.arun_to_str(
                "glosswise_put_rule",
                rule_json="{",
            )
        )
    )
    assert invalid["error"]["code"] == "invalid_json"

    wrong_kind = json.loads(
        asyncio.run(
            toolkit.arun_to_str(
                "glosswise_get_record",
                kind="database",
                object_id="term-agent-query",
            )
        )
    )
    assert wrong_kind["error"]["code"] == "invalid_record_kind"


@pytest.mark.fast
def test_mcp_returns_serialized_versioned_results_without_logging_source(
    glosswise_mcp_workspace: hb.HeavenBase,
) -> None:
    """The default profile should return JSON text without opening a log."""
    workspace = glosswise_mcp_workspace
    seed_mcp_data(workspace)
    toolkit = workspace.glosswise.to_mcp(profile="glosswise")
    source = "Run this query."
    raw = asyncio.run(
        toolkit.arun_to_str(
            "glosswise_prepare_translation",
            text=source,
            source_lang="en",
            target_lang="ja",
            domain="technology",
        )
    )
    result = json.loads(raw)
    assert result["schema_version"] == "1"
    assert result["error"] is None
    assert result["items"]
    assert source not in json.dumps(result["request"], ensure_ascii=False)
    skills = json.loads(asyncio.run(toolkit.arun_to_str("list_skills")))
    assert "glosswise" in {item["name"] for item in skills["skills"]}
    skill = json.loads(
        asyncio.run(
            toolkit.arun_to_str(
                "read_skill",
                skill_name="glosswise",
            )
        )
    )
    assert "Agent translation workflow" in skill["text"]
    assert "glosswise_put_term" in skill["text"]
    assert getattr(toolkit, "_mcp_logging_attached", False) is False
    Message = workspace.entities["agent-message"]
    assert workspace.query(Message).execute().rows() == []


@pytest.mark.fast
def test_mcp_errors_are_stable_and_redacted(
    glosswise_mcp_workspace: hb.HeavenBase,
    tmp_path: Path,
) -> None:
    """Domain and unexpected failures must remain ordinary safe envelopes."""
    workspace = glosswise_mcp_workspace
    toolkit = workspace.glosswise.to_mcp(profile="glosswise-local")
    secret = "client-secret-source"

    missing_target = json.loads(
        asyncio.run(
            toolkit.arun_to_str(
                "glosswise_prepare_translation",
                text=secret,
                target_lang="",
            )
        )
    )
    assert missing_target["error"]["code"] == "target_language_required"
    assert secret not in json.dumps(missing_target, ensure_ascii=False)

    invalid_cursor = json.loads(
        asyncio.run(
            toolkit.arun_to_str(
                "glosswise_scan_text",
                text=secret,
                cursor="not-a-cursor",
            )
        )
    )
    assert invalid_cursor["error"]["code"] == "invalid_cursor"

    invalid_language = json.loads(
        asyncio.run(
            toolkit.arun_to_str(
                "glosswise_scan_text",
                text=secret,
                text_lang="jp",
            )
        )
    )
    assert invalid_language["error"]["code"] == "invalid_language_tag"

    oversized = json.loads(
        asyncio.run(
            toolkit.arun_to_str(
                "glosswise_scan_text",
                text="x" * (MAX_TEXT_CHARS + 1),
            )
        )
    )
    assert oversized["error"]["code"] == "input_too_large"

    denied = json.loads(
        asyncio.run(
            toolkit.arun_to_str(
                "glosswise_scan_file",
                path="/private/client-secret-source.txt",
            )
        )
    )
    assert denied["error"]["code"] == "file_access_denied"
    assert "/private/client-secret-source.txt" not in json.dumps(denied)

    files = tmp_path / "authorized"
    files.mkdir()
    invalid_utf8 = files / "invalid.txt"
    invalid_utf8.write_bytes(b"\xff")
    workspace.glosswise.configure_file_access([files])
    decode = json.loads(
        asyncio.run(
            toolkit.arun_to_str(
                "glosswise_scan_file",
                path=str(invalid_utf8),
            )
        )
    )
    assert decode["error"]["code"] == "decode_failed"

    class FailingEmbedder:
        embedding_space = "none/3/glosswise-v1"
        dimension = 3

        @staticmethod
        def embed(inputs: list[str]) -> list[list[float]]:
            raise RuntimeError("provider detail")

    workspace.glosswise.configure_embedder(FailingEmbedder())
    unavailable = json.loads(
        asyncio.run(
            toolkit.arun_to_str(
                "glosswise_search_terms",
                query="query",
            )
        )
    )
    assert unavailable["error"]["code"] == "embedding_unavailable"

    blank = json.loads(
        asyncio.run(
            toolkit.arun_to_str(
                "glosswise_search_terms",
                query="",
            )
        )
    )
    assert blank["error"]["code"] == "term_conflict"

    def huge_search(*args: object, **kwargs: object) -> dict[str, object]:
        return {
            "schema_version": "1",
            "request": {},
            "detected_language": {},
            "items": [{"payload": "x" * 600_000}],
            "conflicts": [],
            "warnings": [],
            "error": None,
            "truncated": False,
            "next_cursor": None,
        }

    workspace.glosswise.search_terms = huge_search
    too_large = json.loads(
        asyncio.run(
            toolkit.arun_to_str(
                "glosswise_search_terms",
                query="query",
            )
        )
    )
    assert too_large["error"]["code"] == "input_too_large"

    def fail_search(*args: object, **kwargs: object) -> dict[str, object]:
        raise RuntimeError("do not expose provider-secret")

    workspace.glosswise.search_terms = fail_search
    internal = json.loads(
        asyncio.run(
            toolkit.arun_to_str(
                "glosswise_search_terms",
                query=secret,
            )
        )
    )
    assert internal["error"]["code"] == "internal_error"
    serialized = json.dumps(internal)
    assert "provider-secret" not in serialized
    assert secret not in serialized


@pytest.mark.fast
def test_concurrent_calls_keep_language_request_local(
    glosswise_mcp_workspace: hb.HeavenBase,
) -> None:
    """Concurrent clients must not mutate an ambient language preference."""
    workspace = glosswise_mcp_workspace
    seed_mcp_data(workspace)
    toolkit = workspace.glosswise.to_mcp(profile="glosswise")

    async def run_both() -> tuple[dict[str, object], dict[str, object]]:
        english, japanese = await asyncio.gather(
            toolkit.arun(
                "glosswise_scan_text",
                text="query",
                text_lang="en",
                target_lang="ja",
            ),
            toolkit.arun(
                "glosswise_scan_text",
                text="クエリ",
                text_lang="ja",
                target_lang="en",
            ),
        )
        return english, japanese

    english, japanese = asyncio.run(run_both())
    assert english["request"]["text_lang"] == "en"
    assert japanese["request"]["text_lang"] == "ja"
    assert english["items"][0]["matched_text"] == "query"
    assert japanese["items"][0]["matched_text"] == "クエリ"
