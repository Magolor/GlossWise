"""GlossWise module and workspace lifecycle."""

from __future__ import annotations

__all__ = [
    "install",
    "install_agent_skill",
    "install_agent_skills",
    "setup_workspace",
]

from collections.abc import Mapping, Sequence
from importlib.resources import files
from pathlib import Path
from typing import Any

import heavenbase as hb
from heavenbase.utils import delete_path

from .entities import EMBEDDING_DIM
from .errors import GlossWiseError

DEFAULT_EMBEDDING_POLICY: dict[str, object] = {
    "provider": "none",
    "model": "",
    "revision": "",
    "normalization": "glosswise-v1",
    "embedding_space": f"none/{EMBEDDING_DIM}/glosswise-v1",
    "dimension": EMBEDDING_DIM,
}
_DEFAULT_SKILLS_ROOTS = (
    Path("~/.agents/skills"),
    Path("~/.claude/skills"),
)


def _is_glosswise_skill(skill_dir: Path) -> bool:
    target = skill_dir / "SKILL.md"
    return target.is_file() and any(line.strip() == "name: glosswise" for line in target.read_text(encoding="utf-8").splitlines()[:10])


def install(context: hb.Context) -> Any:
    """Install the exact GlossWise module folder into one Context.

    Args:
        context (hb.Context): Explicit machine Context that will own GlossWise.

    Returns:
        Any: HeavenBase install receipt for exact lifecycle tracking.

    Note:
        HeavenBase 0.1.2.1 compiles SparseGram internal SQL types through the
        process-default module resolver. Package modules are therefore set up
        in both the requested Context and the default Context until HeavenBase
        threads the owning resolver through that DDL path.
    """
    modules = context.modules()
    modules.setup()
    if context is not hb.DEFAULT_CONTEXT:
        hb.DEFAULT_CONTEXT.modules().setup()
    return modules.install(Path(__file__).resolve().parent)


def install_agent_skill(
    skills_root: str | Path | None = None,
    *,
    overwrite: bool = False,
    clean: bool = False,
) -> Path:
    """Install the packaged GlossWise Skill into one agent skills root.

    Args:
        skills_root (str | Path | None): Parent agent skills directory.
            Defaults to `~/.agents/skills`.
        overwrite (bool): Whether to replace a different existing Skill.
            An identical installed file is accepted without rewriting.
        clean (bool): Whether to remove and reinstall a verified existing
            GlossWise Skill directory. This is the setup/update path.

    Returns:
        Path: Installed `glosswise/SKILL.md` path.

    Raises:
        FileExistsError: If a conflicting or unverified Skill exists.
        ValueError: If the target folder or file is a symlink or not a
            directory.
    """
    root = Path("~/.agents/skills").expanduser() if skills_root is None else Path(skills_root).expanduser()
    skill_dir = root / "glosswise"
    target = skill_dir / "SKILL.md"
    if skill_dir.is_symlink() or target.is_symlink():
        raise ValueError("GlossWise Skill target must not be a symlink.")
    if skill_dir.exists() and not skill_dir.is_dir():
        raise ValueError(f"GlossWise Skill target must be a directory: {skill_dir}.")
    source = files("glosswise").joinpath("skills").joinpath("glosswise").joinpath("SKILL.md").read_text(encoding="utf-8")
    if clean and skill_dir.exists():
        if not _is_glosswise_skill(skill_dir):
            raise FileExistsError(f"Refusing to replace an unverified Skill directory at {skill_dir}.")
        delete_path(str(skill_dir))
    if target.exists():
        current = target.read_text(encoding="utf-8")
        if current == source:
            return target.resolve()
        if not overwrite:
            raise FileExistsError(f"A different GlossWise Skill already exists at {target}.")
    skill_dir.mkdir(parents=True, exist_ok=True)
    target.write_text(source, encoding="utf-8")
    return target.resolve()


def install_agent_skills(
    skills_roots: Sequence[str | Path] | None = None,
) -> list[Path]:
    """Cleanly reinstall GlossWise for common local agent harnesses.

    Args:
        skills_roots (Sequence[str | Path] | None): Agent skills roots.
            Defaults to both `~/.agents/skills` and `~/.claude/skills`.

    Returns:
        list[Path]: Installed `SKILL.md` paths in root order.

    Raises:
        FileExistsError: If a target contains an unverified Skill.
        ValueError: If a target folder or file is a symlink or not a
            directory.
    """
    requested = tuple(skills_roots) if skills_roots is not None else _DEFAULT_SKILLS_ROOTS
    roots = list(dict.fromkeys(Path(root).expanduser() for root in requested))
    if not roots:
        raise ValueError("At least one agent skills root is required.")
    for root in roots:
        skill_dir = root / "glosswise"
        target = skill_dir / "SKILL.md"
        if skill_dir.is_symlink() or target.is_symlink():
            raise ValueError("GlossWise Skill target must not be a symlink.")
        if skill_dir.exists() and not skill_dir.is_dir():
            raise ValueError(f"GlossWise Skill target must be a directory: {skill_dir}.")
        if skill_dir.exists() and not _is_glosswise_skill(skill_dir):
            raise FileExistsError(f"Refusing to replace an unverified Skill directory at {skill_dir}.")
    return [
        install_agent_skill(
            root,
            overwrite=True,
            clean=True,
        )
        for root in roots
    ]


def setup_workspace(
    workspace: Any,
    *,
    embedding: Mapping[str, object] | None = None,
    embedder: Any | None = None,
) -> Any:
    """Finish GlossWise setup on one extension-enabled workspace.

    Args:
        workspace (Any): HeavenBase workspace with `glosswise` enabled.
        embedding (Mapping[str, object] | None): Optional persisted embedding
            policy. The mapping must contain `provider`, `model`, `revision`,
            `normalization`, `embedding_space`, and a dimension equal to the
            distribution's fixed `EMBEDDING_DIM`.
        embedder (Any | None): Optional live adapter compatible with the
            persisted policy.

    Returns:
        Any: The workspace-bound `GlossWiseService`.

    Raises:
        GlossWiseError: If GlossWise is not enabled or an embedding policy
            conflicts with the stored workspace policy.
    """
    if "glosswise" not in workspace.extensions():
        raise GlossWiseError(
            "extension_not_enabled",
            "Enable the `glosswise` extension before workspace setup.",
        )
    service = workspace.glosswise
    if embedding is not None:
        service.configure_embedding(embedding)
    elif service.embedding_policy() is None:
        service.configure_embedding(DEFAULT_EMBEDDING_POLICY)
    if embedder is not None:
        service.configure_embedder(embedder)
    return service


def _setup_workspace_agent(workspace: Any) -> None:
    """Enable embedded workspace-bound MCP and Skill support on demand."""
    workspace.enable_extension("toolkit")
    workspace.enable_extension("agent")
    skill_type = workspace.entities["agent-skill"]
    skill_dir = files("glosswise").joinpath("skills").joinpath("glosswise")
    skill = skill_type.from_path(str(skill_dir))
    skill.register(ws=workspace)
