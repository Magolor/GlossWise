"""Language-policy contracts."""

from __future__ import annotations

import pytest

from glosswise import GlossWiseError
from glosswise.language import canonicalize_language, canonicalize_language_ranges


@pytest.mark.fast
def test_language_tags_are_canonicalized_without_closed_world_allowlists() -> None:
    """Valid BCP 47 tags should retain standard canonical spelling."""
    assert canonicalize_language("en-us") == "en-US"
    assert canonicalize_language("JA") == "ja"
    assert canonicalize_language("zh-hant-tw") == "zh-Hant-TW"


@pytest.mark.fast
def test_jp_and_request_only_auto_are_rejected_as_stored_languages() -> None:
    """Common country-code mistakes and ambient detection must fail early."""
    for value in ("jp", "auto", "", "not a language"):
        with pytest.raises(GlossWiseError) as failure:
            canonicalize_language(value)
        assert failure.value.code == "invalid_language_tag"
    assert canonicalize_language("auto", allow_auto=True) == "auto"


@pytest.mark.fast
def test_language_ranges_preserve_wildcard_and_deduplicate() -> None:
    """Rule language ranges should remain stable and canonical."""
    assert canonicalize_language_ranges(["*", "en-us", "en-US", "ja"]) == [
        "*",
        "en-US",
        "ja",
    ]
    with pytest.raises(GlossWiseError) as failure:
        canonicalize_language_ranges("en-US")
    assert failure.value.code == "invalid_language_tag"
