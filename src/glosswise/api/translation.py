"""Translation application orchestration."""

from __future__ import annotations

__all__ = ["TranslationService"]

from collections.abc import Mapping, Sequence
from typing import Any

from ..config import GlossWiseConfig
from ..errors import GlossWiseError
from ..generation import TranslationSession
from ..language import canonicalize_language, canonicalize_languages
from ..prompts import translation_prompt

_MAX_TARGET_LANGUAGES = 20


class TranslationService:
    """Prepare GlossWise briefs and invoke HeavenBase LLMSession.

    Args:
        workspace (Any): Live GlossWise-enabled workspace.
    """

    def __init__(self, workspace: Any) -> None:
        """Bind translation orchestration to one workspace.

        Args:
            workspace (Any): Owning GlossWise-enabled workspace.

        Returns:
            None: This initializer invokes no model.
        """
        self.workspace = workspace
        self.service = workspace.glosswise
        self.context = workspace.context

    def translate(
        self,
        text: str,
        *,
        target_langs: Sequence[str] | None = None,
        source_lang: str = "auto",
        domain: str | None = None,
        topic: str | None = None,
        style: str | None = None,
        preset: str | None = None,
    ) -> dict[str, object]:
        """Translate source text with workspace evidence and user behavior.

        Args:
            text (str): Source text.
            target_langs (Sequence[str] | None): Concrete target tags. Omit
                them to use workspace languages, then global user defaults.
            source_lang (str): Concrete source tag or `auto`.
            domain (str | None): Optional terminology domain.
            topic (str | None): Optional rule/example topic.
            style (str | None): Optional translation style.
            preset (str | None): HeavenBase LLM preset override. When omitted,
                the global GlossWise translation preset is used.

        Returns:
            dict[str, object]: Translation or elicitation questions with
            resolved LLM identity and evidence summaries.

        Raises:
            GlossWiseError: If no target language exists or generation fails.
        """
        source = canonicalize_language(source_lang, allow_auto=True)
        explicit_targets = target_langs is not None
        configured = self.service.default_languages() or GlossWiseConfig(self.context).default_languages()
        targets = canonicalize_languages(configured if target_langs is None else target_langs)
        if not explicit_targets and source != "auto":
            targets = [target for target in targets if target != source]
        if not targets:
            raise GlossWiseError(
                "target_language_required",
                ("Translation requires a target language or configured " "workspace default languages."),
            )
        if len(targets) > _MAX_TARGET_LANGUAGES:
            raise GlossWiseError(
                "input_too_large",
                ("One translation request may contain at most " f"{_MAX_TARGET_LANGUAGES} target languages."),
            )
        briefs = {
            target: self.service.prepare_translation(
                text,
                target_lang=target,
                source_lang=source,
                domain=domain,
                topic=topic,
                style=style,
            )
            for target in targets
        }
        config = GlossWiseConfig(self.context)
        mode = config.translation_mode()
        prompt = translation_prompt(
            mode=mode,
            custom_prompt=config.custom_prompt(),
            source_text=text,
            source_lang=source,
            target_langs=targets,
            briefs=briefs,
            workspace=self.workspace,
        )
        result = TranslationSession(self.context).translate(
            prompt,
            preset=preset,
        )
        return {
            "workspace": str(self.workspace.id),
            "mode": mode,
            "source_lang": source,
            "target_langs": targets,
            "evidence": {target: self._brief_summary(brief) for target, brief in briefs.items()},
            **result,
        }

    @staticmethod
    def _brief_summary(
        brief: Mapping[str, object],
    ) -> dict[str, object]:
        return {
            "items": len(brief.get("items", ())),
            "conflicts": len(brief.get("conflicts", ())),
            "warnings": list(brief.get("warnings", ())),
            "truncated": bool(brief.get("truncated", False)),
            "text_sha256": dict(brief.get("request", {})).get("text_sha256"),
        }
