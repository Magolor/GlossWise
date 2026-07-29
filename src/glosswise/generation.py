"""HeavenBase-native translation generation."""

from __future__ import annotations

__all__ = ["TranslationSession"]

from collections.abc import Mapping
import re
from typing import Any

import heavenbase as hb

from .config import GlossWiseConfig
from .errors import GlossWiseError

_BLOCKS = {
    "translation": re.compile(
        r"<translation>(.*?)</translation>",
        re.IGNORECASE | re.DOTALL,
    ),
    "questions": re.compile(
        r"<questions>(.*?)</questions>",
        re.IGNORECASE | re.DOTALL,
    ),
    "explanation": re.compile(
        r"<explanation>(.*?)</explanation>",
        re.IGNORECASE | re.DOTALL,
    ),
}


class TranslationSession:
    """Run translations through one resolved HeavenBase LLM preset.

    Args:
        context (Any): HeavenBase Context owning LLM configuration.
    """

    def __init__(self, context: Any) -> None:
        """Bind translation generation to one HeavenBase Context.

        Args:
            context (Any): HeavenBase Context owning LLM configuration.

        Returns:
            None: This initializer performs no model call.
        """
        self.context = context
        self.config = GlossWiseConfig(context)

    def translate(
        self,
        prompt: str,
        *,
        preset: str | None = None,
    ) -> dict[str, object]:
        """Generate and validate one translation response.

        Args:
            prompt (str): Fully rendered GlossWise translation prompt.
            preset (str | None): HeavenBase LLM preset override. When omitted,
                the global GlossWise translation preset is used.

        Returns:
            dict[str, object]: Parsed translation, questions, explanation, and
            non-secret resolved LLM identity.

        Raises:
            GlossWiseError: If the preset is blank, HeavenBase generation
                fails, or the response violates the output-block contract.
        """
        selected = self.config.translation_preset() if preset is None else str(preset).strip()
        if not selected:
            raise GlossWiseError(
                "invalid_translation_preset",
                "Translation preset must not be blank.",
            )
        try:
            llm = hb.LLM(
                preset=selected,
                context=self.context,
            )
            message = hb.LLMSession(llm=llm).send(
                "Translate the source text supplied in the system message.",
                system=str(prompt),
            )
        except Exception as error:
            raise GlossWiseError(
                "translation_failed",
                (f"HeavenBase translation preset {selected!r} failed " f"({type(error).__name__})."),
            ) from error
        if not isinstance(message, Mapping):
            raise GlossWiseError(
                "translation_output_invalid",
                "HeavenBase LLMSession returned an invalid response.",
            )
        content = message.get("content")
        if not isinstance(content, str):
            raise GlossWiseError(
                "translation_output_invalid",
                "HeavenBase LLMSession returned no text response.",
            )
        return {
            "llm": self._identity(llm),
            **self.parse(content),
        }

    @staticmethod
    def parse(response: str) -> dict[str, object]:
        """Validate and unpack GlossWise translation output blocks.

        Args:
            response (str): Raw LLM response.

        Returns:
            dict[str, object]: Translation or questions plus optional
            explanation and `needs_input`.

        Raises:
            GlossWiseError: If blocks are duplicated, ambiguous, empty, or
                accompanied by text outside the contract.
        """
        rendered = str(response)
        matches = {name: list(pattern.finditer(rendered)) for name, pattern in _BLOCKS.items()}
        if any(len(items) > 1 for items in matches.values()):
            raise GlossWiseError(
                "translation_output_invalid",
                "The LLM returned a duplicate output block.",
            )
        values = {name: items[0].group(1).strip() if items else "" for name, items in matches.items()}
        if bool(values["translation"]) == bool(values["questions"]):
            raise GlossWiseError(
                "translation_output_invalid",
                "The LLM must return exactly one translation or questions block.",
            )
        if values["questions"] and values["explanation"]:
            raise GlossWiseError(
                "translation_output_invalid",
                "The LLM must not explain an unanswered clarification request.",
            )
        remainder = rendered
        for pattern in _BLOCKS.values():
            remainder = pattern.sub("", remainder)
        if remainder.strip():
            raise GlossWiseError(
                "translation_output_invalid",
                "The LLM returned text outside the required output blocks.",
            )
        return {
            "translation": values["translation"] or None,
            "questions": values["questions"] or None,
            "explanation": values["explanation"] or None,
            "needs_input": bool(values["questions"]),
        }

    @staticmethod
    def _identity(llm: Any) -> dict[str, str]:
        spec = llm.spec
        return {
            "preset": str(spec.preset),
            "gateway": str(spec.gateway),
            "provider": str(spec.provider),
            "model": str(spec.model),
            "model_id": str(spec.model_id),
        }
