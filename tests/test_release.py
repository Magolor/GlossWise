"""Release artifact, external-consumer, and documentation gates."""

from __future__ import annotations

import ast
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
import tarfile
from zipfile import ZipFile

import pytest

from glosswise.mcp.generic import (
    GENERIC_FULL_TOOL_NAMES,
    GENERIC_LOCAL_TOOL_NAMES,
    GENERIC_READ_TOOL_NAMES,
)
from test_packaging import EXPECTED_CAPTURE_FILES

PROJECT_ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.full
def test_release_artifacts_have_reviewed_inventory_without_symlinks(
    release_artifacts: tuple[Path, Path],
) -> None:
    """Source and wheel archives must contain only intended path families."""
    source, wheel = release_artifacts
    with tarfile.open(source, "r:gz") as archive:
        members = archive.getmembers()
    assert members
    assert not any(member.issym() or member.islnk() for member in members)
    source_paths = {"/".join(member.name.split("/")[1:]) for member in members if member.isfile()}
    allowed_roots = {"src"}
    allowed_files = {
        "CITATION.cff",
        "CODE_OF_CONDUCT.md",
        "CONTRIBUTING.md",
        "LICENSE",
        "MANIFEST.in",
        "PKG-INFO",
        "README.md",
        "README.ar.md",
        "README.de.md",
        "README.en.md",
        "README.es.md",
        "README.fr.md",
        "README.ja.md",
        "README.ru.md",
        "README.zh.md",
        "SECURITY.md",
        "SKILL.md",
        "pyproject.toml",
        "setup.cfg",
    }
    assert all(path in allowed_files or path.split("/", 1)[0] in allowed_roots for path in source_paths)
    assert not any(path.split("/", 1)[0] in {"docs", "examples", "scripts", "tests"} for path in source_paths)
    assert not any(part in {".git", ".venv", "__pycache__", ".scratch"} for path in source_paths for part in Path(path).parts)

    with ZipFile(wheel) as archive:
        wheel_names = set(archive.namelist())
        symlinks = [name for name in wheel_names if stat.S_ISLNK(archive.getinfo(name).external_attr >> 16)]
    assert symlinks == []
    assert {f"glosswise/{name}" for name in EXPECTED_CAPTURE_FILES} <= wheel_names
    assert all(name.startswith("glosswise/") or re.match(r"glosswise-[^/]+\.dist-info/", name) for name in wheel_names)


@pytest.mark.full
def test_external_consumer_uses_only_public_packages(
    release_artifacts: tuple[Path, Path],
    tmp_path: Path,
) -> None:
    """A clean isolated process should reach its first brief from the wheel."""
    _, wheel = release_artifacts
    consumer = PROJECT_ROOT / "tests" / "external_consumer" / "consumer.py"
    tree = ast.parse(consumer.read_text(encoding="utf-8"))
    imports = {name.name.split(".", 1)[0] for node in ast.walk(tree) if isinstance(node, ast.Import) for name in node.names} | {
        str(node.module).split(".", 1)[0] for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)
    }
    third_party = imports - {
        "__future__",
        "json",
        "pathlib",
        "sys",
    }
    assert third_party == {"heavenbase", "glosswise"}
    uv = shutil.which("uv")
    if uv is None:
        pytest.fail("uv is required for the external-consumer gate")
    environment = {
        **os.environ,
        "HOME": str(tmp_path / "process-home"),
        "UV_NO_PROGRESS": "1",
    }
    environment.pop("PYTHONPATH", None)
    completed = subprocess.run(
        [
            uv,
            "run",
            "--isolated",
            "--with",
            str(wheel),
            "python",
            str(consumer),
            str(tmp_path / "consumer.db"),
        ],
        check=True,
        capture_output=True,
        text=True,
        cwd=tmp_path,
        env=environment,
    )
    result = json.loads(completed.stdout)
    assert result["coordinate"] == "glosswise/glosswise"
    assert result["schema_version"] == "1"
    assert result["error"] is None
    assert "term-query" in result["ids"]
    assert not Path(result["glosswise_file"]).is_relative_to(PROJECT_ROOT)


