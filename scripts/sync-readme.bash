#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "${ROOT}"
source "${ROOT}/scripts/_env.bash"
resolve_uv

CHECK=0
SOURCE="README.en.md"
TARGET="README.md"

if [[ "${1:-}" == "--check" ]]; then
    CHECK=1
elif [[ $# -gt 0 ]]; then
    echo "usage: bash scripts/sync-readme.bash [--check]" >&2
    exit 2
fi

if [[ ! -f "${SOURCE}" ]]; then
    echo "error: ${SOURCE} not found" >&2
    exit 1
fi

if [[ "${CHECK}" -eq 1 ]]; then
    "${UV_BIN}" run python - "${SOURCE}" "${TARGET}" <<'PY'
from pathlib import Path
import sys

source = Path(sys.argv[1])
target = Path(sys.argv[2])
if not target.exists() or target.read_bytes() != source.read_bytes():
    print(f"error: {target} is out of date; run bash scripts/sync-readme.bash", file=sys.stderr)
    raise SystemExit(1)
PY
    echo "[readme] ${TARGET} current"
    exit 0
fi

"${UV_BIN}" run python - "${SOURCE}" "${TARGET}" <<'PY'
from pathlib import Path
import sys

source = Path(sys.argv[1])
target = Path(sys.argv[2])
target.write_bytes(source.read_bytes())
PY
echo "[readme] copied ${SOURCE} to ${TARGET}"
