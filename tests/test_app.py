"""External application facade contracts."""

from __future__ import annotations

import json

import pytest

import heavenbase as hb
import glosswise
from heavenbase.workspace import WorkspaceSpec

from conftest import isolated_context, restore_owner_permissions


@pytest.mark.fast
def test_workspace_directory_manages_default_selection_and_mcp_json(
    tmp_path,
    monkeypatch,
) -> None:
    """Managed defaults should hide storage and follow active selection."""
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    root = tmp_path / "directory-context"
    context = isolated_context(root)
    directory = glosswise.GlossWiseWorkspaces(context)
    try:
        scope = f"{context.config.base_scope}.default"
        with context.config.scoped(scope):
            defaults_before = context.config.get("heavenbase.extensions.default")
        with pytest.raises(Exception) as missing_setup:
            directory.ensure_default()
        assert glosswise.is_glosswise_error(missing_setup.value)
        assert missing_setup.value.code == "setup_required"
        assert directory.configure_user_languages(["en", "zh", "ru"]) == [
            "en",
            "zh",
            "ru",
        ]
        default = directory.ensure_default()
        assert default["id"] == "default"
        assert default["active"] is True
        assert default["default_languages"] == ["en", "zh", "ru"]
        with context.config.scoped(scope):
            assert context.config.get("heavenbase.extensions.default") == defaults_before
        assert WorkspaceSpec.load("default", context=context).extension_roots == ("glosswise",)
        assert "database" not in str(default).lower()
        assert glosswise.managed_database_path() == (tmp_path / "home" / ".glosswise" / "default.db")
        assert [item["id"] for item in directory.list()] == ["default"]

        second = directory.create(
            "client",
            database=tmp_path / "custom.db",
        )
        assert second["active"] is True
        assert second["storage"] == "external"
        assert second["default_languages"] == ["en", "zh", "ru"]
        assert directory.configure_default_languages(
            ["en", "ja", "en"],
        )[
            "default_languages"
        ] == ["en", "ja"]
        assert directory.get("client")["default_languages"] == [
            "en",
            "ja",
        ]
        assert "custom.db" not in str(second)
        assert directory.get()["id"] == "client"
        assert directory.activate("default")["active"] is True
        assert directory.deactivate() == {
            "deactivated": "default",
            "effective": "default",
        }
        assert directory.get()["id"] == "default"

        config = directory.mcp_config()
        server = config["mcpServers"]["glosswise"]
        assert server["command"] == "glosswise"
        assert server["args"] == ["mcp"]
        assert directory.mcp_config(profile="read")["mcpServers"]["glosswise"]["args"] == ["mcp", "--profile", "read"]
        assert directory.mcp_config(transport="http") == {
            "mcpServers": {
                "glosswise": {
                    "transport": "http",
                    "url": "http://127.0.0.1:61055/mcp",
                }
            }
        }
        assert directory.mcp_config(
            transport="sse",
            host="localhost",
            port=61056,
        ) == {
            "mcpServers": {
                "glosswise": {
                    "transport": "sse",
                    "url": "http://localhost:61056/sse",
                }
            }
        }
        with pytest.raises(ValueError, match="1 through 65535"):
            directory.mcp_config(port=70000)
        assert (
            directory.mcp_config(
                transport="http",
                host="::1",
            )["mcpServers"][
                "glosswise"
            ]["url"]
            == "http://[::1]:61055/mcp"
        )
        with pytest.raises(ValueError, match="without a URL scheme"):
            directory.mcp_config(transport="http", host="http://localhost")

        health = directory.health()
        assert "database" not in str(health).lower()
        removed = directory.remove("client")
        assert removed == {
            "removed": "client",
            "data_retained": True,
        }

        manifest_path = tmp_path / "default-manifest.json"
        manifest_path.write_text(
            json.dumps(directory.manifest("default")),
            encoding="utf-8",
        )
        assert directory.remove("default")["data_retained"] is True
        imported = directory.import_manifest(manifest_path)
        assert imported["id"] == "default"
        assert imported["active"] is True
    finally:
        context.close()
        restore_owner_permissions(root)


@pytest.mark.fast
def test_app_facade_runs_workspace_crud_and_translation_brief(
    tmp_path,
) -> None:
    """One owning app should cover the normal external integration flow."""
    root = tmp_path / "app-context"
    context = isolated_context(root)
    glosswise.install(context)
    workspace = hb.HeavenBase(
        "app-facade",
        context=context,
        backends={"main": {"type": "sqlite", "database": ":memory:"}},
    )
    workspace.enable_extension("glosswise")
    glosswise.setup_workspace(workspace)
    app = glosswise.GlossWiseApp(context, workspace)
    try:
        assert app.info()["workspace"] == "app-facade"
        assert "glosswise-curator" in app.info()["profiles"]
        assert app.default_languages() == []
        assert app.configure_default_languages(["en", "ja"]) == ["en", "ja"]
        assert app.info()["default_languages"] == ["en", "ja"]
        assert app.info()["user_config"]["translation"]["mode"] == "auto"
        term = app.put_term(
            {
                "object_id": "term-app-query",
                "key": "app-query",
                "definition": "A query owned by an external application.",
                "domains": ["technology"],
                "status": "active",
            },
            [
                {
                    "object_id": "form-app-query-en",
                    "lang": "en",
                    "role": "preferred",
                    "text": "app query",
                },
                {
                    "object_id": "form-app-query-ja",
                    "lang": "ja",
                    "role": "preferred",
                    "text": "アプリクエリ",
                },
            ],
        )
        assert term["key"] == "app-query"
        assert "term_key" not in term
        assert app.term_language_advisory(term)["complete"] is True
        assert app.get_term("term-app-query") == term
        get_term = app.service.get_term
        app.service.get_term = lambda _object_id: (_ for _ in ()).throw(AssertionError("list_terms must batch form hydration"))
        assert [item["object_id"] for item in app.list_terms()] == ["term-app-query"]
        app.service.get_term = get_term
        scan = app.scan_text(
            "Run the app query.",
            text_lang="en",
            target_lang="ja",
            domain="technology",
        )
        assert "term-app-query" in {item["object_id"] for item in scan["items"]}
        search = app.search_terms(
            "app query",
            query_lang="en",
            target_lang="ja",
            domain="technology",
        )
        assert search["items"][0]["object_id"] == "term-app-query"

        rule = app.put_rule(
            {
                "object_id": "rule-app-query",
                "title": "Keep approved query wording",
                "instruction": "Use the approved target term.",
                "trigger_mode": "lexical",
                "triggers": ["app query"],
                "source_langs": ["en"],
                "target_langs": ["ja"],
                "status": "active",
            }
        )
        assert app.get_rule("rule-app-query") == rule
        assert [item["object_id"] for item in app.list_rules()] == ["rule-app-query"]

        brief = app.prepare_translation(
            "Run the app query.",
            source_lang="en",
            target_lang="ja",
            domain="technology",
        )
        assert {"term-app-query", "rule-app-query"} <= {item["object_id"] for item in brief["items"]}

        archived = app.archive("rule-app-query")
        assert archived["status"] == "deprecated"
        assert app.list_rules(status="active") == []
        archived_term = app.archive("term-app-query")
        assert archived_term["key"] == "app-query"
        assert "term_key" not in archived_term
        assert app.list_terms(status="active") == []
    finally:
        app.close()
        restore_owner_permissions(root)
