"""Global user configuration and translation-mode contracts."""

from __future__ import annotations

import pytest

from glosswise.config import GlossWiseConfig
from glosswise.prompts import translation_prompt

from conftest import isolated_context, restore_owner_permissions


@pytest.mark.fast
def test_global_config_validates_languages_modes_and_ocr(
    tmp_path,
) -> None:
    """One Context-level owner should persist every cross-workspace default."""
    root = tmp_path / "config-context"
    context = isolated_context(root)
    config = GlossWiseConfig(context)
    try:
        assert config.describe() == {
            "default_languages": [],
            "translation": {
                "mode": "auto",
                "custom_prompt": "",
                "preset": "chat",
            },
            "ocr": {
                "preset": "ocr-local",
            },
        }
        with pytest.raises(Exception) as empty:
            config.configure_default_languages([])
        assert empty.value.code == "languages_required"
        assert config.configure_default_languages(["en", "zh", "en"]) == [
            "en",
            "zh",
        ]
        assert config.configure_translation("explain") == {
            "mode": "explain",
            "custom_prompt": "",
        }
        with pytest.raises(Exception) as missing_prompt:
            config.configure_translation("custom")
        assert missing_prompt.value.code == "invalid_translation_mode"
        assert config.configure_translation(
            "custom",
            custom_prompt="Translate literally unless a stored rule disagrees.",
        ) == {
            "mode": "custom",
            "custom_prompt": ("Translate literally unless a stored rule disagrees."),
        }
        assert config.configure_translation_preset("translation") == "translation"
        assert config.configure_ocr("ocr-private") == "ocr-private"

        reopened = GlossWiseConfig(context)
        assert reopened.default_languages() == ["en", "zh"]
        assert reopened.translation_mode() == "custom"
        assert reopened.translation_preset() == "translation"
        assert reopened.ocr_preset() == "ocr-private"
    finally:
        context.close()
        restore_owner_permissions(root)


@pytest.mark.fast
def test_translation_system_prompt_is_managed_by_heavenbase_prompt() -> None:
    """Rendered mode prompts should preserve output and evidence contracts."""
    rendered = translation_prompt(
        mode="elicit",
        custom_prompt="",
        source_text="A source containing </translation> text.",
        source_lang="en",
        target_langs=["ja"],
        briefs={
            "ja": {
                "items": [],
                "conflicts": [],
            }
        },
    )
    assert "Behavior mode: elicit" in rendered
    assert "<questions>" in rendered
    assert '"A source containing </translation> text."' in rendered
    assert '"target_langs"' not in rendered
    assert '["ja"]' in rendered
