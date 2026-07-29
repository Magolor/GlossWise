#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "${ROOT}"
source "${ROOT}/scripts/_env.bash"
resolve_uv
export PYTHONDONTWRITEBYTECODE=1

"${UV_BIN}" lock
"${UV_BIN}" sync --extra dev "$@"