@pytest.mark.fast
def test_release_docs_keep_first_run_simple_and_state_limits() -> None:
    """Release docs must lead with daily use and keep developer limits honest."""
    readme_source = (PROJECT_ROOT / "README.en.md").read_text(encoding="utf-8")
    readme = " ".join(readme_source.split()).replace("`", "")
    assert "--database" not in readme
    assert "demo project" in readme.lower()
    assert not (PROJECT_ROOT / "examples").exists()
    assert not (PROJECT_ROOT / "tests" / "test_demo.py").exists()
    for first_run_contract in (
        "python -m pip install .",
        "glosswise setup",
        "glosswise mcp --json",
        "~/.agents/skills/glosswise",
        "~/.claude/skills/glosswise",
        "~/.glosswise/",
        "glosswise ws lang",
        "glosswise term set",
        "glosswise brief",
        "glosswise config llm",
        "GlossWiseApp",
        "Connect an agent",
        "Try it: teach once, translate consistently",
        "Everyday prompts",
        "Manage workspaces and terminology",
        "Look up guidance and translate",
        "Start a new session and repeat the same request",
        "claude mcp add --scope user glosswise -- glosswise mcp",
        "codex mcp add glosswise -- glosswise mcp",
        "opencode.json",
        "Frankenstein",
        "instruments of life",
        "spark of being",
        "tests/test_quickstart.py",
        "review the exact agent Skill",
        "MCP tools",
        "MCP profiles",
        "How it works",
        "For developers",
        "practical advantages",
        "HeavenBase",
        "LLMSession",
        "127.0.0.1:61055",
    ):
        assert first_run_contract in readme
    for limitation in (
        "does not choose or hide a translation model",
        "explicitly installed",
        "enabled extensions are not disabled",
        "schema migration is not automated",
        "does not add network authentication",
    ):
        assert limitation in readme
    assert "Archive is not delete" not in readme
    assert "Workspaces, domains, and tags" not in readme
    assert "team" not in readme
    assert "term-api" not in readme
    assert "all men" not in readme
    assert "unalienable Rights" not in readme
    assert "Save this as term.json" not in readme
    agent_blocks = re.findall(r"```text\n(.*?)\n```", readme_source, flags=re.DOTALL)
    assert agent_blocks
    assert all(block.startswith("/glosswise ") for block in agent_blocks)
    assert readme_source.count("/glosswise ") >= 12
    translation_prompts = [
        block for block in agent_blocks if "Use the `frankenstein-lab` workspace." in block and "It was on a dreary night of November" in block
    ]
    assert len(translation_prompts) == 2
    assert translation_prompts[0] == translation_prompts[1]
    assert "The prompt is identical; only the persisted GlossWise workspace has changed." in readme_source
    assert "Remember these preferred translations" not in readme_source
    assert "glosswise config agent" not in readme_source
    profile_rows = re.findall(
        r"^\| `(glosswise_[^`]+)` \| [^|]+ \| ([✓—]) \| ([✓—]) \| ([✓—]) \|$",
        readme_source,
        flags=re.MULTILINE,
    )
    assert {name for name, read, _, _ in profile_rows if read == "✓"} == set(GENERIC_READ_TOOL_NAMES)
    assert {name for name, _, full, _ in profile_rows if full == "✓"} == set(GENERIC_FULL_TOOL_NAMES)
    assert {name for name, _, _, local in profile_rows if local == "✓"} == set(GENERIC_LOCAL_TOOL_NAMES)
    assert "Bare `glosswise mcp` and `glosswise mcp --json` select this profile." in readme_source
    assert "The Skill does not\nselect a profile" in readme_source
    assert "Re-running `glosswise setup` is unnecessary when switching profiles." in readme_source
    assert "Use GlossWise." not in readme_source


