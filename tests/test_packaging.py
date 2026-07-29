"""Package and capture-root contracts."""

from __future__ import annotations

from email.parser import Parser
from importlib.metadata import version
from pathlib import Path
from zipfile import ZipFile

import pytest
import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CAPTURE_ROOT = PROJECT_ROOT / "src" / "glosswise"
EXPECTED_CAPTURE_FILES = {
    "__main__.py",
    "__init__.py",
    "api/__init__.py",
    "api/app.py",
    "api/translation.py",
    "api/workspaces.py",
    "cli.py",
    "config.py",
    "contracts.py",
    "documents/__init__.py",
    "documents/pdf.py",
    "documents/store.py",
    "documents/text.py",
    "embedding.py",
    "entities.py",
    "errors.py",
    "generation.py",
    "language.py",
    "lifecycle.py",
    "mcp/__init__.py",
    "mcp/factory.py",
    "mcp/generic.py",
    "mcp/tools.py",
    "mcp/workspaces.py",
    "meta.yaml",
    "prompts.py",
    "ranking.py",
    "retrieval.py",
    "service.py",
    "skills/glosswise/SKILL.md",
}


@pytest.mark.fast
def test_capture_root_is_exact_and_clean() -> None:
    """The installed module root must contain only reviewed module assets."""
    assert CAPTURE_ROOT.is_dir()
    assert not any(path.is_symlink() for path in CAPTURE_ROOT.rglob("*"))
    files = {path.relative_to(CAPTURE_ROOT).as_posix() for path in CAPTURE_ROOT.rglob("*") if path.is_file()}
    assert files == EXPECTED_CAPTURE_FILES
    assert all((CAPTURE_ROOT / name).is_file() for name in ("__init__.py", "meta.yaml"))


@pytest.mark.fast
def test_package_and_manifest_versions_match() -> None:
    """Distribution, facade, and module protocol versions must stay aligned."""
    manifest = yaml.safe_load((CAPTURE_ROOT / "meta.yaml").read_text(encoding="utf-8"))
    assert version("glosswise") == "0.1.0.5"
    assert manifest["version"] == version("glosswise")


@pytest.mark.full
def test_wheel_contains_every_module_asset(
    release_artifacts: tuple[Path, Path],
) -> None:
    """The wheel must preserve the exact capturable module files."""
    _, wheel = release_artifacts
    with ZipFile(wheel) as archive:
        names = set(archive.namelist())
        metadata_name = next(name for name in names if name.endswith(".dist-info/METADATA"))
        entry_points_name = next(name for name in names if name.endswith(".dist-info/entry_points.txt"))
        metadata = Parser().parsestr(archive.read(metadata_name).decode("utf-8"))
        entry_points = archive.read(entry_points_name).decode("utf-8")
    assert {f"glosswise/{name}" for name in EXPECTED_CAPTURE_FILES} <= names
    dependencies = metadata.get_all("Requires-Dist", [])
    assert any(value.startswith("heavenbase") and ">=0.1.2.1" in value and "<" not in value for value in dependencies)
    assert any(value.startswith("langcodes") and ">=3.4" in value and "<4" in value for value in dependencies)
    assert any(value.startswith("pillow") and ">=10" in value and "<13" in value for value in dependencies)
    assert any(value.startswith("pypdfium2") and ">=4.30" in value and "<6" in value for value in dependencies)
    assert "glosswise = glosswise.cli:main" in entry_points
