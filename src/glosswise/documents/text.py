"""Bounded line-addressed text reading."""

from __future__ import annotations

__all__ = ["TextSelection", "read_stream", "read_text", "select_text"]

from dataclasses import dataclass
from io import StringIO
from pathlib import Path
from typing import TextIO

from ..contracts import MAX_FILE_BYTES, MAX_TEXT_CHARS
from ..errors import GlossWiseError


@dataclass(frozen=True)
class TextSelection:
    """Represent one bounded inclusive line selection.

    Args:
        text (str): Selected text with original line endings.
        start_line (int): One-based first selected line.
        end_line (int | None): One-based last selected line, or `None` for an
            empty source.
        has_more (bool): Whether at least one later source line exists.
        bytes_read (int): Encoded byte count of selected text.
    """

    text: str
    start_line: int
    end_line: int | None
    has_more: bool
    bytes_read: int

    def to_dict(self) -> dict[str, object]:
        """Return redacted selection metadata.

        Args:
            None.

        Returns:
            dict[str, object]: Line range, size, and continuation state.
        """
        return {
            "start_line": self.start_line,
            "end_line": self.end_line,
            "has_more": self.has_more,
            "chars": len(self.text),
            "bytes": self.bytes_read,
        }


def read_text(
    path: str | Path,
    *,
    encoding: str = "utf-8",
    start_line: int | None = None,
    end_line: int | None = None,
    max_bytes: int = MAX_FILE_BYTES,
    max_chars: int = MAX_TEXT_CHARS,
) -> TextSelection:
    """Read an inclusive line range without materializing the whole file.

    Args:
        path (str | Path): Local text file.
        encoding (str): Strict text decoder.
        start_line (int | None): One-based first line; defaults to 1.
        end_line (int | None): Inclusive last line; defaults to end of file.
        max_bytes (int): Maximum encoded bytes in the selected range.
        max_chars (int): Maximum characters in the selected range.

    Returns:
        TextSelection: Selected text and bounded range metadata.

    Raises:
        GlossWiseError: If the range, decoding, or selected size is invalid.
        OSError: If the file cannot be opened.
    """
    with Path(path).open(
        "r",
        encoding=encoding,
        errors="strict",
        newline="",
    ) as handle:
        return read_stream(
            handle,
            encoding=encoding,
            start_line=start_line,
            end_line=end_line,
            max_bytes=max_bytes,
            max_chars=max_chars,
        )


def select_text(
    text: str,
    *,
    encoding: str = "utf-8",
    start_line: int | None = None,
    end_line: int | None = None,
    max_bytes: int = MAX_FILE_BYTES,
    max_chars: int = MAX_TEXT_CHARS,
) -> TextSelection:
    """Select an inclusive line range from transient text.

    Args:
        text (str): Source text.
        encoding (str): Encoding used for the byte budget.
        start_line (int | None): One-based first line; defaults to 1.
        end_line (int | None): Inclusive last line; defaults to end of text.
        max_bytes (int): Maximum encoded bytes in the selected range.
        max_chars (int): Maximum characters in the selected range.

    Returns:
        TextSelection: Selected text and range metadata.

    Raises:
        GlossWiseError: If the range or selected size is invalid.
    """
    if not isinstance(text, str):
        raise GlossWiseError(
            "invalid_line_range",
            "Text selection requires a string.",
        )
    return read_stream(
        StringIO(text, newline=""),
        encoding=encoding,
        start_line=start_line,
        end_line=end_line,
        max_bytes=max_bytes,
        max_chars=max_chars,
    )


def read_stream(
    handle: TextIO,
    *,
    encoding: str,
    start_line: int | None,
    end_line: int | None,
    max_bytes: int,
    max_chars: int,
) -> TextSelection:
    """Read a bounded inclusive line range from an open text stream.

    Args:
        handle (TextIO): Strict-decoding text stream positioned at its start.
        encoding (str): Encoding used for the selected byte budget.
        start_line (int | None): One-based first line; defaults to 1.
        end_line (int | None): Inclusive last line; defaults to stream end.
        max_bytes (int): Maximum encoded bytes in the selected range.
        max_chars (int): Maximum characters in the selected range.

    Returns:
        TextSelection: Selected text and range metadata.

    Raises:
        GlossWiseError: If the range, decoding, or selected size is invalid.
    """
    start, end = _line_range(start_line, end_line)
    selected: list[str] = []
    selected_bytes = 0
    selected_chars = 0
    last_line: int | None = None
    saw_line = False
    has_more = False
    try:
        for number, line in enumerate(handle, start=1):
            saw_line = True
            if number < start:
                continue
            if end is not None and number > end:
                has_more = True
                break
            selected.append(line)
            last_line = number
            selected_bytes += len(line.encode(encoding))
            selected_chars += len(line)
            if selected_bytes > max_bytes or selected_chars > max_chars:
                raise GlossWiseError(
                    "input_too_large",
                    ("Selected text exceeds the configured " f"{max_bytes}-byte or {max_chars}-character limit."),
                )
    except UnicodeDecodeError as error:
        raise GlossWiseError(
            "decode_failed",
            "The file could not be decoded strictly with the requested encoding.",
        ) from error
    if not selected and start > 1 and (saw_line or start != 1):
        raise GlossWiseError(
            "invalid_line_range",
            f"Start line {start} is beyond the end of the source.",
        )
    return TextSelection(
        text="".join(selected),
        start_line=start,
        end_line=last_line,
        has_more=has_more,
        bytes_read=selected_bytes,
    )


def _line_range(
    start_line: int | None,
    end_line: int | None,
) -> tuple[int, int | None]:
    try:
        start = 1 if start_line is None else int(start_line)
        end = None if end_line is None else int(end_line)
    except (TypeError, ValueError) as error:
        raise GlossWiseError(
            "invalid_line_range",
            "Line boundaries must be integers.",
        ) from error
    if start < 1:
        raise GlossWiseError(
            "invalid_line_range",
            "Start line must be at least 1.",
        )
    if end is not None and end < start:
        raise GlossWiseError(
            "invalid_line_range",
            "End line must be greater than or equal to start line.",
        )
    return start, end
