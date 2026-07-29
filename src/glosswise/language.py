"""Open-world BCP 47 language policy."""

from __future__ import annotations

__all__ = [
    "DEFAULT_LANGUAGES_CONFIG_KEY",
    "canonicalize_language",
    "canonicalize_language_ranges",
    "canonicalize_languages",
]

from collections.abc import Iterable

import langcodes

from .errors import GlossWiseError

DEFAULT_LANGUAGES_CONFIG_KEY = "glosswise.default_languages"


def canonicalize_language(
    tag: str,
    *,
    allow_auto: bool = False,
) -> str:
    """Validate and canonicalize one BCP 47 language tag.

    Args:
        tag (str): Language tag such as `en`, `ja`, or `zh-CN`.
        allow_auto (bool): Whether the request-only sentinel `auto` is valid.

    Returns:
        str: Canonically cased BCP 47 tag, or `auto` when allowed.

    Raises:
        GlossWiseError: If the tag is blank, malformed, `jp`, or a forbidden
            `auto` value.
    """
    value = str(tag).strip()
    if value.lower() == "auto":
        if allow_auto:
            return "auto"
        raise GlossWiseError(
            "invalid_language_tag",
            "`auto` is valid only for source or scanned text language.",
        )
    if value.lower() == "jp" or not value or not langcodes.tag_is_valid(value):
        raise GlossWiseError(
            "invalid_language_tag",
            f"Invalid BCP 47 language tag {value!r}.",
        )
    return langcodes.standardize_tag(value)


def canonicalize_language_ranges(tags: Iterable[str]) -> list[str]:
    """Canonicalize language filters while preserving the `*` wildcard.

    Args:
        tags (Iterable[str]): Concrete BCP 47 tags or `*`.

    Returns:
        list[str]: Deduplicated canonical tags in input order.

    Raises:
        GlossWiseError: If any non-wildcard value is invalid.
    """
    if isinstance(tags, (str, bytes)):
        raise GlossWiseError(
            "invalid_language_tag",
            "Language ranges must be a list, not one string.",
        )
    values: list[str] = []
    for raw in tags:
        value = "*" if str(raw).strip() == "*" else canonicalize_language(str(raw))
        if value not in values:
            values.append(value)
    return values


def canonicalize_languages(tags: Iterable[str]) -> list[str]:
    """Canonicalize an ordered collection of concrete language tags.

    Args:
        tags (Iterable[str]): Concrete BCP 47 language tags.

    Returns:
        list[str]: Deduplicated canonical tags in input order.

    Raises:
        GlossWiseError: If the collection is a string or contains an invalid,
            wildcard, or request-only language value.
    """
    if isinstance(tags, (str, bytes)):
        raise GlossWiseError(
            "invalid_language_tag",
            "Languages must be a list, not one string.",
        )
    values: list[str] = []
    for raw in tags:
        value = canonicalize_language(str(raw))
        if value not in values:
            values.append(value)
    return values