@pytest.mark.fast
def test_localized_readmes_are_utf8_structural_peers() -> None:
    """Every locale must preserve source structure and approved terminology."""

    def line_shape(line: str) -> str:
        if not line:
            return "blank"
        if line.startswith("```"):
            return "fence"
        heading = re.match(r"^(#{1,6}) ", line)
        if heading:
            return f"heading-{len(heading.group(1))}"
        if line.startswith("|"):
            return "table"
        if line.startswith(">"):
            return "quote"
        if line.startswith("- "):
            return "list"
        if re.match(r"^\d+\. ", line):
            return "ordered"
        if line.startswith("<") or line.startswith("  <"):
            return "html"
        return "prose"

    locale_terms = {
        "ar": ("مساحة عمل", "وكيل ذكي", "موجز الترجمة", "مصطلح مفضّل", "تلميح", "ملف تعريف MCP"),
        "de": ("Arbeitsbereich", "KI-Agent", "Übersetzungsbriefing", "bevorzug", "Sprachhinweis", "MCP-Profil"),
        "es": ("espacio de trabajo", "agente de IA", "informe de traducción", "término preferido", "indicaci", "perfil"),
        "fr": ("espace de travail", "agent IA", "dossier de traduction", "terme privilégié", "indication", "profil MCP"),
        "ja": ("ワークスペース", "AIエージェント", "翻訳ブリーフ", "優先用語", "言語ヒント", "MCPプロファイル"),
        "ru": ("рабочее пространство", "ИИ-агент", "бриф перевода", "предпочтительный термин", "языков", "профил"),
        "zh": ("工作区", "智能体", "翻译简报", "首选术语", "语言提示", "MCP 配置档"),
    }
    locale_labels = {
        "ar": "العربية",
        "de": "Deutsch",
        "es": "Español",
        "fr": "Français",
        "ja": "日本語",
        "ru": "Русский",
        "zh": "中文",
    }
    stable_anchors = {
        "install",
        "connect-an-agent",
        "try-it-teach-once-translate-consistently",
        "everyday-prompts",
        "mcp-server",
        "python-sdk",
    }
    source_bytes = (PROJECT_ROOT / "README.en.md").read_bytes()
    assert (PROJECT_ROOT / "README.md").read_bytes() == source_bytes
    source = source_bytes.decode("utf-8")
    source_lines = source.splitlines()
    source_shape = tuple(line_shape(line) for line in source_lines)
    source_fences = re.findall(r"^```([^\n]*)$", source, flags=re.MULTILINE)
    source_blocks = re.findall(r"```([^\n]*)\n(.*?)\n```", source, flags=re.DOTALL)
    source_executable = re.findall(r"```(console|json|python|bibtex)\n(.*?)\n```", source, flags=re.DOTALL)
    source_links = set(re.findall(r"\]\(([^)]+)\)", source))

    for locale, approved_terms in locale_terms.items():
        path = PROJECT_ROOT / f"README.{locale}.md"
        raw = path.read_bytes()
        assert not raw.startswith(b"\xef\xbb\xbf")
        assert raw.endswith(b"\n")
        text = raw.decode("utf-8")
        assert "\r" not in text
        assert "\ufffd" not in text
        lines = text.splitlines()
        assert len(lines) == len(source_lines)
        assert tuple(line_shape(line) for line in lines) == source_shape
        assert re.findall(r"^```([^\n]*)$", text, flags=re.MULTILINE) == source_fences
        blocks = re.findall(r"```([^\n]*)\n(.*?)\n```", text, flags=re.DOTALL)
        assert [(tag, len(body.splitlines())) for tag, body in blocks] == [(tag, len(body.splitlines())) for tag, body in source_blocks]
        assert re.findall(r"```(console|json|python|bibtex)\n(.*?)\n```", text, flags=re.DOTALL) == source_executable
        text_blocks = [body for tag, body in blocks if tag == "text"]
        assert max(text_blocks.count(body) for body in text_blocks) == 2
        assert source_links <= set(re.findall(r"\]\(([^)]+)\)", text))
        assert text.count("<strong>") == 1
        assert f"<strong>{locale_labels[locale]}</strong>" in text
        assert all(f'href="README.{other}.md"' in text for other in {"en", *locale_terms} - {locale})
        assert all(f'<a id="{anchor}"></a>' in text for anchor in stable_anchors)
        folded = text.casefold()
        assert all(term.casefold() in folded for term in approved_terms)


