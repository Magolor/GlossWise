"""Short-handle storage for temporary OCR page text."""

from __future__ import annotations

__all__ = ["DocumentStore"]

from collections.abc import Mapping
import json
from pathlib import Path
import re
from secrets import token_hex
import shutil
from typing import Any

from ..errors import GlossWiseError
from .text import read_text

_DEFAULT_ROOT = Path("~/.glosswise/documents")
_HANDLE_PATTERN = re.compile(r"^gw-[0-9a-f]{12}$")
_PAGE_FILE_PATTERN = re.compile(r"^page-[0-9]{4}\.txt$")
_MAX_PAGE_BYTES = 1_000_000
_MAX_PAGE_CHARS = 200_000


class DocumentStore:
    """Own temporary OCR text addressed by short opaque handles.

    Args:
        root (str | Path | None): Storage root. Defaults to
            `~/.glosswise/documents`.
    """

    def __init__(self, root: str | Path | None = None) -> None:
        """Bind the document cache root.

        Args:
            root (str | Path | None): Optional cache root override.

        Returns:
            None: This initializer creates no document handle.
        """
        candidate = _DEFAULT_ROOT.expanduser() if root is None else Path(root).expanduser()
        if candidate.is_symlink():
            raise GlossWiseError(
                "document_access_denied",
                "Document cache root must not be a symlink.",
            )
        self.root = candidate.resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def list(self) -> list[dict[str, object]]:
        """List completed OCR handles newest first.

        Args:
            None.

        Returns:
            list[dict[str, object]]: Redacted document manifests.
        """
        manifests = [
            self._load_manifest(path.name) for path in self.root.iterdir() if path.is_dir() and not path.is_symlink() and _HANDLE_PATTERN.fullmatch(path.name)
        ]
        return sorted(
            manifests,
            key=lambda item: (
                -float(item.get("created_at", 0.0)),
                str(item.get("handle", "")),
            ),
        )

    def describe(self, handle: str) -> dict[str, object]:
        """Return one redacted OCR document manifest.

        Args:
            handle (str): Short `gw-...` document handle.

        Returns:
            dict[str, object]: OCR source and page metadata.

        Raises:
            GlossWiseError: If the handle does not exist or is malformed.
        """
        return self._load_manifest(self._handle(handle))

    def read_page(
        self,
        handle: str,
        page: int,
        *,
        start_line: int | None = None,
        end_line: int | None = None,
    ) -> dict[str, object]:
        """Read a bounded inclusive line range from one OCR page.

        Args:
            handle (str): Short document handle.
            page (int): One-based source PDF page number.
            start_line (int | None): One-based first OCR text line.
            end_line (int | None): Inclusive last OCR text line.

        Returns:
            dict[str, object]: Manifest summary, selection metadata, and text.

        Raises:
            GlossWiseError: If the handle, page, or line range is invalid.
        """
        selected_handle = self._handle(handle)
        manifest = self._load_manifest(selected_handle)
        try:
            page_number = int(page)
        except (TypeError, ValueError) as error:
            raise GlossWiseError(
                "document_not_found",
                "Document page must be an integer.",
            ) from error
        page_meta = next(
            (item for item in manifest.get("pages", ()) if int(item.get("page", 0)) == page_number),
            None,
        )
        if not isinstance(page_meta, Mapping):
            raise GlossWiseError(
                "document_not_found",
                f"Document {selected_handle!r} has no OCR page {page_number}.",
            )
        filename = str(page_meta.get("file", ""))
        expected = f"page-{page_number:04d}.txt"
        if filename != expected or not _PAGE_FILE_PATTERN.fullmatch(filename):
            raise GlossWiseError(
                "document_corrupt",
                f"OCR document {selected_handle!r} has invalid page metadata.",
            )
        directory = self._directory(selected_handle)
        path = directory / filename
        if directory.is_symlink() or path.is_symlink() or not path.is_file():
            raise GlossWiseError(
                "document_corrupt",
                f"OCR document {selected_handle!r} contains an unsafe page file.",
            )
        selection = read_text(
            path,
            start_line=start_line,
            end_line=end_line,
            max_bytes=_MAX_PAGE_BYTES,
            max_chars=_MAX_PAGE_CHARS,
        )
        return {
            "handle": selected_handle,
            "source": dict(manifest.get("source", {})),
            "page": page_number,
            "page_count": manifest.get("page_count"),
            "warnings": list(page_meta.get("warnings", ())),
            "selection": selection.to_dict(),
            "text": selection.text,
        }

    def remove(self, handle: str) -> dict[str, object]:
        """Remove one completed temporary OCR document.

        Args:
            handle (str): Short document handle.

        Returns:
            dict[str, object]: Removal result.

        Raises:
            GlossWiseError: If the handle is absent or malformed.
        """
        selected = self._handle(handle)
        directory = self._directory(selected)
        if not directory.is_dir() or directory.is_symlink():
            raise GlossWiseError(
                "document_not_found",
                f"No OCR document {selected!r} exists.",
            )
        shutil.rmtree(directory)
        return {
            "removed": selected,
        }

    def new_handle(self) -> str:
        """Reserve an unused short handle value.

        Args:
            None.

        Returns:
            str: Unused `gw-...` handle.
        """
        for _ in range(100):
            handle = f"gw-{token_hex(6)}"
            if not self._directory(handle).exists() and not self._temporary(handle).exists():
                return handle
        raise RuntimeError("Could not allocate a unique OCR document handle.")

    def temporary_directory(self, handle: str) -> Path:
        """Create the private staging directory for one handle.

        Args:
            handle (str): Unused handle returned by `new_handle`.

        Returns:
            Path: Newly created private staging directory.
        """
        path = self._temporary(self._handle(handle))
        path.mkdir(mode=0o700)
        return path

    def commit(
        self,
        handle: str,
        manifest: Mapping[str, object],
    ) -> dict[str, object]:
        """Atomically publish one fully written staged OCR document.

        Args:
            handle (str): Reserved handle.
            manifest (Mapping[str, object]): Redacted document manifest.

        Returns:
            dict[str, object]: Published manifest.
        """
        selected = self._handle(handle)
        temporary = self._temporary(selected)
        target = self._directory(selected)
        payload = dict(manifest)
        payload["handle"] = selected
        (temporary / "manifest.json").write_text(
            json.dumps(
                payload,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        temporary.replace(target)
        return payload

    def discard(self, handle: str) -> None:
        """Delete a failed staging directory if it exists.

        Args:
            handle (str): Reserved document handle.

        Returns:
            None: This cleanup method is idempotent.
        """
        temporary = self._temporary(self._handle(handle))
        if temporary.exists():
            if temporary.is_symlink():
                raise GlossWiseError(
                    "document_access_denied",
                    "Document staging directories must not be symlinks.",
                )
            shutil.rmtree(temporary)

    def _load_manifest(self, handle: str) -> dict[str, object]:
        directory = self._directory(handle)
        path = directory / "manifest.json"
        if directory.is_symlink():
            raise GlossWiseError(
                "document_access_denied",
                "Document handles must not resolve through symlinks.",
            )
        if not path.is_file() or path.is_symlink():
            raise GlossWiseError(
                "document_not_found",
                f"No OCR document {handle!r} exists.",
            )
        try:
            payload: Any = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            raise GlossWiseError(
                "document_corrupt",
                f"OCR document {handle!r} has an invalid manifest.",
            ) from error
        if not isinstance(payload, dict):
            raise GlossWiseError(
                "document_corrupt",
                f"OCR document {handle!r} has an invalid manifest.",
            )
        return payload

    def _directory(self, handle: str) -> Path:
        return self.root / handle

    def _temporary(self, handle: str) -> Path:
        return self.root / f".{handle}.tmp"

    @staticmethod
    def _handle(handle: str) -> str:
        selected = str(handle).strip().lower()
        if not _HANDLE_PATTERN.fullmatch(selected):
            raise GlossWiseError(
                "document_not_found",
                "Document handle must use the `gw-` short-handle format.",
            )
        return selected
