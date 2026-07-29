"""Semantic retrieval and translation-brief orchestration."""

from __future__ import annotations

__all__ = ["GlossWiseRetrieval"]

from collections.abc import Mapping, Sequence
from hashlib import sha256
from typing import Any

from .contracts import (
    MAX_QUERY_CHARS,
    MAX_SEARCH_LIMIT,
    result_envelope,
)
from .errors import GlossWiseError
from .language import canonicalize_language
from .ranking import reciprocal_rank_fusion

_NO_EMBEDDER_WARNING = "No embedder is configured; semantic retrieval was skipped and lexical results remain available."
_MIN_SEMANTIC_SCORE = 0.05


class GlossWiseRetrieval:
    """Execute retrieval through one workspace-bound GlossWise service."""

    def __init__(self, service: Any) -> None:
        """Bind retrieval to the service's exact workspace and Context.

        Args:
            service (Any): Owning `GlossWiseService`.

        Returns:
            None: This initializer stores the domain authority.
        """
        self.service = service
        self.workspace = service.workspace

    def search_terms(
        self,
        query: str,
        *,
        query_lang: str = "auto",
        target_lang: str | None = None,
        domain: str | None = None,
        limit: int = 10,
    ) -> dict[str, object]:
        """Return fused term concepts with matching and target forms."""
        text = self._query_text(query)
        source = canonicalize_language(query_lang, allow_auto=True)
        target = None if target_lang is None else canonicalize_language(target_lang)
        page_size = self._limit(limit)
        scope = self._optional(domain)
        TermForm = self.workspace.entities["glosswise-term-form"]

        lexical_query = (
            self.workspace.query(TermForm).where(TermForm.triggers.contained_in(text) | TermForm.text.match(text)).where(TermForm.status == "active")
        )
        lexical_query = self._term_filters(
            lexical_query,
            TermForm,
            source_lang=source,
            domain=scope,
        )
        lexical_rows = lexical_query.execute().rows()

        semantic_rows: list[dict[str, object]] = []
        warnings = []
        if self.service.embedding_available():
            vector = self.service._embed_text(text)
            semantic_query = (
                self.workspace.query(TermForm)
                .where(TermForm.status == "active")
                .where(TermForm.embedding_space == self.service.embedding_policy()["embedding_space"])
            )
            semantic_query = self._term_filters(
                semantic_query,
                TermForm,
                source_lang=source,
                domain=scope,
            )
            semantic_rows = self._near_all(
                TermForm,
                semantic_query,
                TermForm.embedding,
                vector,
            )
        else:
            warnings.append(_NO_EMBEDDER_WARNING)
        terms = self.service._terms_by_id(str(row["term_id"]) for row in [*lexical_rows, *semantic_rows])
        lexical_candidates = self._term_signal_rows(
            lexical_rows,
            terms,
            semantic=False,
        )
        semantic_candidates = self._term_signal_rows(
            semantic_rows,
            terms,
            semantic=True,
        )
        fused = reciprocal_rank_fusion(lexical_candidates, semantic_candidates)

        lexical_forms = self._forms_by_term(lexical_rows)
        semantic_forms = self._forms_by_term(semantic_rows)
        items = []
        for candidate in fused:
            term = terms.get(str(candidate["candidate_id"]))
            if term is None or term.get("status") != "active":
                continue
            source_forms = lexical_forms.get(str(term["object_id"])) or semantic_forms.get(str(term["object_id"])) or []
            items.append(
                {
                    "kind": "term",
                    "object_id": term["object_id"],
                    "key": term["key"],
                    "definition": term["definition"],
                    "use_when": term.get("use_when", ""),
                    "avoid_when": term.get("avoid_when", ""),
                    "priority": int(term.get("priority", 0)),
                    "source_forms": [self.service._form_summary(form) for form in source_forms],
                    "target_forms": self.service._target_forms(term["forms"], target),
                    "linked_ids": sorted(str(edge["term"]) for edge in term.get("related_terms", []) if isinstance(edge, Mapping) and edge.get("term")),
                    "match_method": candidate["match_method"],
                    "score": candidate["score"],
                    "signals": candidate["signals"],
                }
            )
            if len(items) >= page_size:
                break
        return self._search_envelope(
            text,
            source,
            items,
            warnings,
            {
                "target_lang": target,
                "domain": scope,
                "limit": page_size,
                "kind": "terms",
            },
        )

    def search_rules(
        self,
        query: str,
        *,
        source_lang: str = "auto",
        target_lang: str | None = None,
        topic: str | None = None,
        style: str | None = None,
        limit: int = 10,
    ) -> dict[str, object]:
        """Return fused lexical, always-on, and semantic rule guidance."""
        text = self._query_text(query)
        source = canonicalize_language(source_lang, allow_auto=True)
        target = None if target_lang is None else canonicalize_language(target_lang)
        page_size = self._limit(limit)
        selected_topic = self._optional(topic)
        selected_style = self._optional(style)
        Rule = self.workspace.entities["glosswise-rule"]

        lexical_query = (
            self.workspace.query(Rule)
            .where(Rule.status == "active")
            .where((Rule.triggers.contained_in(text) & ((Rule.trigger_mode == "lexical") | (Rule.trigger_mode == "hybrid"))) | (Rule.trigger_mode == "always"))
        )
        lexical_query = self._rule_filters(
            lexical_query,
            Rule,
            source_lang=source,
            target_lang=target,
            topic=selected_topic,
            style=selected_style,
        )
        lexical_rows = sorted(
            lexical_query.execute().rows(),
            key=lambda row: (-int(row.get("priority", 0)), str(row["object_id"])),
        )
        lexical_candidates = [
            {
                "candidate_id": row["object_id"],
                "priority": int(row.get("priority", 0)),
            }
            for row in lexical_rows
        ]

        semantic_rows: list[dict[str, object]] = []
        warnings = []
        if self.service.embedding_available():
            vector = self.service._embed_text(text)
            semantic_query = (
                self.workspace.query(Rule)
                .where(Rule.status == "active")
                .where(Rule.embedding_space == self.service.embedding_policy()["embedding_space"])
                .where((Rule.trigger_mode == "semantic") | (Rule.trigger_mode == "hybrid"))
            )
            semantic_query = self._rule_filters(
                semantic_query,
                Rule,
                source_lang=source,
                target_lang=target,
                topic=selected_topic,
                style=selected_style,
            )
            semantic_rows = self._near_all(
                Rule,
                semantic_query,
                Rule.embedding,
                vector,
            )
        else:
            warnings.append(_NO_EMBEDDER_WARNING)
        semantic_candidates = [
            {
                "candidate_id": row["object_id"],
                "score": float(row.get("score", 0.0)),
            }
            for row in semantic_rows
        ]
        fused = reciprocal_rank_fusion(lexical_candidates, semantic_candidates)
        rows_by_id = {str(row["object_id"]): row for row in [*lexical_rows, *semantic_rows]}
        items = [self._rule_item(rows_by_id[str(candidate["candidate_id"])], candidate) for candidate in fused[:page_size]]
        return self._search_envelope(
            text,
            source,
            items,
            warnings,
            {
                "target_lang": target,
                "topic": selected_topic,
                "style": selected_style,
                "limit": page_size,
                "kind": "rules",
            },
        )

    def search_examples(
        self,
        query: str,
        *,
        source_lang: str | None = None,
        target_lang: str | None = None,
        topic: str | None = None,
        style: str | None = None,
        tag: str | None = None,
        limit: int = 10,
    ) -> dict[str, object]:
        """Return semantic example pairs with explicit scalar filters."""
        text = self._query_text(query)
        source = None if source_lang is None else canonicalize_language(source_lang)
        target = None if target_lang is None else canonicalize_language(target_lang)
        page_size = self._limit(limit)
        selected_topic = self._optional(topic)
        selected_style = self._optional(style)
        selected_tag = self._optional(tag)
        warnings = []
        rows: list[dict[str, object]] = []
        if self.service.embedding_available():
            Example = self.workspace.entities["glosswise-example"]
            vector = self.service._embed_text(text)
            semantic_query = (
                self.workspace.query(Example)
                .where(Example.status == "active")
                .where(Example.embedding_space == self.service.embedding_policy()["embedding_space"])
            )
            if source is not None:
                semantic_query = semantic_query.where(Example.source_lang == source)
            if target is not None:
                semantic_query = semantic_query.where(Example.target_lang == target)
            if selected_topic is not None:
                semantic_query = semantic_query.where(Example.topic == selected_topic)
            if selected_style is not None:
                semantic_query = semantic_query.where(Example.style == selected_style)
            if selected_tag is not None:
                semantic_query = semantic_query.where(Example.tags.array_contains(selected_tag))
            rows = self._near_all(
                Example,
                semantic_query,
                Example.embedding,
                vector,
            )[:page_size]
        else:
            warnings.append(_NO_EMBEDDER_WARNING)
        items = [
            {
                "kind": "example",
                "object_id": row["object_id"],
                "source_text": row["source_text"],
                "target_text": row["target_text"],
                "source_lang": row["source_lang"],
                "target_lang": row["target_lang"],
                "topic": row.get("topic", ""),
                "style": row.get("style", ""),
                "notes": row.get("notes", ""),
                "match_method": "semantic",
                "score": float(row.get("score", 0.0)),
                "signals": {
                    "lexical": None,
                    "semantic": {"score": float(row.get("score", 0.0))},
                },
            }
            for row in rows
        ]
        detected = source or "auto"
        return self._search_envelope(
            text,
            detected,
            items,
            warnings,
            {
                "target_lang": target,
                "topic": selected_topic,
                "style": selected_style,
                "tag": selected_tag,
                "limit": page_size,
                "kind": "examples",
            },
        )

    def prepare_translation(
        self,
        text: str,
        *,
        target_lang: str,
        source_lang: str = "auto",
        domain: str | None = None,
        topic: str | None = None,
        style: str | None = None,
        term_limit: int = 20,
        rule_limit: int = 20,
        example_limit: int = 10,
    ) -> dict[str, object]:
        """Assemble one bounded lexical and semantic translation brief."""
        if not isinstance(target_lang, str) or not target_lang.strip() or target_lang.strip().lower() == "auto":
            raise GlossWiseError(
                "target_language_required",
                "Translation preparation requires a concrete target language.",
            )
        target = canonicalize_language(target_lang)
        scan = self.service.scan_text(
            text,
            text_lang=source_lang,
            target_lang=target,
            include_rules=True,
            domain=domain,
            topic=topic,
            style=style,
            limit=max(self._limit(term_limit), self._limit(rule_limit)),
        )
        query = text[:MAX_QUERY_CHARS]
        terms = self.search_terms(
            query,
            query_lang=source_lang,
            target_lang=target,
            domain=domain,
            limit=term_limit,
        )
        rules = self.search_rules(
            query,
            source_lang=source_lang,
            target_lang=target,
            topic=topic,
            style=style,
            limit=rule_limit,
        )
        examples = self.search_examples(
            query,
            source_lang=None if source_lang == "auto" else source_lang,
            target_lang=target,
            topic=topic,
            style=style,
            limit=example_limit,
        )
        items = self._merge_brief_items(
            scan["items"],
            terms["items"],
            rules["items"],
            examples["items"],
        )
        warnings = list(
            dict.fromkeys(
                [
                    *scan["warnings"],
                    *terms["warnings"],
                    *rules["warnings"],
                    *examples["warnings"],
                ]
            )
        )
        return result_envelope(
            request={
                "kind": "translation_brief",
                "text_sha256": sha256(text.encode("utf-8")).hexdigest(),
                "text_chars": len(text),
                "source_lang": source_lang,
                "target_lang": target,
                "domain": self._optional(domain),
                "topic": self._optional(topic),
                "style": self._optional(style),
                "term_limit": self._limit(term_limit),
                "rule_limit": self._limit(rule_limit),
                "example_limit": self._limit(example_limit),
            },
            detected_language=scan["detected_language"],
            items=items,
            conflicts=scan["conflicts"],
            warnings=warnings,
            truncated=bool(scan["truncated"]),
            next_cursor=None,
        )

    def _near_all(
        self,
        entity: Any,
        filtered_query: Any,
        vector_field: Any,
        vector: Sequence[float],
    ) -> list[dict[str, object]]:
        policy = self.service.embedding_policy()
        all_space_rows = (
            self.workspace.query(entity)
            .where(entity.status == "active")
            .where(entity.embedding_space == policy["embedding_space"])
            .select("object_id")
            .execute()
            .ids
        )
        if not all_space_rows:
            return []
        rows = (
            filtered_query.near(
                vector_field,
                list(vector),
                top_k=len(all_space_rows),
            )
            .execute()
            .rows()
        )
        return [row for row in rows if float(row.get("score", 0.0)) >= _MIN_SEMANTIC_SCORE]

    @staticmethod
    def _term_filters(
        query: Any,
        TermForm: Any,
        *,
        source_lang: str,
        domain: str | None,
    ) -> Any:
        if source_lang != "auto":
            query = query.where(TermForm.lang == source_lang)
        if domain is not None:
            query = query.where(TermForm.domains.array_contains(domain))
        return query

    @staticmethod
    def _rule_filters(
        query: Any,
        Rule: Any,
        *,
        source_lang: str,
        target_lang: str | None,
        topic: str | None,
        style: str | None,
    ) -> Any:
        if source_lang != "auto":
            query = query.where(Rule.source_langs.array_contains("*") | Rule.source_langs.array_contains(source_lang))
        if target_lang is not None:
            query = query.where(Rule.target_langs.array_contains("*") | Rule.target_langs.array_contains(target_lang))
        if topic is not None:
            query = query.where(Rule.topics.array_contains(topic))
        if style is not None:
            query = query.where(Rule.styles.array_contains(style))
        return query

    def _term_signal_rows(
        self,
        rows: Sequence[Mapping[str, object]],
        terms: Mapping[str, Mapping[str, object]],
        *,
        semantic: bool,
    ) -> list[dict[str, object]]:
        best: dict[str, dict[str, object]] = {}
        for row in rows:
            term = terms.get(str(row["term_id"]))
            if term is None or term.get("status") != "active":
                continue
            candidate = {
                "candidate_id": row["term_id"],
                "priority": int(term.get("priority", 0)),
                "score": float(row.get("score", 0.0)),
            }
            current = best.get(str(row["term_id"]))
            if current is None or (semantic and float(candidate["score"]) > float(current["score"])):
                best[str(row["term_id"])] = candidate
        return sorted(
            best.values(),
            key=lambda item: (
                -float(item["score"]) if semantic else -int(item["priority"]),
                str(item["candidate_id"]),
            ),
        )

    @staticmethod
    def _forms_by_term(
        rows: Sequence[Mapping[str, object]],
    ) -> dict[str, list[Mapping[str, object]]]:
        output: dict[str, list[Mapping[str, object]]] = {}
        for row in rows:
            forms = output.setdefault(str(row["term_id"]), [])
            if all(item["object_id"] != row["object_id"] for item in forms):
                forms.append(row)
        return output

    @staticmethod
    def _rule_item(
        row: Mapping[str, object],
        candidate: Mapping[str, object],
    ) -> dict[str, object]:
        return {
            "kind": "rule",
            "object_id": row["object_id"],
            "title": row["title"],
            "instruction": row["instruction"],
            "trigger_mode": row["trigger_mode"],
            "priority": int(row.get("priority", 0)),
            "linked_ids": sorted(
                {
                    str(edge.get(endpoint))
                    for field, endpoint in (
                        ("related_rules", "rule"),
                        ("referenced_terms", "term"),
                    )
                    for edge in row.get(field, [])
                    if isinstance(edge, Mapping) and edge.get(endpoint)
                }
            ),
            "match_method": candidate["match_method"],
            "score": candidate["score"],
            "signals": candidate["signals"],
        }

    @staticmethod
    def _merge_brief_items(
        scan: Sequence[Mapping[str, object]],
        terms: Sequence[Mapping[str, object]],
        rules: Sequence[Mapping[str, object]],
        examples: Sequence[Mapping[str, object]],
    ) -> list[dict[str, object]]:
        output = [dict(item) for item in scan]
        seen = {(str(item.get("kind")), str(item.get("object_id"))) for item in output}
        for group in (terms, rules, examples):
            for item in group:
                key = (str(item.get("kind")), str(item.get("object_id")))
                if key in seen:
                    continue
                seen.add(key)
                output.append(dict(item))
        return output

    @staticmethod
    def _query_text(query: str) -> str:
        if not isinstance(query, str) or not query.strip():
            raise GlossWiseError("term_conflict", "Search query must not be blank.")
        text = query.strip()
        if len(text) > MAX_QUERY_CHARS:
            raise GlossWiseError(
                "input_too_large",
                f"Search query exceeds the {MAX_QUERY_CHARS}-character limit.",
            )
        return text

    @staticmethod
    def _limit(limit: int) -> int:
        try:
            value = int(limit)
        except (TypeError, ValueError) as error:
            raise GlossWiseError("term_conflict", "Search limit must be an integer.") from error
        if value < 1 or value > MAX_SEARCH_LIMIT:
            raise GlossWiseError(
                "term_conflict",
                f"Search limit must be between 1 and {MAX_SEARCH_LIMIT}.",
            )
        return value

    @staticmethod
    def _optional(value: str | None) -> str | None:
        if value is None:
            return None
        selected = str(value).strip()
        return selected or None

    @staticmethod
    def _search_envelope(
        text: str,
        source_lang: str,
        items: Sequence[Mapping[str, object]],
        warnings: Sequence[str],
        request: Mapping[str, object],
    ) -> dict[str, object]:
        detected = (
            {"tag": None, "confidence": 0.0, "method": "unavailable"} if source_lang == "auto" else {"tag": source_lang, "confidence": 1.0, "method": "caller"}
        )
        return result_envelope(
            request={
                "query_sha256": sha256(text.encode("utf-8")).hexdigest(),
                "query_chars": len(text),
                "query_lang": source_lang,
                **dict(request),
            },
            detected_language=detected,
            items=items,
            warnings=warnings,
        )
