"""Page-wise PDF rendering and HeavenBase OCR."""

from __future__ import annotations

__all__ = [
    "DEFAULT_OCR_DPI",
    "MAX_OCR_PAGES",
    "MAX_PDF_BYTES",
    "PdfProcessor",
]

from collections.abc import Callable
from hashlib import sha256
from math import ceil
from pathlib import Path
import re
from time import time
from typing import Any

import heavenbase as hb

from ..errors import GlossWiseError
from ..prompts import ocr_page_prompt
from .store import DocumentStore

DEFAULT_OCR_DPI = 144
MAX_OCR_PAGES = 50
MAX_PDF_BYTES = 50_000_000
_MAX_PAGE_TEXT_CHARS = 200_000
_MAX_RENDER_PIXELS = 25_000_000
_REPETITION_WINDOW_CHARS = 512


class PdfProcessor:
    """Render PDF pages and OCR them through a HeavenBase LLM preset.

    Args:
        context (Any): HeavenBase Context owning LLM configuration.
        workspace (Any | None): Optional GlossWise workspace authority.
        store (DocumentStore | None): Short-handle OCR text store.
        llm_factory (Callable[..., Any] | None): Testable `hb.LLM` factory.
    """

    def __init__(
        self,
        context: Any,
        *,
        workspace: Any | None = None,
        store: DocumentStore | None = None,
        llm_factory: Callable[..., Any] | None = None,
    ) -> None:
        """Bind PDF processing dependencies without invoking a provider.

        Args:
            context (Any): Owning HeavenBase Context.
            workspace (Any | None): Optional workspace used for prompt
                configuration.
            store (DocumentStore | None): Optional document store override.
            llm_factory (Callable[..., Any] | None): Optional LLM constructor.

        Returns:
            None: This initializer performs no OCR.
        """
        self.context = context
        self.workspace = workspace
        self.store = store or DocumentStore()
        self.llm_factory = llm_factory or hb.LLM

    def ocr(
        self,
        path: str | Path,
        *,
        preset: str,
        start_page: int | None = None,
        end_page: int | None = None,
        dpi: int = DEFAULT_OCR_DPI,
    ) -> dict[str, object]:
        """OCR an inclusive page range into per-page text files.

        Args:
            path (str | Path): Existing regular PDF path.
            preset (str): HeavenBase LLM preset used for visual OCR.
            start_page (int | None): One-based first page; defaults to 1.
            end_page (int | None): Inclusive last page; defaults to the final
                page.
            dpi (int): Render resolution from 72 through 600 dots per inch.

        Returns:
            dict[str, object]: Short handle and redacted per-page metadata.

        Raises:
            GlossWiseError: If the file, range, renderer, or OCR provider
                fails.
        """
        candidate = Path(path).expanduser()
        if candidate.is_symlink():
            raise GlossWiseError(
                "file_access_denied",
                "PDF source must be a regular non-symlink file.",
            )
        try:
            source = candidate.resolve(strict=True)
        except OSError as error:
            raise GlossWiseError(
                "file_access_denied",
                "The requested PDF does not exist.",
            ) from error
        if not source.is_file():
            raise GlossWiseError(
                "file_access_denied",
                "PDF source must be a regular non-symlink file.",
            )
        size = source.stat().st_size
        if size > MAX_PDF_BYTES:
            raise GlossWiseError(
                "input_too_large",
                f"PDF exceeds the {MAX_PDF_BYTES}-byte limit.",
            )
        selected_preset = str(preset).strip()
        if not selected_preset:
            raise GlossWiseError(
                "invalid_ocr_preset",
                "OCR preset must not be blank.",
            )
        try:
            selected_dpi = int(dpi)
        except (TypeError, ValueError) as error:
            raise GlossWiseError(
                "invalid_pdf_range",
                "OCR DPI must be an integer.",
            ) from error
        if not 72 <= selected_dpi <= 600:
            raise GlossWiseError(
                "invalid_pdf_range",
                "OCR DPI must be from 72 through 600.",
            )
        try:
            import pypdfium2 as pdfium
        except ImportError as error:
            raise GlossWiseError(
                "pdf_support_unavailable",
                "PDF OCR requires the pypdfium2 and Pillow packages.",
            ) from error
        handle = self.store.new_handle()
        temporary = self.store.temporary_directory(handle)
        try:
            with pdfium.PdfDocument(str(source)) as document:
                page_count = len(document)
                first, last = self._page_range(
                    start_page,
                    end_page,
                    page_count,
                )
                llm = self.llm_factory(
                    preset=selected_preset,
                    context=self.context,
                )
                pages: list[dict[str, object]] = []
                scale = selected_dpi / 72
                for page_number in range(first, last + 1):
                    image_path = temporary / f"page-{page_number:04d}.png"
                    text_path = temporary / f"page-{page_number:04d}.txt"
                    page = document[page_number - 1]
                    try:
                        page_width, page_height = page.get_size()
                        width = ceil(float(page_width) * scale)
                        height = ceil(float(page_height) * scale)
                        if width * height > _MAX_RENDER_PIXELS:
                            raise GlossWiseError(
                                "input_too_large",
                                (f"Rendered PDF page {page_number} exceeds " f"the {_MAX_RENDER_PIXELS}-pixel safety " "limit."),
                            )
                        bitmap = page.render(scale=scale)
                        try:
                            image = bitmap.to_pil()
                            try:
                                image.save(image_path, format="PNG")
                            finally:
                                image.close()
                        finally:
                            bitmap.close()
                    finally:
                        page.close()
                    try:
                        response = llm.chat(
                            ocr_page_prompt(
                                page_number,
                                page_count,
                                workspace=self.workspace,
                            ),
                            images=[str(image_path)],
                            cache=False,
                        )
                        text = "" if response is None else str(response).strip()
                    except Exception as error:
                        raise GlossWiseError(
                            "ocr_failed",
                            f"OCR failed on PDF page {page_number}.",
                        ) from error
                    finally:
                        if image_path.exists():
                            image_path.unlink()
                    if len(text) > _MAX_PAGE_TEXT_CHARS:
                        raise GlossWiseError(
                            "input_too_large",
                            (f"OCR text for PDF page {page_number} exceeds " f"{_MAX_PAGE_TEXT_CHARS} characters."),
                        )
                    warnings = self._text_warnings(text)
                    text_path.write_text(text + "\n", encoding="utf-8")
                    pages.append(
                        {
                            "page": page_number,
                            "file": text_path.name,
                            "chars": len(text),
                            "blank": not bool(text),
                            "sha256": sha256(text.encode("utf-8")).hexdigest(),
                            "warnings": warnings,
                        }
                    )
            return self.store.commit(
                handle,
                {
                    "created_at": time(),
                    "source": {
                        "name": source.name,
                        "bytes": size,
                        "sha256": self._file_sha256(source),
                    },
                    "page_count": page_count,
                    "selected_pages": {
                        "start": first,
                        "end": last,
                    },
                    "ocr": {
                        "preset": selected_preset,
                        "dpi": selected_dpi,
                    },
                    "pages": pages,
                },
            )
        except GlossWiseError:
            self.store.discard(handle)
            raise
        except Exception as error:
            self.store.discard(handle)
            raise GlossWiseError(
                "pdf_processing_failed",
                "The PDF could not be rendered for OCR.",
            ) from error

    @staticmethod
    def _page_range(
        start_page: int | None,
        end_page: int | None,
        page_count: int,
    ) -> tuple[int, int]:
        if page_count < 1:
            raise GlossWiseError(
                "invalid_pdf_range",
                "PDF contains no pages.",
            )
        try:
            first = 1 if start_page is None else int(start_page)
            last = page_count if end_page is None else int(end_page)
        except (TypeError, ValueError) as error:
            raise GlossWiseError(
                "invalid_pdf_range",
                "PDF page boundaries must be integers.",
            ) from error
        if first < 1 or last < first or last > page_count:
            raise GlossWiseError(
                "invalid_pdf_range",
                (f"PDF page range must be within 1 through {page_count} " "with end at or after start."),
            )
        if last - first + 1 > MAX_OCR_PAGES:
            raise GlossWiseError(
                "input_too_large",
                f"One OCR request may contain at most {MAX_OCR_PAGES} pages.",
            )
        return first, last

    @staticmethod
    def _file_sha256(path: Path) -> str:
        digest = sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    @staticmethod
    def _text_warnings(text: str) -> list[str]:
        compact = re.sub(r"\s+", " ", str(text)).strip()
        window = _REPETITION_WINDOW_CHARS
        if len(compact) >= window * 2:
            prefix = compact[:window]
            if compact.find(prefix, window) >= 0:
                return ["OCR output may contain an accidentally repeated long " "passage; compare it with the source page."]
        return []
