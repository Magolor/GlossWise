#!/usr/bin/env bash
set -uo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "${ROOT}"
source "${ROOT}/scripts/_env.bash"
resolve_uv
export PYTHONDONTWRITEBYTECODE=1

cleanup_capture_cache() {
    find "${ROOT}/src/glosswise" -type d -name __pycache__ -prune -exec rm -rf {} +
}

cleanup_capture_cache
trap cleanup_capture_cache EXIT
"${UV_BIN}" run pytest "$@"
status=$?
if [[ "${status}" -eq 5 ]]; then
    echo "[test] no tests collected"
    exit 0
fi
exit "${status}"
