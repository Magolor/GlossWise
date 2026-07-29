"""Entity, extension, and curator-service contracts."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import textwrap
import warnings

import pytest

import heavenbase as hb
import glosswise
from glosswise import is_glosswise_error

from conftest import restore_owner_permissions

ENTITY_IDS = {
    "glosswise-term",
    "glosswise-term-form",
    "glosswise-rule",
    "glosswise-example",
}


def active_term(object_id: str, key: str) -> dict[str, object]:
    """Create the minimum active term payload for one test."""
    return {
        "object_id": object_id,
        "key": key,
        "definition": f"Definition of {key}",
        "status": "active",
    }


def preferred_form(
    object_id: str,
    text: str,
    *,
    lang: str = "en",
) -> dict[str, object]:
    """Create the minimum active preferred-form payload for one test."""
    return {
        "object_id": object_id,
        "lang": lang,
        "role": "preferred",
        "text": text,
    }


@pytest.mark.fast
def test_activation_binds_four_entities_and_exact_workspace_service(
    glosswise_workspace: hb.HeavenBase,
) -> None:
    """Activation should expose only resolver-local entity identities."""
    workspace = glosswise_workspace
    assert ENTITY_IDS <= set(workspace.entities)
    assert workspace.glosswise.workspace is workspace
    assert workspace.glosswise.context is workspace.context
    assert glosswise.setup_workspace(workspace) is workspace.glosswise
    assert "agent-skill" not in workspace.entities
    workspace.glosswise.to_mcp(profile="glosswise")
    Skill = workspace.entities["agent-skill"]
    skills = workspace.query(Skill).where(Skill.name == "glosswise").execute().rows()
    assert len(skills) == 1


@pytest.mark.fast
def test_sqlite_schema_avoids_reserved_provider_names(
    glosswise_context: hb.Context,
) -> None:
    """SQLite activation should not warn about GlossWise physical names."""
    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always")
        workspace = hb.HeavenBase(
            "sqlite-safe-physical-names",
            context=glosswise_context,
            backends={"main": {"type": "sqlite", "database": ":memory:"}},
        )
        workspace.enable_extension("glosswise")
        glosswise.setup_workspace(workspace)
    messages = [str(item.message) for item in captured]
    assert not any("reserved provider name" in message for message in messages)


@pytest.mark.fast
def test_curator_service_derives_canonical_form_fields(
    glosswise_workspace: hb.HeavenBase,
) -> None:
    """Term writes should derive search and normalization data centrally."""
    stored = glosswise_workspace.glosswise.put_term(
        active_term("term-api", "api"),
        [preferred_form("form-api-en", "ＡＰＩ!", lang="en-us")],
    )
    form = stored["forms"][0]
    assert form["term_id"] == "term-api"
    assert form["lang"] == "en-US"
    assert form["normalized_text"] == "api"
    assert form["triggers"] == ["ＡＰＩ!"]
    assert form["embedding_space"] == ""

    updated = glosswise_workspace.glosswise.put_term(
        {
            **active_term("term-api", "api"),
            "definition": "Updated API definition",
            "domains": ["technology"],
        },
        [],
    )
    assert updated["forms"][0]["domains"] == ["technology"]
    assert "Updated API definition" in updated["forms"][0]["search_text"]


@pytest.mark.fast
def test_hydrated_term_roundtrip_does_not_stringify_null_metadata(
    glosswise_workspace: hb.HeavenBase,
) -> None:
    """Agent round-trips must not turn absent metadata into literal text."""
    service = glosswise_workspace.glosswise
    stored = service.put_term(
        {
            "object_id": "term-spark",
            "key": "spark",
            "status": "active",
        },
        [preferred_form("form-spark-en", "spark")],
    )
    hydrated = {
        **stored,
        "definition": None,
    }

    roundtripped = service.put_term(hydrated, stored["forms"])

    assert roundtripped["forms"][0]["search_text"] == "spark"
    assert "None" not in roundtripped["forms"][0]["search_text"]


@pytest.mark.fast
def test_workspace_default_languages_are_advisory(
    glosswise_workspace: hb.HeavenBase,
) -> None:
    """Default languages should guide term coverage without rejecting writes."""
    service = glosswise_workspace.glosswise
    assert service.default_languages() == []
    assert service.configure_default_languages(
        ["en-us", "zh", "en-US", "ru"],
    ) == ["en-US", "zh", "ru"]
    assert service.default_languages() == ["en-US", "zh", "ru"]
    assert service.info()["default_languages"] == ["en-US", "zh", "ru"]

    stored = service.put_term(
        active_term("term-language-hint", "language-hint"),
        [
            preferred_form(
                "form-language-hint-en",
                "language hint",
                lang="en-US",
            )
        ],
    )
    assert service.term_language_advisory(stored) == {
        "default_languages": ["en-US", "zh", "ru"],
        "present_languages": ["en-US"],
        "missing_languages": ["zh", "ru"],
        "complete": False,
        "enforced": False,
    }

    with pytest.raises(Exception) as wildcard:
        service.configure_default_languages(["*"])
    assert is_glosswise_error(wildcard.value)
    assert wildcard.value.code == "invalid_language_tag"
    assert service.default_languages() == ["en-US", "zh", "ru"]
    assert service.configure_default_languages([]) == []
    assert service.term_language_advisory(stored)["complete"] is True


@pytest.mark.fast
def test_active_term_requires_preferred_form_and_unique_key(
    glosswise_workspace: hb.HeavenBase,
) -> None:
    """Public curation must enforce semantic invariants before persistence."""
    service = glosswise_workspace.glosswise
    with pytest.raises(Exception) as missing:
        service.put_term(active_term("term-empty", "empty"), [])
    assert is_glosswise_error(missing.value)
    assert missing.value.code == "term_conflict"

    service.put_term(
        active_term("term-first", "shared-key"),
        [preferred_form("form-first", "First")],
    )
    with pytest.raises(Exception) as duplicate:
        service.put_term(
            active_term("term-second", "shared-key"),
            [preferred_form("form-second", "Second")],
        )
    assert is_glosswise_error(duplicate.value)
    assert duplicate.value.code == "term_conflict"
    assert set(duplicate.value.object_ids) == {"term-first", "term-second"}

    with pytest.raises(Exception) as demoted:
        service.put_term(
            active_term("term-first", "shared-key"),
            [
                {
                    **preferred_form("form-first", "First"),
                    "status": "deprecated",
                }
            ],
        )
    assert is_glosswise_error(demoted.value)
    assert demoted.value.code == "term_conflict"


@pytest.mark.fast
def test_normalized_form_identity_is_unique(
    glosswise_workspace: hb.HeavenBase,
) -> None:
    """Equivalent forms in one language and role should be rejected."""
    service = glosswise_workspace.glosswise
    with pytest.raises(Exception) as duplicate:
        service.put_term(
            active_term("term-duplicate", "duplicate"),
            [
                preferred_form("form-one", "API"),
                preferred_form("form-two", "ＡＰＩ!"),
            ],
        )
    assert is_glosswise_error(duplicate.value)
    assert duplicate.value.code == "term_conflict"
    assert set(duplicate.value.object_ids) == {"form-one", "form-two"}

    service.put_term(
        active_term("term-stored", "stored"),
        [preferred_form("form-stored", "API")],
    )
    with pytest.raises(Exception) as stored_duplicate:
        service.put_term(
            active_term("term-stored", "stored"),
            [preferred_form("form-new", "ＡＰＩ!")],
        )
    assert is_glosswise_error(stored_duplicate.value)
    assert set(stored_duplicate.value.object_ids) == {
        "form-stored",
        "form-new",
    }


@pytest.mark.fast
def test_profiles_expose_only_domain_owned_mutation(
    glosswise_context: hb.Context,
) -> None:
    """Read profiles stay safe and curator mutation stays domain-specific."""
    mutation_names = {
        "insert",
        "upsert",
        "set",
        "update",
        "delete",
        "query",
    }
    normal = glosswise_context.modules().resolve("mcp_profile", "glosswise")
    local = glosswise_context.modules().resolve("mcp_profile", "glosswise-local")
    curator = glosswise_context.modules().resolve(
        "mcp_profile",
        "glosswise-curator",
    )
    assert not mutation_names & {*normal["tools"], *local["tools"]}
    assert not mutation_names & set(curator["tools"])
    assert {
        "glosswise_put_term",
        "glosswise_put_rule",
        "glosswise_put_example",
        "glosswise_archive",
    } <= set(curator["tools"])
    assert set(normal["entities"]) == ENTITY_IDS
    assert set(local["entities"]) == ENTITY_IDS
    assert set(curator["entities"]) == ENTITY_IDS


@pytest.mark.fast
def test_embedding_policy_is_scoped_per_workspace(
    glosswise_context: hb.Context,
) -> None:
    """Two workspaces may pin different compatible embedding identities."""
    first = hb.HeavenBase(
        "embedding-scope-first",
        context=glosswise_context,
        backends={"main": {"type": "inmem"}},
    )
    second = hb.HeavenBase(
        "embedding-scope-second",
        context=glosswise_context,
        backends={"main": {"type": "inmem"}},
    )
    first.enable_extension("glosswise")
    second.enable_extension("glosswise")
    default = glosswise.setup_workspace(first).embedding_policy()
    custom = glosswise.setup_workspace(
        second,
        embedding={
            "provider": "fixture",
            "model": "deterministic",
            "revision": "1",
            "normalization": "glosswise-v1",
            "embedding_space": "fixture/deterministic/1",
            "dimension": 3,
        },
    ).embedding_policy()
    assert default["embedding_space"] == "none/3/glosswise-v1"
    assert custom["embedding_space"] == "fixture/deterministic/1"
    assert glosswise.setup_workspace(second).embedding_policy() == custom
    with pytest.raises(Exception) as mismatch:
        glosswise.setup_workspace(
            first,
            embedding={
                "provider": "fixture",
                "model": "deterministic",
                "revision": "1",
                "normalization": "glosswise-v1",
                "embedding_space": "fixture/deterministic/1",
                "dimension": 3,
            },
        )
    assert is_glosswise_error(mismatch.value)
    assert mismatch.value.code == "embedding_space_mismatch"


@pytest.mark.full
def test_workspace_configuration_survives_process_restart(tmp_path: Path) -> None:
    """A new interpreter should observe embedding and language configuration."""
    root = tmp_path / "process-restart"
    program = textwrap.dedent("""
        import json
        import sys

        import heavenbase as hb
        import glosswise

        context = hb.Context.load()
        try:
            if sys.argv[1] == "write":
                glosswise.install(context)
            workspace = hb.HeavenBase(
                "embedding-process-restart",
                context=context,
                backends={"main": {"type": "inmem"}},
            )
            workspace.enable_extension("glosswise")
            if sys.argv[1] == "write":
                service = glosswise.setup_workspace(workspace)
                service.configure_default_languages(["en", "zh", "ru"])
            else:
                service = workspace.glosswise
            print(json.dumps({
                "embedding": service.embedding_policy(),
                "default_languages": service.default_languages(),
            }, sort_keys=True))
        finally:
            context.close()
        """)
    home = root / "home"
    home.mkdir(parents=True)
    environment = {**os.environ, "HOME": str(home)}
    write = subprocess.run(
        [sys.executable, "-c", program, "write"],
        check=True,
        capture_output=True,
        text=True,
        env=environment,
    )
    read = subprocess.run(
        [sys.executable, "-c", program, "read"],
        check=True,
        capture_output=True,
        text=True,
        env=environment,
    )
    try:
        assert json.loads(read.stdout) == json.loads(write.stdout)
        assert json.loads(read.stdout)["embedding"]["embedding_space"] == ("none/3/glosswise-v1")
        assert json.loads(read.stdout)["default_languages"] == ["en", "zh", "ru"]
    finally:
        restore_owner_permissions(root)
