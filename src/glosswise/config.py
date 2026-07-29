"""Global GlossWise user configuration."""

from __future__ import annotations

__all__ = [
    "DEFAULT_OCR_PRESET",
    "DEFAULT_TRANSLATION_PRESET",
    "TRANSLATION_MODES",
    "GlossWiseConfig",
]

from collections.abc import Sequence
from typing import Any

from .errors import GlossWiseError
from .language import canonicalize_languages

DEFAULT_OCR_PRESET = "ocr-local"
DEFAULT_TRANSLATION_PRESET = "chat"
TRANSLATION_MODES = ("auto", "yolo", "elicit", "explain", "custom")
_LANGUAGES_KEY = "glosswise.user.default_languages"
_MODE_KEY = "glosswise.user.translation.mode"
_CUSTOM_PROMPT_KEY = "glosswise.user.translation.custom_prompt"
_TRANSLATION_PRESET_KEY = "glosswise.user.translation.preset"
_OCR_PRESET_KEY = "glosswise.user.ocr.preset"


class GlossWiseConfig:
    """Own user defaults shared by every GlossWise workspace.

    Args:
        context (Any): HeavenBase Context whose configuration registry stores
            the global GlossWise settings.
    """

    def __init__(self, context: Any) -> None:
        """Bind the global configuration owner to one Context.

        Args:
            context (Any): Owning HeavenBase Context.

        Returns:
            None: This initializer stores configuration authority.
        """
        self.context = context
        self.manager = context.config

    def describe(self) -> dict[str, object]:
        """Return the complete non-secret user configuration.

        Args:
            None.

        Returns:
            dict[str, object]: Canonical languages, translation behavior,
            translation LLM preset, and OCR preset.
        """
        return {
            "default_languages": self.default_languages(),
            "translation": {
                "mode": self.translation_mode(),
                "custom_prompt": self.custom_prompt(),
                "preset": self.translation_preset(),
            },
            "ocr": {
                "preset": self.ocr_preset(),
            },
        }

    def configure_default_languages(
        self,
        languages: Sequence[str],
    ) -> list[str]:
        """Persist languages inherited by newly created workspaces.

        Args:
            languages (Sequence[str]): Non-empty ordered concrete BCP 47 tags.

        Returns:
            list[str]: Canonical, deduplicated tags in input order.

        Raises:
            GlossWiseError: If no language is supplied or a tag is invalid.
        """
        canonical = canonicalize_languages(languages)
        if not canonical:
            raise GlossWiseError(
                "languages_required",
                "At least one default language is required.",
            )
        self._set(_LANGUAGES_KEY, canonical)
        return list(canonical)

    def default_languages(self) -> list[str]:
        """Return languages inherited by newly created workspaces.

        Args:
            None.

        Returns:
            list[str]: Canonical language tags, or an empty list before setup.
        """
        return canonicalize_languages(self._get(_LANGUAGES_KEY, ()) or ())

    def configure_translation(
        self,
        mode: str,
        *,
        custom_prompt: str | None = None,
    ) -> dict[str, object]:
        """Persist how agents should handle translation uncertainty.

        Args:
            mode (str): Supported values:
                - `auto`: Ask more when the workspace is sparse and decide
                  autonomously when it contains strong guidance.
                - `yolo`: Translate immediately from available information.
                - `elicit`: Proactively ask about uncertain terminology.
                - `explain`: Translate, then explain terminology choices.
                - `custom`: Follow `custom_prompt`.
            custom_prompt (str | None): Required behavior instruction for
                `custom`; rejected for all other modes.

        Returns:
            dict[str, object]: Canonical active translation configuration.

        Raises:
            GlossWiseError: If the mode or custom prompt is invalid.
        """
        selected = str(mode).strip().lower()
        if selected not in TRANSLATION_MODES:
            expected = ", ".join(TRANSLATION_MODES)
            raise GlossWiseError(
                "invalid_translation_mode",
                f"Translation mode must be one of {expected}; got {mode!r}.",
            )
        prompt = "" if custom_prompt is None else str(custom_prompt).strip()
        if selected == "custom" and not prompt:
            raise GlossWiseError(
                "invalid_translation_mode",
                "Custom translation mode requires a non-blank prompt.",
            )
        if selected != "custom" and prompt:
            raise GlossWiseError(
                "invalid_translation_mode",
                "A custom prompt is accepted only in custom translation mode.",
            )
        self._set(_MODE_KEY, selected)
        self._set(_CUSTOM_PROMPT_KEY, prompt)
        return {
            "mode": selected,
            "custom_prompt": prompt,
        }

    def translation_mode(self) -> str:
        """Return the configured translation behavior mode.

        Args:
            None.

        Returns:
            str: One of `TRANSLATION_MODES`; defaults to `auto`.
        """
        value = str(self._get(_MODE_KEY, "auto")).strip().lower()
        return value if value in TRANSLATION_MODES else "auto"

    def custom_prompt(self) -> str:
        """Return the active custom translation instruction.

        Args:
            None.

        Returns:
            str: Custom prompt in `custom` mode, otherwise an empty string.
        """
        if self.translation_mode() != "custom":
            return ""
        return str(self._get(_CUSTOM_PROMPT_KEY, "")).strip()

    def configure_translation_preset(self, preset: str) -> str:
        """Persist the HeavenBase preset used for direct translation.

        Args:
            preset (str): Existing or future HeavenBase LLM preset name.

        Returns:
            str: Canonical non-blank preset name.

        Raises:
            GlossWiseError: If the preset is blank.
        """
        selected = str(preset).strip()
        if not selected:
            raise GlossWiseError(
                "invalid_translation_preset",
                "Translation preset must not be blank.",
            )
        self._set(_TRANSLATION_PRESET_KEY, selected)
        return selected

    def translation_preset(self) -> str:
        """Return the configured HeavenBase translation preset.

        Args:
            None.

        Returns:
            str: Preset name; defaults to `chat`.
        """
        return (
            str(
                self._get(
                    _TRANSLATION_PRESET_KEY,
                    DEFAULT_TRANSLATION_PRESET,
                )
            ).strip()
            or DEFAULT_TRANSLATION_PRESET
        )

    def configure_ocr(self, preset: str) -> str:
        """Persist the HeavenBase LLM preset used for PDF OCR.

        Args:
            preset (str): Existing or future HeavenBase LLM preset name.

        Returns:
            str: Canonical non-blank preset name.

        Raises:
            GlossWiseError: If the preset is blank.
        """
        selected = str(preset).strip()
        if not selected:
            raise GlossWiseError(
                "invalid_ocr_preset",
                "OCR preset must not be blank.",
            )
        self._set(_OCR_PRESET_KEY, selected)
        return selected

    def ocr_preset(self) -> str:
        """Return the configured HeavenBase OCR preset.

        Args:
            None.

        Returns:
            str: Preset name; defaults to `ocr-local`.
        """
        return str(self._get(_OCR_PRESET_KEY, DEFAULT_OCR_PRESET)).strip() or DEFAULT_OCR_PRESET

    def _get(self, key: str, default: object) -> object:
        with self.manager.scoped(self.manager.base_scope):
            return self.manager.get(key, default=default)

    def _set(self, key: str, value: object) -> None:
        self.manager.set(
            key,
            value,
            scope=self.manager.base_scope,
        )
