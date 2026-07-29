"""HeavenBase LLMSession and translation orchestration contracts."""

from __future__ import annotations

import pytest

from glosswise.api.translation import TranslationService
from glosswise.config import GlossWiseConfig
from glosswise.generation import TranslationSession

from conftest import isolated_context, restore_owner_permissions


@pytest.mark.fast
def test_llm_session_translation_reports_resolved_route(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Direct translation should use LLMSession and expose its resolved route."""
    root = tmp_path / "translation-context"
    context = isolated_context(root)
    captured = {}

    class Spec:
        preset = "translation"
        gateway = "openai"
        provider = "deepseek"
        model = "deepseek-v4-flash"
        model_id = "deepseek-v4-flash"

    class LLM:
        spec = Spec()

    class Session:
        def __init__(self, llm):
            captured["llm"] = llm

        def send(self, prompt, *, system):
            captured["prompt"] = prompt
            captured["system"] = system
            return {
                "role": "assistant",
                "content": ("<translation>翻訳</translation>" "<explanation>Used the preferred term.</explanation>"),
            }

    def create_llm(**kwargs):
        captured["llm_kwargs"] = kwargs
        return LLM()

    monkeypatch.setattr(
        "glosswise.generation.hb.LLM",
        create_llm,
    )
    monkeypatch.setattr("glosswise.generation.hb.LLMSession", Session)
    GlossWiseConfig(context).configure_translation_preset("translation")
    try:
        result = TranslationSession(context).translate("Translate this.")
        assert captured["llm_kwargs"] == {
            "preset": "translation",
            "context": context,
        }
        assert captured["prompt"] == ("Translate the source text supplied in the system message.")
        assert captured["system"] == "Translate this."
        assert result == {
            "llm": {
                "preset": "translation",
                "gateway": "openai",
                "provider": "deepseek",
                "model": "deepseek-v4-flash",
                "model_id": "deepseek-v4-flash",
            },
            "translation": "翻訳",
            "questions": None,
            "explanation": "Used the preferred term.",
            "needs_input": False,
        }
    finally:
        context.close()
        restore_owner_permissions(root)


@pytest.mark.fast
def test_translation_output_accepts_questions_and_rejects_ambiguity() -> None:
    """Elicitation is distinct from successful translation."""
    assert TranslationSession.parse("<questions>Choose A or B?</questions>") == {
        "translation": None,
        "questions": "Choose A or B?",
        "explanation": None,
        "needs_input": True,
    }
    with pytest.raises(Exception) as invalid:
        TranslationSession.parse("<translation>A</translation><questions>B?</questions>")
    assert invalid.value.code == "translation_output_invalid"
    with pytest.raises(Exception) as duplicate:
        TranslationSession.parse(
            "<translation>A</translation><translation>B</translation>",
        )
    assert duplicate.value.code == "translation_output_invalid"
    with pytest.raises(Exception) as prose:
        TranslationSession.parse("Result: <translation>A</translation>")
    assert prose.value.code == "translation_output_invalid"


@pytest.mark.fast
def test_translation_uses_default_targets_mode_and_preset(
    glosswise_sql_workspace,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The application layer should prepare one brief per inferred target."""
    workspace = glosswise_sql_workspace
    workspace.glosswise.configure_default_languages(["en", "ja", "fr"])
    GlossWiseConfig(workspace.context).configure_translation("explain")
    captured = {}

    def translate(_self, prompt, *, preset=None):
        captured["prompt"] = prompt
        captured["preset"] = preset
        return {
            "llm": {
                "preset": "translation",
                "gateway": "openai",
                "provider": "deepseek",
                "model": "deepseek-v4-flash",
                "model_id": "deepseek-v4-flash",
            },
            "translation": "JA + FR",
            "questions": None,
            "explanation": "Two targets.",
            "needs_input": False,
        }

    monkeypatch.setattr(TranslationSession, "translate", translate)
    result = TranslationService(workspace).translate(
        "Use the API.",
        source_lang="en",
        preset="translation",
    )
    assert result["target_langs"] == ["ja", "fr"]
    assert set(result["evidence"]) == {"ja", "fr"}
    assert result["mode"] == "explain"
    assert "Behavior mode: explain" in captured["prompt"]
    assert captured["preset"] == "translation"
    assert result["translation"] == "JA + FR"
