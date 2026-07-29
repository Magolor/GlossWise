"""Synchronize the reviewable root Skill with the packaged source."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = PROJECT_ROOT / "src" / "glosswise" / "skills" / "glosswise" / "SKILL.md"
DEFAULT_TARGET = PROJECT_ROOT / "SKILL.md"


def sync_skill(source: Path, target: Path, *, check: bool) -> bool:
    """Synchronize one generated Skill copy.

    Args:
        source (Path): Canonical packaged Skill.
        target (Path): Generated public Skill.
        check (bool): Whether to report drift without writing.

    Returns:
        bool: Whether the target already matches or was synchronized.

    Raises:
        FileNotFoundError: If the canonical Skill does not exist.
        ValueError: If the generated target is a symbolic link.
    """
    if not source.is_file():
        raise FileNotFoundError(f"Canonical GlossWise Skill not found: {source}")
    if target.is_symlink():
        raise ValueError(f"Refusing to replace symbolic-link Skill target: {target}")
    expected = source.read_bytes()
    current = target.read_bytes() if target.is_file() else None
    if current == expected:
        return True
    if check:
        return False
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(expected)
    return True


def main(argv: list[str] | None = None) -> int:
    """Run the Skill synchronization command."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Fail without writing when the root Skill is stale.")
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE, help=argparse.SUPPRESS)
    parser.add_argument("--target", type=Path, default=DEFAULT_TARGET, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    try:
        synchronized = sync_skill(args.source.expanduser().resolve(), args.target.expanduser().absolute(), check=args.check)
    except (FileNotFoundError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    if not synchronized:
        print("error: root SKILL.md is stale; run `uv run python scripts/sync-skill.py`.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
