"""Public-API-only external consumer smoke program."""

from __future__ import annotations

import json
from pathlib import Path
import sys

import heavenbase as hb
import glosswise

database = Path(sys.argv[1])
context = hb.Context.load(
    {
        "version": 1,
        "root": str(database.parent / "isolated-context"),
        "workspace": "default",
        "backend": {
            "type": "inmem",
            "module": "heavenbase.backends.inmem.backend",
            "name": "system",
        },
        "registry": {
            "hash": "sha256",
            "max_items": None,
            "max_bytes": 1024 * 1024,
        },
    },
    config=hb.ConfigManager(
        root=str(database.parent / "isolated-config"),
        setup=True,
    ),
)
try:
    receipt = glosswise.install(context)
    workspace = hb.HeavenBase(
        "external-consumer",
        context=context,
        backends={
            "main": {
                "type": "sqlite",
                "database": database.resolve().as_uri(),
            }
        },
    )
    workspace.enable_extension("glosswise")
    service = glosswise.setup_workspace(workspace)
    service.put_term(
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
    result = service.prepare_translation(
        "Run this query.",
        source_lang="en",
        target_lang="ja",
        domain="technology",
    )
    print(
        json.dumps(
            {
                "coordinate": receipt.coordinate,
                "glosswise_file": str(Path(glosswise.__file__).resolve()),
                "schema_version": result["schema_version"],
                "error": result["error"],
                "ids": [item["object_id"] for item in result["items"]],
            },
            sort_keys=True,
        )
    )
finally:
    context.close()
