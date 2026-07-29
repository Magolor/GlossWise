"""Installed-wheel GlossWise stdio lifecycle proof."""

from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
import shutil
import subprocess
import textwrap

import pytest


@pytest.mark.full
def test_installed_wheel_serves_prepare_over_stdio(
    tmp_path: Path,
    release_artifacts: tuple[Path, Path],
) -> None:
    """An isolated wheel process should restore data and serve one brief."""
    Client = pytest.importorskip("fastmcp").Client
    StdioTransport = pytest.importorskip("fastmcp.client.transports").StdioTransport
    uv = shutil.which("uv")
    if uv is None:
        pytest.fail("uv is required for the isolated installed-wheel gate")

    _, wheel = release_artifacts
    database = tmp_path / "glosswise.db"
    workspace_id = "glosswise-wheel-stdio"
    environment = {
        **os.environ,
        "HOME": str(tmp_path / "process-home"),
        "UV_NO_PROGRESS": "1",
    }
    seed = textwrap.dedent("""
        import sys

        import heavenbase as hb
        import glosswise

        context = hb.Context.load()
        try:
            glosswise.install(context)
            workspace = hb.HeavenBase(
                sys.argv[1],
                context=context,
                backends={
                    "main": {
                        "type": "sqlite",
                        "database": hb.utils.path_to_file_uri(sys.argv[2]),
                    },
                },
            )
            workspace.enable_extension("glosswise")
            glosswise.setup_workspace(workspace)
            workspace.activate()
            workspace.glosswise.put_term(
                {
                    "object_id": "term-query",
                    "key": "query",
                    "definition": "A database query.",
                    "domains": ["technology"],
                    "priority": 8,
                    "status": "active",
                },
                [
                    {
                        "object_id": "form-query-en",
                        "lang": "en",
                        "role": "preferred",
                        "text": "query",
                    },
                    {
                        "object_id": "form-query-ja",
                        "lang": "ja",
                        "role": "preferred",
                        "text": "クエリ",
                    },
                ],
            )
        finally:
            context.close()
        """)
    isolated = [
        "run",
        "--isolated",
        "--with",
        str(wheel),
    ]
    subprocess.run(
        [
            uv,
            *isolated,
            "python",
            "-c",
            seed,
            workspace_id,
            str(database),
        ],
        check=True,
        cwd=tmp_path,
        env=environment,
    )

    async def roundtrip() -> tuple[set[str], dict[str, object]]:
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
            response = await asyncio.wait_for(
                client.call_tool(
                    "glosswise_prepare_translation",
                    {
                        "text": "Run this query.",
                        "source_lang": "en",
                        "target_lang": "ja",
                        "domain": "technology",
                        "workspace_id": workspace_id,
                    },
                ),
                timeout=30,
            )
        finally:
            await asyncio.wait_for(
                client.__aexit__(None, None, None),
                timeout=10,
            )
        return (
            {tool.name for tool in tools},
            json.loads(response.content[0].text),
        )

    tools, result = asyncio.run(roundtrip())
    assert "glosswise_prepare_translation" in tools
    assert "glosswise_scan_file" not in tools
    assert result["schema_version"] == "1"
    assert result["error"] is None
    assert "term-query" in {item["object_id"] for item in result["items"]}