@pytest.mark.fast
def test_root_skill_is_generated_and_drift_is_rejected(
    tmp_path: Path,
) -> None:
    """The public Skill projection must be exact and have a negative gate."""
    script = PROJECT_ROOT / "scripts" / "sync-skill.py"
    canonical = PROJECT_ROOT / "src" / "glosswise" / "skills" / "glosswise" / "SKILL.md"
    public = PROJECT_ROOT / "SKILL.md"
    assert public.read_bytes() == canonical.read_bytes()
    assert "Fast path for `/glosswise`" in public.read_text(encoding="utf-8")
    assert "Never echo hydrated fields" in public.read_text(encoding="utf-8")
    subprocess.run(
        [sys.executable, str(script), "--check"],
        check=True,
        cwd=PROJECT_ROOT,
    )

    source = tmp_path / "source.md"
    target = tmp_path / "target.md"
    source.write_text("current\n", encoding="utf-8")
    target.write_text("stale\n", encoding="utf-8")
    stale = subprocess.run(
        [
            sys.executable,
            str(script),
            "--check",
            "--source",
            str(source),
            "--target",
            str(target),
        ],
        capture_output=True,
        text=True,
    )
    assert stale.returncode == 1
    assert target.read_text(encoding="utf-8") == "stale\n"

    subprocess.run(
        [
            sys.executable,
            str(script),
            "--source",
            str(source),
            "--target",
            str(target),
        ],
        check=True,
    )
    assert target.read_bytes() == source.read_bytes()
    pre_commit = (PROJECT_ROOT / ".pre-commit-config.yaml").read_text(encoding="utf-8")
    flake = (PROJECT_ROOT / "scripts" / "flake.bash").read_text(encoding="utf-8")
    assert "python scripts/sync-skill.py" in pre_commit
    assert "scripts/sync-skill.py --check" in flake


@pytest.mark.fast
def test_public_repository_metadata_is_complete_and_portable() -> None:
    """Standalone metadata must be public-facing and machine independent."""
    required = (
        ".github/ISSUE_TEMPLATE/bug_report.yml",
        ".github/ISSUE_TEMPLATE/feature_request.yml",
        ".github/pull_request_template.md",
        ".github/workflows/ci.yml",
        ".pre-commit-config.yaml",
        "AGENTS.md",
        "CITATION.cff",
        "CODE_OF_CONDUCT.md",
        "CONTRIBUTING.md",
        "LICENSE",
        "SECURITY.md",
        "SKILL.md",
        "README.ar.md",
        "README.de.md",
        "README.en.md",
        "README.es.md",
        "README.fr.md",
        "README.ja.md",
        "README.ru.md",
        "README.zh.md",
        "docs/assets/glosswise-banner.png",
        "scripts/sync-readme.bash",
        "scripts/sync-skill.py",
    )
    assert all((PROJECT_ROOT / path).is_file() for path in required)

    public_text = "\n".join(
        (PROJECT_ROOT / path).read_text(encoding="utf-8")
        for path in ("AGENTS.md", "CITATION.cff", "CONTRIBUTING.md", "README.en.md", "SECURITY.md", "SKILL.md", "pyproject.toml")
    )
    assert "https://github.com/Magolor/GlossWise" in public_text
    assert "https://ahvn.top" in public_text
    private_heavenbase_link = "https://github.com/Magolor/" + "HeavenBase"
    assert private_heavenbase_link not in public_text
    assert "/Users/" not in public_text
    assert "HeavenBase-community" not in public_text
    assert "incubated inside" not in public_text
