#!/usr/bin/env bash

resolve_uv() {
    if command -v uv >/dev/null 2>&1; then
        UV_BIN="uv"
        return
    fi
    if command -v uv.exe >/dev/null 2>&1; then
        UV_BIN="uv.exe"
        return
    fi
    echo "error: uv or uv.exe is required but was not found on PATH" >&2
    exit 1
}
