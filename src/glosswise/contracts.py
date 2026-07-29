"""Versioned bounded result and cursor contracts."""

from __future__ import annotations

__all__ = [
    "DEFAULT_SCAN_LIMIT",
    "MAX_FILE_BYTES",
    "MAX_QUERY_CHARS",
    "MAX_SCAN_LIMIT",
    "MAX_SEARCH_LIMIT",
    "MAX_TEXT_CHARS",
    "SCHEMA_VERSION",
    "decode_cursor",
    "encode_cursor",
    "error_envelope",
    "request_fingerprint",
    "result_envelope",
    "scan_envelope",
]

from base64 import urlsafe_b64decode, urlsafe_b64encode
from collections.abc import Mapping, Sequence
from hashlib import sha256
import json

from .errors import GlossWiseError

SCHEMA_VERSION = "1"
DEFAULT_SCAN_LIMIT = 50
MAX_SCAN_LIMIT = 200
MAX_SEARCH_LIMIT = 50
MAX_QUERY_CHARS = 2_000
MAX_TEXT_CHARS = 20_000
MAX_FILE_BYTES = 20_000


def request_fingerprint(request: Mapping[str, object]) -> str:
    """Hash one redacted request summary for cursor binding.

    Args:
        request (Mapping[str, object]): Request metadata without source text.

    Returns:
        str: Stable SHA-256 hexadecimal digest.
    """
    payload = json.dumps(
        dict(request),
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(payload).hexdigest()


def encode_cursor(offset: int, fingerprint: str) -> str:
    """Encode a deterministic opaque scan cursor.

    Args:
        offset (int): Next result offset.
        fingerprint (str): Bound request digest.

    Returns:
        str: URL-safe opaque cursor.
    """
    payload = json.dumps(
        {"fingerprint": fingerprint, "offset": int(offset), "version": 1},
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return urlsafe_b64encode(payload).decode("ascii").rstrip("=")


def decode_cursor(cursor: str | None, fingerprint: str) -> int:
    """Decode and validate a scan cursor for one request.

    Args:
        cursor (str | None): Opaque cursor from a prior response.
        fingerprint (str): Digest of the current redacted request.

    Returns:
        int: Non-negative page offset.

    Raises:
        GlossWiseError: If the cursor is malformed, stale, or request-bound to
            different input.
    """
    if cursor is None or not str(cursor).strip():
        return 0
    if len(str(cursor)) > 1024:
        raise GlossWiseError(
            "invalid_cursor",
            "Scan cursor exceeds the supported size.",
        )
    try:
        encoded = str(cursor).strip()
        padding = "=" * (-len(encoded) % 4)
        payload = json.loads(urlsafe_b64decode(encoded + padding).decode("utf-8"))
        if not isinstance(payload, Mapping):
            raise TypeError("cursor payload must be a mapping")
        offset = int(payload["offset"])
        valid = type(payload.get("version")) is int and payload.get("version") == 1 and payload.get("fingerprint") == fingerprint and offset >= 0
    except (KeyError, TypeError, ValueError, UnicodeError, json.JSONDecodeError) as error:
        raise GlossWiseError(
            "invalid_cursor",
            "Scan cursor is malformed or no longer valid.",
        ) from error
    if not valid:
        raise GlossWiseError(
            "invalid_cursor",
            "Scan cursor does not match this request.",
        )
    return offset


def scan_envelope(
    *,
    request: Mapping[str, object],
    detected_language: Mapping[str, object],
    items: Sequence[Mapping[str, object]],
    conflicts: Sequence[Mapping[str, object]] = (),
    warnings: Sequence[str] = (),
    truncated: bool = False,
    next_cursor: str | None = None,
) -> dict[str, object]:
    """Build the successful version-one scan envelope.

    Args:
        request (Mapping[str, object]): Redacted request summary.
        detected_language (Mapping[str, object]): Detection evidence.
        items (Sequence[Mapping[str, object]]): Bounded scan findings.
        conflicts (Sequence[Mapping[str, object]]): Bounded conflict records.
        warnings (Sequence[str]): Caller-actionable non-fatal warnings.
        truncated (bool): Whether additional findings are available.
        next_cursor (str | None): Cursor for the next page.

    Returns:
        dict[str, object]: Stable serializable scan response.
    """
    return result_envelope(
        request=request,
        detected_language=detected_language,
        items=items,
        conflicts=conflicts,
        warnings=warnings,
        truncated=truncated,
        next_cursor=next_cursor,
    )


def result_envelope(
    *,
    request: Mapping[str, object],
    detected_language: Mapping[str, object],
    items: Sequence[Mapping[str, object]],
    conflicts: Sequence[Mapping[str, object]] = (),
    warnings: Sequence[str] = (),
    truncated: bool = False,
    next_cursor: str | None = None,
) -> dict[str, object]:
    """Build one successful version-one public result envelope.

    Args:
        request (Mapping[str, object]): Redacted request summary.
        detected_language (Mapping[str, object]): Detection evidence.
        items (Sequence[Mapping[str, object]]): Bounded result items.
        conflicts (Sequence[Mapping[str, object]]): Bounded conflict records.
        warnings (Sequence[str]): Caller-actionable non-fatal warnings.
        truncated (bool): Whether omitted results exist.
        next_cursor (str | None): Cursor when this result supports paging.

    Returns:
        dict[str, object]: Stable serializable public response.
    """
    return {
        "schema_version": SCHEMA_VERSION,
        "request": dict(request),
        "detected_language": dict(detected_language),
        "items": [dict(item) for item in items],
        "conflicts": [dict(item) for item in conflicts],
        "warnings": [str(item) for item in warnings],
        "error": None,
        "truncated": bool(truncated),
        "next_cursor": next_cursor,
    }


def error_envelope(
    *,
    request: Mapping[str, object],
    code: str,
    message: str,
    object_ids: Sequence[str] = (),
) -> dict[str, object]:
    """Build one redacted version-one failure response.

    Args:
        request (Mapping[str, object]): Redacted request summary.
        code (str): Stable machine-readable error code.
        message (str): Caller-facing message without sensitive details.
        object_ids (Sequence[str]): Optional related domain object ids.

    Returns:
        dict[str, object]: Stable serializable failure envelope.
    """
    envelope = result_envelope(
        request=request,
        detected_language={
            "tag": None,
            "confidence": 0.0,
            "method": "unavailable",
        },
        items=(),
    )
    envelope["error"] = {
        "code": str(code),
        "message": str(message),
        "object_ids": [str(item) for item in object_ids],
    }
    return envelope
