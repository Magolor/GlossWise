#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "${ROOT}"
source "${ROOT}/scripts/_env.bash"
resolve_uv
export PYTHONDONTWRITEBYTECODE=1

case "${1:---ci}" in
    --ci)
        "${UV_BIN}" run python scripts/sync-skill.py --check
        bash scripts/sync-readme.bash --check
        "${UV_BIN}" run black --check --diff src tests scripts/sync-skill.py
        "${UV_BIN}" run flake8 src tests scripts/sync-skill.py --max-line-length 160 --extend-ignore E203,W503
        ;;
    --all)
        "${UV_BIN}" run python scripts/sync-skill.py
        bash scripts/sync-readme.bash
        "${UV_BIN}" run black src tests scripts/sync-skill.py
        "${UV_BIN}" run flake8 src tests scripts/sync-skill.py --max-line-length 160 --extend-ignore E203,W503
        ;;
    *)
        echo "usage: bash scripts/flake.bash [--ci|--all]" >&2
        exit 2
        ;;
esac
