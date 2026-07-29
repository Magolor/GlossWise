"""Installed Skill, CLI, curator MCP, and agent workflow proof."""

from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import time

import pytest

from conftest import restore_owner_permissions

PROJECT_ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.full
def test_installed_skill_drives_cli_and_curator_mcp_workflow(
    tmp_path: Path,
    release_artifacts: tuple[Path, Path],
) -> None:
    """An installed agent should create, curate, brief, scan, and archive."""
    Client = pytest.importorskip("fastmcp").Client
    StdioTransport = pytest.importorskip("fastmcp.client.transports").StdioTransport
    uv = shutil.which("uv")
    if uv is None:
        pytest.fail("uv is required for the installed agent gate")

    _, wheel = release_artifacts
    isolated = ["run", "--isolated", "--with", str(wheel)]
    environment = {
        **os.environ,
        "HOME": str(tmp_path / "home"),
        "UV_NO_PROGRESS": "1",
    }

    def cli(*args: str) -> dict[str, object]:
        completed = subprocess.run(
            [uv, *isolated, "glosswise", *args],
            check=True,
            capture_output=True,
            text=True,
            cwd=tmp_path,
            env=environment,
        )
        return json.loads(completed.stdout)

    setup = cli(
        "setup",
        "-l",
        "en",
        "-l",
        "ja",
        "-l",
        "ru",
    )
    packaged_skill = PROJECT_ROOT / "src" / "glosswise" / "skills" / "glosswise" / "SKILL.md"
    installed_paths = [Path(str(path)) for path in setup["skills"]]
    assert installed_paths == [
        Path(environment["HOME"]) / ".agents" / "skills" / "glosswise" / "SKILL.md",
        Path(environment["HOME"]) / ".claude" / "skills" / "glosswise" / "SKILL.md",
    ]
    assert all(path.read_bytes() == packaged_skill.read_bytes() for path in installed_paths)
    workspace_id = "default"
    assert setup["workspace"]["id"] == workspace_id
    assert setup["workspace"]["active"] is True
    assert "database" not in json.dumps(setup).lower()
    assert (Path(environment["HOME"]) / ".glosswise" / "default.db").is_file()

    config = cli("mcp", "--json")
    assert config["mcpServers"]["glosswise"]["args"] == ["mcp"]

    term_payload = {
        "term": {
            "object_id": "term-agent-query",
            "key": "agent-query",
            "definition": "A query curated by an installed agent.",
            "domains": ["technology"],
            "status": "active",
        },
        "forms": [
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
        ],
    }
    term_file = tmp_path / "term.json"
    term_file.write_text(
        json.dumps(term_payload, ensure_ascii=False),
        encoding="utf-8",
    )
    stored = cli(
        "term",
        "set",
        f"@{term_file}",
    )
    assert stored["key"] == "agent-query"
    assert "term_key" not in stored

    async def agent_roundtrip() -> dict[str, object]:
        transport = StdioTransport(
            command=uv,
            args=[
                *isolated,
                "glosswise",
                "mcp",
            ],
            env=environment,
            cwd=str(tmp_path),
        )
        client = Client(transport)
        await asyncio.wait_for(client.__aenter__(), timeout=30)
        try:
            tools = await asyncio.wait_for(
                client.list_tools(),
                timeout=30,
            )

            async def call(
                name: str,
                arguments: dict[str, object],
            ) -> dict[str, object]:
                response = await asyncio.wait_for(
                    client.call_tool(name, arguments),
                    timeout=30,
                )
                return json.loads(response.content[0].text)

            skill = await call(
                "glosswise_read_skill",
                {},
            )
            workspaces = await call("glosswise_list_workspaces", {})
            configured_languages = await call(
                "glosswise_set_workspace_languages",
                {
                    "languages_json": '["en","ja","ru"]',
                },
            )
            fetched = await call(
                "glosswise_get_record",
                {
                    "kind": "term",
                    "object_id": "term-agent-query",
                },
            )
            updated_term = dict(term_payload["term"])
            updated_term["definition"] = "An updated installed-agent query."
            updated = await call(
                "glosswise_put_term",
                {
                    "term_json": json.dumps(
                        updated_term,
                        ensure_ascii=False,
                    )
                },
            )
            rule = {
                "object_id": "rule-agent-query",
                "title": "Use approved agent query wording",
                "instruction": "Use the preferred target term.",
                "trigger_mode": "lexical",
                "triggers": ["agent query"],
                "source_langs": ["en"],
                "target_langs": ["ja"],
                "status": "active",
            }
            stored_rule = await call(
                "glosswise_put_rule",
                {"rule_json": json.dumps(rule)},
            )
            rule["instruction"] = "Always use the approved target term."
            updated_rule = await call(
                "glosswise_put_rule",
                {"rule_json": json.dumps(rule)},
            )
            listed = await call(
                "glosswise_list_records",
                {"kind": "rule", "status": "active"},
            )
            brief = await call(
                "glosswise_prepare_translation",
                {
                    "text": "Run the agent query.",
                    "source_lang": "en",
                    "target_lang": "ja",
                    "domain": "technology",
                },
            )
            proposed_translation = "エージェントクエリを実行します。"
            scan = await call(
                "glosswise_scan_text",
                {
                    "text": proposed_translation,
                    "text_lang": "ja",
                },
            )
            archived_rule = await call(
                "glosswise_archive",
                {"object_id": "rule-agent-query"},
            )
            archived_term = await call(
                "glosswise_archive",
                {"object_id": "term-agent-query"},
            )
        finally:
            await asyncio.wait_for(
                client.__aexit__(None, None, None),
                timeout=10,
            )
        return {
            "tools": {tool.name for tool in tools},
            "skill": skill,
            "workspaces": workspaces,
            "configured_languages": configured_languages,
            "fetched": fetched,
            "updated": updated,
            "stored_rule": stored_rule,
            "updated_rule": updated_rule,
            "listed": listed,
            "brief": brief,
            "scan": scan,
            "archived_rule": archived_rule,
            "archived_term": archived_term,
        }

    result = asyncio.run(agent_roundtrip())
    assert {
        "glosswise_put_term",
        "glosswise_put_rule",
        "glosswise_get_record",
        "glosswise_list_records",
        "glosswise_archive",
        "glosswise_prepare_translation",
        "glosswise_read_skill",
        "glosswise_list_workspaces",
        "glosswise_create_workspace",
        "glosswise_set_workspace_languages",
        "glosswise_activate_workspace",
    } <= result["tools"]
    assert "Agent translation workflow" in result["skill"]["items"][0]["text"]
    assert result["workspaces"]["items"][0]["id"] == "default"
    assert result["configured_languages"]["items"][0]["default_languages"] == [
        "en",
        "ja",
        "ru",
    ]
    assert result["fetched"]["items"][0]["key"] == "agent-query"
    assert "updated" in result["updated"]["items"][0]["definition"]
    assert result["updated"]["warnings"] == [
        "Term is missing active preferred forms for workspace default languages: ru. Defaults are advisory; the term was stored."
    ]
    assert result["stored_rule"]["error"] is None
    assert "Always" in result["updated_rule"]["items"][0]["instruction"]
    assert [item["object_id"] for item in result["listed"]["items"]] == ["rule-agent-query"]
    assert {"term-agent-query", "rule-agent-query"} <= {item["object_id"] for item in result["brief"]["items"]}
    assert result["scan"]["items"][0]["matched_text"] == "エージェントクエリ"
    assert result["archived_rule"]["items"][0]["status"] == "deprecated"
    assert result["archived_term"]["items"][0]["status"] == "deprecated"


