"""Executable proof for the agent-first README quickstart."""

from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
import shutil
import subprocess

import pytest

SOURCE_TEXT = (
    "It was on a dreary night of November, that I beheld the accomplishment of my toils. "
    "With an anxiety that almost amounted to agony, I collected the instruments of life "
    "around me, that I might infuse a spark of being into the lifeless thing that lay at my feet."
)
LANGUAGES = ["en", "zh", "fr", "de", "ru", "ja"]
TERMS = [
    {
        "term": {
            "object_id": "term-instruments-of-life",
            "key": "instruments-of-life",
            "definition": "Apparatus used in the experiment that brings the creature to life.",
            "use_when": "Use for the experiment's life-giving apparatus.",
            "status": "active",
        },
        "forms": {
            "en": "instruments of life",
            "zh": "生命仪器",
            "fr": "instruments de vie",
            "de": "Instrumente des Lebens",
            "ru": "орудия жизни",
            "ja": "生命の器具",
        },
    },
    {
        "term": {
            "object_id": "term-spark-of-being",
            "key": "spark-of-being",
            "definition": "The animating essence imparted to lifeless matter.",
            "status": "active",
        },
        "forms": {
            "en": "spark of being",
            "zh": "生命之火",
            "fr": "étincelle d'existence",
            "de": "Funke des Seins",
            "ru": "искра бытия",
            "ja": "存在の火花",
        },
    },
]
CORRECTED_TRANSLATIONS = {
    "zh": ("那是十一月一个阴沉的夜晚，我目睹了自己辛劳的成果。怀着近乎痛苦的焦虑，" "我把生命仪器聚集在身边，想把生命之火注入躺在我脚边的无生命之物中。"),
    "fr": (
        "Ce fut par une lugubre nuit de novembre que je contemplai l’accomplissement de mes travaux. "
        "Avec une anxiété qui confinait presque à l’agonie, je rassemblai autour de moi les "
        "instruments de vie afin d’insuffler une étincelle d'existence à la chose inanimée étendue "
        "à mes pieds."
    ),
    "de": (
        "Es war in einer trüben Novembernacht, als ich die Vollendung meiner Mühen erblickte. "
        "Mit einer Angst, die beinahe an Qual grenzte, versammelte ich die Instrumente des Lebens "
        "um mich, um dem leblosen Ding zu meinen Füßen einen Funken des Seins einzuhauchen."
    ),
    "ru": (
        "В мрачную ноябрьскую ночь я увидел завершение своих трудов. С тревогой, почти переходившей "
        "в агонию, я собрал вокруг себя орудия жизни, чтобы вдохнуть искру бытия в безжизненное "
        "создание, лежавшее у моих ног."
    ),
    "ja": (
        "十一月の陰鬱な夜、私は自らの労苦の成就を目の当たりにした。苦悶に近い不安を抱えながら、"
        "私は生命の器具を周囲に集め、足元に横たわる生命なきものへ存在の火花を吹き込もうとした。"
    ),
}
REQUIRED_SURFACES = {
    "zh": ["生命仪器", "生命之火"],
    "fr": ["instruments de vie", "étincelle d'existence"],
    "de": ["Instrumente des Lebens", "Funken des Seins"],
    "ru": ["орудия жизни", "искру бытия"],
    "ja": ["生命の器具", "存在の火花"],
}


def _term_forms(term: dict[str, object]) -> list[dict[str, str]]:
    """Convert readable demo forms into stable GlossWise records."""
    term_id = str(term["term"]["object_id"])
    return [
        {
            "object_id": f"form-{term_id.removeprefix('term-')}-{lang}",
            "lang": lang,
            "role": "preferred",
            "text": text,
        }
        for lang, text in term["forms"].items()
    ]


