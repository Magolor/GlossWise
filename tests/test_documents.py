"""PDF OCR and short-handle document browsing contracts."""

from __future__ import annotations

from pathlib import Path
import json
import re

import pytest
import pypdfium2 as pdfium

from glosswise.documents import DocumentStore, PdfProcessor


def build_pdf(path: Path, pages: int = 2) -> None:
    """Create a small deterministic PDF fixture.

    Args:
        path (Path): Output PDF path.
        pages (int): Number of fixture pages.

    Returns:
        None: The fixture is written to `path`.
    """
    document = pdfium.PdfDocument.new()
    for _number in range(1, pages + 1):
        page = document.new_page(width=612, height=792)
        page.close()
    document.save(path)
    document.close()


@pytest.mark.fast
def test_pdf_ocr_writes_per_page_text_and_short_handle(
    tmp_path: Path,
    glosswise_context,
) -> None:
    """Rendered PNGs should be transient while OCR text remains browsable."""
    source = tmp_path / "source.pdf"
    build_pdf(source)
    store = DocumentStore(tmp_path / "documents")
    calls = []

    class FakeLLM:
        def chat(self, prompt, *, images, cache):
            assert cache is False
            image = Path(images[0])
            assert image.is_file()
            page = int(re.search(r"page (\d+)", prompt).group(1))
            calls.append((page, image.name))
            return f"Page {page}\nSecond line"

    def llm_factory(*, preset, context):
        assert preset == "ocr-local"
        assert context is glosswise_context
        return FakeLLM()

    result = PdfProcessor(
        glosswise_context,
        store=store,
        llm_factory=llm_factory,
    ).ocr(
        source,
        preset="ocr-local",
    )
    assert re.fullmatch(r"gw-[0-9a-f]{12}", result["handle"])
    assert result["selected_pages"] == {
        "start": 1,
        "end": 2,
    }
    assert calls == [
        (1, "page-0001.png"),
        (2, "page-0002.png"),
    ]
    directory = store.root / result["handle"]
    assert not list(directory.glob("*.png"))
    assert sorted(path.name for path in directory.glob("*.txt")) == [
        "page-0001.txt",
        "page-0002.txt",
    ]
    page = store.read_page(
        result["handle"],
        2,
        start_line=2,
        end_line=2,
    )
    assert page["text"] == "Second line\n"
    assert page["warnings"] == []
    assert page["selection"] == {
        "start_line": 2,
        "end_line": 2,
        "has_more": False,
        "chars": 12,
        "bytes": 12,
    }
    assert store.describe(result["handle"])["source"]["name"] == "source.pdf"
    assert store.remove(result["handle"]) == {
        "removed": result["handle"],
    }
    assert not directory.exists()


@pytest.mark.fast
def test_pdf_ocr_flags_long_repetition_without_rewriting_text(
    tmp_path: Path,
    glosswise_context,
) -> None:
    """Suspicious model repetition should remain visible and reviewable."""
    source = tmp_path / "source.pdf"
    build_pdf(source, pages=1)
    store = DocumentStore(tmp_path / "documents")
    passage = " ".join(f"token-{index}" for index in range(100))
    repeated = f"{passage}\n{passage}"

    class RepeatingLLM:
        def chat(self, _prompt, *, images, cache):
            assert Path(images[0]).is_file()
            assert cache is False
            return repeated

    result = PdfProcessor(
        glosswise_context,
        store=store,
        llm_factory=lambda **_kwargs: RepeatingLLM(),
    ).ocr(source, preset="ocr-local")
    warning = "OCR output may contain an accidentally repeated long passage"
    assert warning in result["pages"][0]["warnings"][0]
    page = store.read_page(result["handle"], 1)
    assert page["text"].strip() == repeated
    assert page["warnings"] == result["pages"][0]["warnings"]


@pytest.mark.fast
def test_pdf_ocr_rejects_ranges_and_cleans_failed_staging(
    tmp_path: Path,
    glosswise_context,
) -> None:
    """Invalid or failed OCR should not publish a partial handle."""
    source = tmp_path / "source.pdf"
    build_pdf(source)
    store = DocumentStore(tmp_path / "documents")
    processor = PdfProcessor(
        glosswise_context,
        store=store,
        llm_factory=lambda **_kwargs: None,
    )
    with pytest.raises(Exception) as invalid:
        processor.ocr(
            source,
            preset="ocr-local",
            start_page=2,
            end_page=1,
        )
    assert invalid.value.code == "invalid_pdf_range"
    assert not list(store.root.iterdir())

    class FailedLLM:
        def chat(self, _prompt, *, images, cache):
            assert cache is False
            assert Path(images[0]).is_file()
            raise RuntimeError("provider failed")

    failed = PdfProcessor(
        glosswise_context,
        store=store,
        llm_factory=lambda **_kwargs: FailedLLM(),
    )
    with pytest.raises(Exception) as ocr:
        failed.ocr(source, preset="ocr-local")
    assert ocr.value.code == "ocr_failed"
    assert not list(store.root.iterdir())

    oversized = tmp_path / "oversized-page.pdf"
    document = pdfium.PdfDocument.new()
    page = document.new_page(width=10_000, height=10_000)
    page.close()
    document.save(oversized)
    document.close()
    with pytest.raises(Exception) as pixels:
        failed.ocr(oversized, preset="ocr-local")
    assert pixels.value.code == "input_too_large"
    assert not list(store.root.iterdir())


@pytest.mark.fast
def test_document_store_rejects_tampered_page_paths(
    tmp_path: Path,
) -> None:
    """Manifest page names must never become arbitrary filesystem paths."""
    store = DocumentStore(tmp_path / "documents")
    handle = store.new_handle()
    staging = store.temporary_directory(handle)
    page = staging / "page-0001.txt"
    page.write_text("safe\n", encoding="utf-8")
    store.commit(
        handle,
        {
            "source": {"name": "source.pdf"},
            "page_count": 1,
            "pages": [
                {
                    "page": 1,
                    "file": page.name,
                }
            ],
        },
    )
    manifest = store.root / handle / "manifest.json"
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    payload["pages"][0]["file"] = "../../outside.txt"
    manifest.write_text(
        json.dumps(payload),
        encoding="utf-8",
    )
    with pytest.raises(Exception) as corrupt:
        store.read_page(handle, 1)
    assert corrupt.value.code == "document_corrupt"
