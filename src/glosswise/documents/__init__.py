"""Bounded local-document ingestion and browsing."""

from .pdf import (
    DEFAULT_OCR_DPI,
    MAX_OCR_PAGES,
    MAX_PDF_BYTES,
    PdfProcessor,
)
from .store import DocumentStore
from .text import TextSelection, read_text, select_text

__all__ = [
    "DEFAULT_OCR_DPI",
    "MAX_OCR_PAGES",
    "MAX_PDF_BYTES",
    "DocumentStore",
    "PdfProcessor",
    "TextSelection",
    "read_text",
    "select_text",
]