@pytest.mark.full
def test_agent_first_quickstart_roundtrip(
    tmp_path: Path,
    release_artifacts: tuple[Path, Path],
) -> None:
    """A fresh install should support the complete natural-language demo."""
    Client = pytest.importorskip("fastmcp").Client
    StdioTransport = pytest.importorskip("fastmcp.client.transports").StdioTransport
    uv = shutil.which("uv")
    if uv is None:
        pytest.fail("uv is required for the README quickstart gate")

    _, wheel = release_artifacts
    isolated = ["run", "--isolated", "--with", str(wheel)]
    environment = {
        **os.environ,
        "HOME": str(tmp_path / "home"),
        "UV_NO_PROGRESS": "1",
    }
    setup = subprocess.run(
        [
            uv,
            *isolated,
            "glosswise",
            "setup",
            *[item for language in LANGUAGES for item in ("--lang", language)],
        ],
        check=True,
        capture_output=True,
        text=True,
        cwd=tmp_path,
        env=environment,
    )
    assert json.loads(setup.stdout)["workspace"]["id"] == "default"

    def new_client() -> object:
        return Client(
            StdioTransport(
                command=uv,
                args=[*isolated, "glosswise", "mcp"],
                env=environment,
                cwd=str(tmp_path),
            )
        )

    async def call(client: object, name: str, arguments: dict[str, object]) -> dict[str, object]:
        response = await asyncio.wait_for(client.call_tool(name, arguments), timeout=30)
        return json.loads(response.content[0].text)

    async def roundtrip() -> dict[str, object]:
        first_session = new_client()
        await asyncio.wait_for(first_session.__aenter__(), timeout=30)
        try:
            created = await call(
                first_session,
                "glosswise_create_workspace",
                {"workspace_id": "frankenstein-lab"},
            )
            configured = await call(
                first_session,
                "glosswise_set_workspace_languages",
                {
                    "workspace_id": "frankenstein-lab",
                    "languages_json": json.dumps(LANGUAGES),
                },
            )
            stored = []
            for payload in TERMS:
                stored.append(
                    await call(
                        first_session,
                        "glosswise_put_term",
                        {
                            "workspace_id": "frankenstein-lab",
                            "term_json": json.dumps(payload["term"], ensure_ascii=False),
                            "forms_json": json.dumps(_term_forms(payload), ensure_ascii=False),
                        },
                    )
                )
        finally:
            await asyncio.wait_for(first_session.__aexit__(None, None, None), timeout=10)

        second_session = new_client()
        await asyncio.wait_for(second_session.__aenter__(), timeout=30)
        try:
            reopened = await call(
                second_session,
                "glosswise_get_workspace",
                {"workspace_id": "frankenstein-lab"},
            )
            briefs = {
                lang: await call(
                    second_session,
                    "glosswise_prepare_translation",
                    {
                        "workspace_id": "frankenstein-lab",
                        "text": SOURCE_TEXT,
                        "source_lang": "en",
                        "target_lang": lang,
                    },
                )
                for lang in LANGUAGES[1:]
            }
            found = await call(
                second_session,
                "glosswise_search_terms",
                {
                    "workspace_id": "frankenstein-lab",
                    "query": "spark",
                    "query_lang": "en",
                },
            )
            spark = TERMS[1]
            edited_form = next(form for form in _term_forms(spark) if form["lang"] == "ja")
            edited_form["text"] = "生命の火花"
            edited = await call(
                second_session,
                "glosswise_put_term",
                {
                    "workspace_id": "frankenstein-lab",
                    "term_json": json.dumps(spark["term"], ensure_ascii=False),
                    "forms_json": json.dumps([edited_form], ensure_ascii=False),
                },
            )
            fetched = await call(
                second_session,
                "glosswise_get_record",
                {
                    "workspace_id": "frankenstein-lab",
                    "kind": "term",
                    "object_id": "term-spark-of-being",
                },
            )
        finally:
            await asyncio.wait_for(second_session.__aexit__(None, None, None), timeout=10)
        return {
            "created": created,
            "configured": configured,
            "stored": stored,
            "reopened": reopened,
            "briefs": briefs,
            "found": found,
            "edited": edited,
            "fetched": fetched,
        }

    result = asyncio.run(roundtrip())
    assert result["created"]["items"][0]["id"] == "frankenstein-lab"
    assert result["configured"]["items"][0]["default_languages"] == LANGUAGES
    assert all(not response["warnings"] for response in result["stored"])
    assert result["reopened"]["items"][0]["id"] == "frankenstein-lab"
    assert result["reopened"]["items"][0]["default_languages"] == LANGUAGES
    assert result["found"]["items"][0]["object_id"] == "term-spark-of-being"

    for lang, brief in result["briefs"].items():
        assert brief["error"] is None
        terms = {item["object_id"]: item for item in brief["items"] if item["kind"] == "term"}
        assert set(terms) == {"term-instruments-of-life", "term-spark-of-being"}
        expected_forms = [term["forms"][lang] for term in TERMS]
        assert all(expected in json.dumps(terms, ensure_ascii=False) for expected in expected_forms)
        assert all(surface.casefold() in CORRECTED_TRANSLATIONS[lang].casefold() for surface in REQUIRED_SURFACES[lang])

    assert result["edited"]["error"] is None
    forms = {form["lang"]: form["text"] for form in result["fetched"]["items"][0]["forms"]}
    assert forms == {
        **TERMS[1]["forms"],
        "ja": "生命の火花",
    }
