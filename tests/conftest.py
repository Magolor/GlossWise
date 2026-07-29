"""Isolated HeavenBase fixtures for GlossWise tests."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
import re
import subprocess
import sys

import pytest

import heavenbase as hb
import glosswise

SEMANTIC_POLICY = {
    "provider": "mock",
    "model": "mock",
    "revision": "fixture-1",
    "normalization": "glosswise-v1",
    "embedding_space": "mock/semantic/fixture-1",
    "dimension": 3,
}
PROJECT_ROOT = Path(__file__).resolve().parents[1]


def isolated_bootstrap(root: Path) -> dict[str, object]:
    """Return a minimal isolated in-memory Context bootstrap.

    Args:
        root (Path): Context state directory.

    Returns:
        dict[str, object]: Bootstrap accepted by `hb.Context.load`.
    """
    return {
        "version": 1,
        "root": str(root),
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
    }


def isolated_context(root: Path) -> hb.Context:
    """Create one Context with isolated state and configuration.

    Args:
        root (Path): Parent directory for Context-owned state.

    Returns:
        hb.Context: Explicit isolated Context.
    """
    return hb.Context.load(
        isolated_bootstrap(root / "state"),
        config=hb.ConfigManager(
            root=str(root / "config"),
            setup=True,
        ),
    )


def restore_owner_permissions(root: Path) -> None:
    """Make an exact disposable Context root removable by pytest.

    Args:
        root (Path): Test-owned Context root.

    Returns:
        None: Permissions are restored only below `root`.
    """
    if not root.exists():
        return
    for path in sorted(root.rglob("*"), key=lambda item: len(item.parts), reverse=True):
        if path.is_symlink():
            continue
        path.chmod(0o700 if path.is_dir() else 0o600)


@pytest.fixture(scope="session")
def release_artifacts(
    tmp_path_factory: pytest.TempPathFactory,
) -> tuple[Path, Path]:
    """Build one source and wheel pair for all release-gate tests."""
    output = tmp_path_factory.mktemp("release-artifacts")
    subprocess.run(
        [
            sys.executable,
            "-m",
            "build",
            "--sdist",
            "--wheel",
            "--outdir",
            str(output),
            str(PROJECT_ROOT),
        ],
        check=True,
    )
    return (
        next(output.glob("glosswise-*.tar.gz")),
        next(output.glob("glosswise-*.whl")),
    )


@pytest.fixture(scope="session")
def glosswise_context(tmp_path_factory: pytest.TempPathFactory) -> Iterator[hb.Context]:
    """Install GlossWise once into an isolated test-session Context."""
    root = tmp_path_factory.mktemp("glosswise-context")
    context = isolated_context(root)
    glosswise.install(context)
    try:
        yield context
    finally:
        context.close()
        restore_owner_permissions(root)


@pytest.fixture
def glosswise_workspace(
    glosswise_context: hb.Context,
    request: pytest.FixtureRequest,
) -> Iterator[hb.HeavenBase]:
    """Create one extension-enabled in-memory workspace per test."""
    suffix = re.sub(r"[^a-z0-9]+", "-", request.node.name.lower()).strip("-")
    workspace = hb.HeavenBase(
        f"test-{suffix}",
        context=glosswise_context,
        backends={"main": {"type": "inmem"}},
    )
    workspace.enable_extension("glosswise")
    glosswise.setup_workspace(workspace)
    yield workspace


@pytest.fixture(scope="module")
def glosswise_sql_workspace(
    glosswise_context: hb.Context,
    request: pytest.FixtureRequest,
) -> Iterator[hb.HeavenBase]:
    """Create one extension-enabled SQLite workspace per test module."""
    suffix = re.sub(r"[^a-z0-9]+", "-", request.node.name.lower()).strip("-")
    workspace = hb.HeavenBase(
        f"sql-{suffix}",
        context=glosswise_context,
        backends={"main": {"type": "sqlite", "database": ":memory:"}},
    )
    workspace.enable_extension("glosswise")
    glosswise.setup_workspace(workspace)
    yield workspace


@pytest.fixture
def glosswise_mcp_workspace(
    glosswise_context: hb.Context,
    request: pytest.FixtureRequest,
) -> Iterator[hb.HeavenBase]:
    """Create one isolated SQLite workspace per MCP test."""
    suffix = re.sub(r"[^a-z0-9]+", "-", request.node.name.lower()).strip("-")
    workspace = hb.HeavenBase(
        f"mcp-{suffix}",
        context=glosswise_context,
        backends={"main": {"type": "sqlite", "database": ":memory:"}},
    )
    workspace.enable_extension("glosswise")
    glosswise.setup_workspace(workspace)
    yield workspace


@pytest.fixture(scope="module")
def glosswise_semantic_workspace(
    glosswise_context: hb.Context,
) -> Iterator[hb.HeavenBase]:
    """Create one SQLite workspace with semantic policy for search tests."""
    workspace = hb.HeavenBase(
        "sql-semantic-search",
        context=glosswise_context,
        backends={"main": {"type": "sqlite", "database": ":memory:"}},
    )
    workspace.enable_extension("glosswise")
    glosswise.setup_workspace(workspace, embedding=SEMANTIC_POLICY)
    yield workspace


@pytest.fixture(scope="module")
def glosswise_no_embedder_workspace(
    glosswise_context: hb.Context,
) -> Iterator[hb.HeavenBase]:
    """Create one semantic-policy workspace with no live embedder."""
    workspace = hb.HeavenBase(
        "sql-no-embedder-search",
        context=glosswise_context,
        backends={"main": {"type": "sqlite", "database": ":memory:"}},
    )
    workspace.enable_extension("glosswise")
    glosswise.setup_workspace(workspace, embedding=SEMANTIC_POLICY)
    yield workspace