@pytest.mark.full
def test_installed_cli_serves_global_http_mcp_on_requested_port(
    tmp_path: Path,
    release_artifacts: tuple[Path, Path],
) -> None:
    """The wheel CLI should bind HTTP and expose the complete global Toolkit."""
    Client = pytest.importorskip("fastmcp").Client
    uv = shutil.which("uv")
    if uv is None:
        pytest.fail("uv is required for the installed HTTP MCP gate")
    _, wheel = release_artifacts
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = int(listener.getsockname()[1])
    environment = {
        **os.environ,
        "HOME": str(tmp_path / "home"),
        "UV_NO_PROGRESS": "1",
    }
    subprocess.run(
        [
            uv,
            "run",
            "--isolated",
            "--with",
            str(wheel),
            "glosswise",
            "setup",
            "-l",
            "en",
            "-l",
            "ja",
        ],
        check=True,
        capture_output=True,
        text=True,
        cwd=tmp_path,
        env=environment,
    )
    process = subprocess.Popen(
        [
            uv,
            "run",
            "--isolated",
            "--with",
            str(wheel),
            "glosswise",
            "mcp",
            "--transport",
            "http",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
        ],
        cwd=tmp_path,
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    output = ""
    try:
        ready = False
        for _ in range(180):
            if process.poll() is not None:
                break
            try:
                with socket.create_connection(
                    ("127.0.0.1", port),
                    timeout=0.25,
                ):
                    ready = True
                    break
            except OSError:
                time.sleep(0.25)
        if not ready:
            process.terminate()
            output = process.communicate(timeout=10)[0]
            pytest.fail(f"GlossWise HTTP MCP did not start:\n{output}")

        async def inspect_server() -> tuple[int, dict[str, object]]:
            async with Client(f"http://127.0.0.1:{port}/mcp") as client:
                tools = await client.list_tools()
                response = await client.call_tool(
                    "glosswise_list_workspaces",
                    {},
                )
                return len(tools), json.loads(response.content[0].text)

        async def inspect_with_timeout() -> tuple[int, dict[str, object]]:
            return await asyncio.wait_for(
                inspect_server(),
                timeout=30,
            )

        tool_count, result = asyncio.run(inspect_with_timeout())
        assert tool_count == 22
        assert result["error"] is None
        assert result["items"][0]["id"] == "default"
    finally:
        if process.poll() is None:
            process.terminate()
        try:
            output += process.communicate(timeout=10)[0]
        except subprocess.TimeoutExpired:
            process.kill()
            output += process.communicate(timeout=10)[0]
        home = Path(environment["HOME"])
        restore_owner_permissions(home / ".heavenbase")
        restore_owner_permissions(home / ".glosswise")
