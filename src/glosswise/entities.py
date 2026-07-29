"""GlossWise entity declarations."""

from __future__ import annotations

__all__ = [
    "EMBEDDING_DIM",
    "GlossWiseExample",
    "GlossWiseRule",
    "GlossWiseTerm",
    "GlossWiseTermForm",
]

import heavenbase as hb

EMBEDDING_DIM = 3


class GlossWiseTerm(hb.Entity):
    """Store one language-neutral terminology concept."""

    identifier = "glosswise-term"

    term_key = hb.field(hb.ShortText).desc("Curator-facing unique concept key")
    definition = hb.field(hb.LongText).desc("Language-neutral concept meaning")
    use_when = hb.field(hb.LongText).default("").desc("Positive usage guidance")
    avoid_when = hb.field(hb.LongText).default("").desc("Negative or boundary guidance")
    domains = hb.field(hb.Array[hb.ShortText]).default([]).store(strategy=hb.SideTable).desc("Structured domain filters")
    tags = hb.field(hb.Array[hb.ShortText]).default([]).store(strategy=hb.SideTable).desc("Open curator annotations")
    priority = hb.field(hb.Integer).default(0).desc("Deterministic policy priority")
    status = hb.field(hb.ShortText).default("draft").desc("Draft, active, or deprecated")
    related_terms = (
        hb.field(
            hb.HyperG[
                "term" : hb.Identifier["glosswise-term"],
                "relation" : hb.ShortText,
            ]
        )
        .default([])
        .store(strategy=hb.GraphEdge(target="term", on_delete="restrict"))
        .desc("Typed relationships to other terminology concepts")
    )


class GlossWiseTermForm(hb.Entity):
    """Store one independently searchable language-specific term form."""

    identifier = "glosswise-term-form"

    term_id = hb.field(hb.Identifier["glosswise-term"]).desc("Owning concept object id")
    lang = hb.field(hb.ShortText).desc("Canonical BCP 47 language tag")
    role = hb.field(hb.ShortText).desc("Preferred, alias, typo, or prohibited")
    text = hb.field(hb.ShortText).desc("Original display form")
    normalized_text = hb.field(hb.ShortText).desc("Versioned normalized deduplication key")
    usage_note = hb.field(hb.LongText).default("").desc("Form-specific guidance")
    domains = hb.field(hb.Array[hb.ShortText]).default([]).store(strategy=hb.SideTable).desc("Derived parent-domain filters")
    triggers = (
        hb.field(hb.Array[hb.ShortText])
        .default([])
        .store(strategy=hb.SparseGramIndex(normalizer="default"))
        .desc("Exact stored surfaces used by reverse-containment scanning")
    )
    search_text = hb.field(hb.LongText).default("").desc("Derived semantic embedding input")
    embedding = hb.field(hb.Vector[EMBEDDING_DIM]).optional().desc("Concrete vector in the configured embedding space")
    embedding_space = hb.field(hb.ShortText).default("").desc("Embedding model and normalization policy id")
    status = hb.field(hb.ShortText).default("active").desc("Draft, active, or deprecated")


class GlossWiseRule(hb.Entity):
    """Store one general translation instruction."""

    identifier = "glosswise-rule"

    title = hb.field(hb.ShortText).desc("Curator-facing rule title")
    instruction = hb.field(hb.LongText).desc("Translation instruction for an agent")
    trigger_mode = hb.field(hb.ShortText).default("always").desc("Always, lexical, semantic, or hybrid")
    triggers = hb.field(hb.Array[hb.ShortText]).default([]).store(strategy=hb.SparseGramIndex(normalizer="default")).desc("Explicit lexical trigger phrases")
    source_langs = hb.field(hb.Array[hb.ShortText]).default(["*"]).store(strategy=hb.SideTable).desc("Source-language ranges")
    target_langs = hb.field(hb.Array[hb.ShortText]).default(["*"]).store(strategy=hb.SideTable).desc("Target-language ranges")
    topics = hb.field(hb.Array[hb.ShortText]).default([]).store(strategy=hb.SideTable).desc("Structured topic filters")
    styles = hb.field(hb.Array[hb.ShortText]).default([]).store(strategy=hb.SideTable).desc("Structured style filters")
    tags = hb.field(hb.Array[hb.ShortText]).default([]).store(strategy=hb.SideTable).desc("Open curator annotations")
    priority = hb.field(hb.Integer).default(0).desc("Deterministic policy priority")
    status = hb.field(hb.ShortText).default("draft").desc("Draft, active, or deprecated")
    search_text = hb.field(hb.LongText).default("").desc("Derived semantic embedding input")
    embedding = hb.field(hb.Vector[EMBEDDING_DIM]).optional().desc("Concrete vector in the configured embedding space")
    embedding_space = hb.field(hb.ShortText).default("").desc("Embedding model and normalization policy id")
    related_rules = (
        hb.field(
            hb.HyperG[
                "rule" : hb.Identifier["glosswise-rule"],
                "relation" : hb.ShortText,
            ]
        )
        .default([])
        .store(strategy=hb.GraphEdge(target="rule", on_delete="restrict"))
        .desc("Typed relationships to other translation rules")
    )
    referenced_terms = (
        hb.field(
            hb.HyperG[
                "term" : hb.Identifier["glosswise-term"],
                "relation" : hb.ShortText,
            ]
        )
        .default([])
        .store(strategy=hb.GraphEdge(target="term", on_delete="restrict"))
        .desc("Terminology concepts referenced by this rule")
    )


class GlossWiseExample(hb.Entity):
    """Store one annotated source and target translation pair."""

    identifier = "glosswise-example"

    source_text = hb.field(hb.LongText).desc("Source-language example text")
    target_text = hb.field(hb.LongText).desc("Target-language example text")
    source_lang = hb.field(hb.ShortText).desc("Canonical source BCP 47 tag")
    target_lang = hb.field(hb.ShortText).desc("Canonical target BCP 47 tag")
    topic = hb.field(hb.ShortText).default("").desc("Exact topic filter")
    style = hb.field(hb.ShortText).default("").desc("Exact style filter")
    tags = hb.field(hb.Array[hb.ShortText]).default([]).store(strategy=hb.SideTable).desc("Open curator annotations")
    notes = hb.field(hb.LongText).default("").desc("Why this example is useful")
    status = hb.field(hb.ShortText).default("draft").desc("Draft, active, or deprecated")
    search_text = hb.field(hb.LongText).default("").desc("Derived semantic embedding input")
    embedding = hb.field(hb.Vector[EMBEDDING_DIM]).optional().desc("Concrete vector in the configured embedding space")
    embedding_space = hb.field(hb.ShortText).default("").desc("Embedding model and normalization policy id")
    referenced_terms = (
        hb.field(
            hb.HyperG[
                "term" : hb.Identifier["glosswise-term"],
                "relation" : hb.ShortText,
            ]
        )
        .default([])
        .store(strategy=hb.GraphEdge(target="term", on_delete="restrict"))
        .desc("Terminology concepts illustrated by this example")
    )
    referenced_rules = (
        hb.field(
            hb.HyperG[
                "rule" : hb.Identifier["glosswise-rule"],
                "relation" : hb.ShortText,
            ]
        )
        .default([])
        .store(strategy=hb.GraphEdge(target="rule", on_delete="restrict"))
        .desc("Translation rules illustrated by this example")
    )
