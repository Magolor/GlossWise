"""Workspace-bound GlossWise application service."""

from __future__ import annotations

__all__ = ["GlossWiseService"]

import codecs
from collections.abc import Iterable, Mapping, Sequence
from copy import deepcopy
from hashlib import sha256
import os
from pathlib import Path
import stat
from typing import Any
import unicodedata

from .contracts import (
    DEFAULT_SCAN_LIMIT,
    MAX_FILE_BYTES,
    MAX_SCAN_LIMIT,
    MAX_TEXT_CHARS,
    decode_cursor,
    encode_cursor,
    request_fingerprint,
    scan_envelope,
)
from .config import GlossWiseConfig
from .documents import (
    DEFAULT_OCR_DPI,
    MAX_PDF_BYTES,
    DocumentStore,
    PdfProcessor,
)
from .documents.text import read_stream
from .entities import EMBEDDING_DIM
from .errors import GlossWiseError
from .language import (
    DEFAULT_LANGUAGES_CONFIG_KEY,
    canonicalize_language,
    canonicalize_language_ranges,
    canonicalize_languages,
)
from .retrieval import GlossWiseRetrieval

_STATUSES = frozenset({"draft", "active", "deprecated"})
_FORM_ROLES = frozenset({"preferred", "alias", "typo", "prohibited"})
_TRIGGER_MODES = frozenset({"always", "lexical", "semantic", "hybrid"})
_ENTITY_IDS = (
    "glosswise-term",
    "glosswise-term-form",
    "glosswise-rule",
    "glosswise-example",
)
_EMBEDDING_KEYS = (
    "provider",
    "model",
    "revision",
    "normalization",
    "embedding_space",
    "dimension",
)


class GlossWiseService:
    """Own GlossWise curation and retrieval policy for one workspace.

    Args:
        workspace (Any): HeavenBase workspace activating the external
            `glosswise` extension.
    """

    def __init__(self, workspace: Any) -> None:
        """Bind GlossWise domain policy to one workspace and Context.

        Args:
            workspace (Any): Owning HeavenBase workspace.

        Returns:
            None: This initializer stores workspace authority.
        """
        self.workspace = workspace
        self.context = workspace.context
        self._embedder: Any | None = None

    def configure_embedding(self, policy: Mapping[str, object]) -> dict[str, object]:
        """Persist the immutable embedding-space policy for this workspace.

        Args:
            policy (Mapping[str, object]): Provider, model, revision,
                normalization, embedding-space id, and fixed dimension.

        Returns:
            dict[str, object]: Canonical persisted policy.

        Raises:
            GlossWiseError: If fields are missing, dimension differs from the
                distribution schema, or a different policy is already stored.
        """
        missing = [key for key in _EMBEDDING_KEYS if key not in policy]
        if missing:
            raise GlossWiseError(
                "embedding_space_mismatch",
                f"Embedding policy is missing fields: {', '.join(missing)}.",
            )
        canonical = {key: policy[key] for key in _EMBEDDING_KEYS}
        try:
            canonical["dimension"] = int(canonical["dimension"])
        except (TypeError, ValueError) as error:
            raise GlossWiseError(
                "embedding_space_mismatch",
                "Embedding dimension must be an integer.",
            ) from error
        if canonical["dimension"] != EMBEDDING_DIM:
            raise GlossWiseError(
                "embedding_space_mismatch",
                f"Embedding dimension must be {EMBEDDING_DIM}.",
            )
        if not str(canonical["embedding_space"]).strip():
            raise GlossWiseError(
                "embedding_space_mismatch",
                "Embedding-space id must not be blank.",
            )
        manager = self.context.config
        with manager.scoped(self._workspace_scope()):
            stored = manager.get("glosswise.embedding", default=None)
            if stored is not None and dict(stored) != canonical:
                raise GlossWiseError(
                    "embedding_space_mismatch",
                    "A different embedding policy is already stored; re-embedding is required.",
                )
            manager.set("glosswise.embedding", canonical)
        return deepcopy(canonical)

    def embedding_policy(self) -> dict[str, object] | None:
        """Return the persisted workspace embedding policy.

        Args:
            None.

        Returns:
            dict[str, object] | None: Persisted policy, or `None` before setup.
        """
        manager = self.context.config
        with manager.scoped(self._workspace_scope()):
            value = manager.get("glosswise.embedding", default=None)
        return None if value is None else deepcopy(dict(value))

    def configure_embedder(self, embedder: Any | None) -> Any | None:
        """Attach one live embedder compatible with persisted policy.

        Args:
            embedder (Any | None): Object exposing `embedding_space`,
                `dimension`, and `embed(sequence)`, or `None` to disable
                semantic computation for this live workspace.

        Returns:
            Any | None: The attached adapter.

        Raises:
            GlossWiseError: If the adapter does not match workspace policy.
        """
        if embedder is None:
            self._embedder = None
            return None
        policy = self.embedding_policy()
        if policy is None:
            raise GlossWiseError(
                "embedding_space_mismatch",
                "Configure workspace embedding policy before attaching an embedder.",
            )
        try:
            dimension = int(embedder.dimension)
            embedding_space = str(embedder.embedding_space)
            embed = embedder.embed
        except (AttributeError, TypeError, ValueError) as error:
            raise GlossWiseError(
                "embedding_space_mismatch",
                "Embedder must expose dimension, embedding_space, and embed().",
            ) from error
        if not callable(embed) or dimension != int(policy["dimension"]) or embedding_space != policy["embedding_space"]:
            raise GlossWiseError(
                "embedding_space_mismatch",
                "Embedder identity does not match the persisted workspace policy.",
            )
        self._embedder = embedder
        return embedder

    def embedding_available(self) -> bool:
        """Return whether semantic computation is available in this process.

        Args:
            None.

        Returns:
            bool: Whether a compatible live adapter is attached.
        """
        return self._embedder is not None

    def configure_default_languages(
        self,
        languages: Sequence[str],
    ) -> list[str]:
        """Persist advisory default languages for this workspace.

        The annotation helps agents plan multilingual curation. It does not
        restrict valid language tags or make missing term forms an error.

        Args:
            languages (Sequence[str]): Ordered concrete BCP 47 tags. An empty
                sequence clears the annotation.

        Returns:
            list[str]: Canonical, deduplicated tags in input order.

        Raises:
            GlossWiseError: If the value is not a sequence of valid concrete
                BCP 47 tags.
        """
        canonical = canonicalize_languages(languages)
        manager = self.context.config
        with manager.scoped(self._workspace_scope()):
            manager.set(DEFAULT_LANGUAGES_CONFIG_KEY, canonical)
        return list(canonical)

    def default_languages(self) -> list[str]:
        """Return this workspace's advisory default language annotation.

        Args:
            None.

        Returns:
            list[str]: Canonical tags, or an empty list when unconfigured.
        """
        manager = self.context.config
        with manager.scoped(self._workspace_scope()):
            value = manager.get(DEFAULT_LANGUAGES_CONFIG_KEY, default=[])
        return canonicalize_languages(value or ())

    def term_language_advisory(
        self,
        term: Mapping[str, object],
    ) -> dict[str, object]:
        """Describe preferred-form coverage of workspace default languages.

        Args:
            term (Mapping[str, object]): Hydrated term containing a `forms`
                sequence.

        Returns:
            dict[str, object]: Non-enforcing coverage with configured,
                present, and missing default languages.
        """
        defaults = self.default_languages()
        forms = term.get("forms", ())
        present = {
            str(form.get("lang", "")) for form in forms if isinstance(form, Mapping) and form.get("role") == "preferred" and form.get("status") == "active"
        }
        covered = [language for language in defaults if language in present]
        missing = [language for language in defaults if language not in present]
        return {
            "default_languages": defaults,
            "present_languages": covered,
            "missing_languages": missing,
            "complete": not missing,
            "enforced": False,
        }

    def info(self) -> dict[str, object]:
        """Describe the active GlossWise workspace and safe capabilities.

        Args:
            None.

        Returns:
            dict[str, object]: Workspace identity, entity ids, available MCP
                profiles, and configured capability state. Filesystem roots
                and other machine-sensitive configuration are not returned.
        """
        return {
            "workspace": str(self.workspace.id),
            "entities": list(_ENTITY_IDS),
            "profiles": [
                "glosswise",
                "glosswise-local",
                "glosswise-curator",
            ],
            "default_languages": self.default_languages(),
            "user_config": GlossWiseConfig(self.context).describe(),
            "embedding": {
                "available": self.embedding_available(),
                "policy": self.embedding_policy(),
            },
            "file_access": {
                "configured": self.file_access_policy() is not None,
            },
        }

    def configure_file_access(
        self,
        allowed_roots: Sequence[str | os.PathLike[str]],
        *,
        max_bytes: int = MAX_FILE_BYTES,
        max_pdf_bytes: int = MAX_PDF_BYTES,
        encodings: Sequence[str] = ("utf-8",),
    ) -> dict[str, object]:
        """Persist explicit local-file authority for this workspace.

        Args:
            allowed_roots (Sequence[str | os.PathLike[str]]): Existing,
                non-symlink directories that local scans may read below.
            max_bytes (int): Maximum accepted file size.
            max_pdf_bytes (int): Maximum accepted PDF size.
            encodings (Sequence[str]): Explicit strict-decoding allowlist.

        Returns:
            dict[str, object]: Canonical persisted file policy.

        Raises:
            GlossWiseError: If a root, size, or encoding is invalid.
        """
        if isinstance(allowed_roots, (str, bytes, os.PathLike)):
            raise GlossWiseError(
                "file_access_denied",
                "Allowed file roots must be a list of directories.",
            )
        roots: list[str] = []
        for raw in allowed_roots:
            candidate = Path(raw).expanduser()
            if candidate.is_symlink():
                raise GlossWiseError(
                    "file_access_denied",
                    "Allowed file roots must not be symlinks.",
                )
            try:
                resolved = candidate.resolve(strict=True)
            except OSError as error:
                raise GlossWiseError(
                    "file_access_denied",
                    "An allowed file root does not exist.",
                ) from error
            if not resolved.is_dir():
                raise GlossWiseError(
                    "file_access_denied",
                    "Every allowed file root must be a directory.",
                )
            if str(resolved) not in roots:
                roots.append(str(resolved))
        if not roots:
            raise GlossWiseError(
                "file_access_denied",
                "At least one allowed file root is required.",
            )
        try:
            size = int(max_bytes)
        except (TypeError, ValueError) as error:
            raise GlossWiseError(
                "input_too_large",
                "File byte limit must be an integer.",
            ) from error
        if size < 1 or size > MAX_FILE_BYTES:
            raise GlossWiseError(
                "input_too_large",
                f"File byte limit must be between 1 and {MAX_FILE_BYTES}.",
            )
        try:
            pdf_size = int(max_pdf_bytes)
        except (TypeError, ValueError) as error:
            raise GlossWiseError(
                "input_too_large",
                "PDF byte limit must be an integer.",
            ) from error
        if pdf_size < 1 or pdf_size > MAX_PDF_BYTES:
            raise GlossWiseError(
                "input_too_large",
                f"PDF byte limit must be between 1 and {MAX_PDF_BYTES}.",
            )
        if isinstance(encodings, (str, bytes)) or not isinstance(encodings, Sequence):
            raise GlossWiseError(
                "decode_failed",
                "Allowed encodings must be a list.",
            )
        canonical_encodings: list[str] = []
        for raw in encodings:
            try:
                encoding = codecs.lookup(str(raw)).name
            except LookupError as error:
                raise GlossWiseError(
                    "decode_failed",
                    "An allowed file encoding is unknown.",
                ) from error
            if encoding not in canonical_encodings:
                canonical_encodings.append(encoding)
        if not canonical_encodings:
            raise GlossWiseError(
                "decode_failed",
                "At least one file encoding is required.",
            )
        policy: dict[str, object] = {
            "allowed_roots": roots,
            "max_bytes": size,
            "max_pdf_bytes": pdf_size,
            "encodings": canonical_encodings,
        }
        manager = self.context.config
        with manager.scoped(self._workspace_scope()):
            manager.set("glosswise.files", policy)
        return deepcopy(policy)

    def file_access_policy(self) -> dict[str, object] | None:
        """Return the workspace's persisted local-file authority.

        Args:
            None.

        Returns:
            dict[str, object] | None: Canonical policy, or `None` when local
                file access has not been authorized.
        """
        manager = self.context.config
        with manager.scoped(self._workspace_scope()):
            value = manager.get("glosswise.files", default=None)
        return None if value is None else deepcopy(dict(value))

    def scan_text(
        self,
        text: str,
        *,
        text_lang: str = "auto",
        target_lang: str | None = None,
        include_rules: bool = True,
        domain: str | None = None,
        topic: str | None = None,
        style: str | None = None,
        limit: int = DEFAULT_SCAN_LIMIT,
        cursor: str | None = None,
    ) -> dict[str, object]:
        """Find bounded lexical term and rule occurrences in transient text.

        Args:
            text (str): Source text, never persisted by this method.
            text_lang (str): Concrete BCP 47 tag or request-only `auto`.
            target_lang (str | None): Optional concrete target language used to
                select target forms and applicable rules.
            include_rules (bool): Whether lexical and always-on rules join the
                term findings.
            domain (str | None): Optional exact term-domain filter.
            topic (str | None): Optional exact rule-topic filter.
            style (str | None): Optional exact rule-style filter.
            limit (int): Page size from 1 through `MAX_SCAN_LIMIT`.
            cursor (str | None): Opaque cursor from a matching prior request.

        Returns:
            dict[str, object]: Versioned bounded scan envelope.

        Raises:
            GlossWiseError: If input, language, limit, or cursor is invalid.
        """
        if not isinstance(text, str):
            raise GlossWiseError("term_conflict", "Scan text must be a string.")
        if len(text) > MAX_TEXT_CHARS:
            raise GlossWiseError(
                "input_too_large",
                f"Scan text exceeds the {MAX_TEXT_CHARS}-character limit.",
            )
        source = canonicalize_language(text_lang, allow_auto=True)
        target = None if target_lang is None else canonicalize_language(target_lang)
        page_size = self._scan_limit(limit)
        request = {
            "text_sha256": sha256(text.encode("utf-8")).hexdigest(),
            "text_chars": len(text),
            "text_lang": source,
            "target_lang": target,
            "include_rules": bool(include_rules),
            "domain": self._optional_filter(domain),
            "topic": self._optional_filter(topic),
            "style": self._optional_filter(style),
            "limit": page_size,
        }
        fingerprint = request_fingerprint(request)
        offset = decode_cursor(cursor, fingerprint)
        findings = self._scan_term_findings(
            text,
            source_lang=source,
            target_lang=target,
            domain=request["domain"],
        )
        if include_rules:
            findings.extend(
                self._scan_rule_findings(
                    text,
                    source_lang=source,
                    target_lang=target,
                    topic=request["topic"],
                    style=request["style"],
                )
            )
        conflicts = self._term_conflicts(findings)
        findings.sort(key=lambda item: self._finding_sort_key(item, len(text)))
        if offset > len(findings):
            raise GlossWiseError(
                "invalid_cursor",
                "Scan cursor points beyond the available findings.",
            )
        page = findings[offset : offset + page_size]
        page_ids = {str(item["id"]) for item in page}
        page_conflicts = [conflict for conflict in conflicts if page_ids.intersection(conflict["finding_ids"])]
        next_offset = offset + len(page)
        truncated = next_offset < len(findings)
        warnings = []
        if source == "auto":
            warnings.append("No language detector is configured; lexical scanning included all stored source languages.")
        detected = {"tag": None, "confidence": 0.0, "method": "unavailable"} if source == "auto" else {"tag": source, "confidence": 1.0, "method": "caller"}
        return scan_envelope(
            request=request,
            detected_language=detected,
            items=page,
            conflicts=page_conflicts,
            warnings=warnings,
            truncated=truncated,
            next_cursor=encode_cursor(next_offset, fingerprint) if truncated else None,
        )

    def scan_file(
        self,
        path: str | os.PathLike[str],
        *,
        encoding: str = "utf-8",
        text_lang: str = "auto",
        target_lang: str | None = None,
        include_rules: bool = True,
        domain: str | None = None,
        topic: str | None = None,
        style: str | None = None,
        start_line: int | None = None,
        end_line: int | None = None,
        limit: int = DEFAULT_SCAN_LIMIT,
        cursor: str | None = None,
    ) -> dict[str, object]:
        """Read one authorized local text file strictly and scan its content.

        Args:
            path (str | os.PathLike[str]): Server-local file path.
            encoding (str): Strict decoder from the configured allowlist.
            text_lang (str): Concrete BCP 47 tag or request-only `auto`.
            target_lang (str | None): Optional concrete target language.
            include_rules (bool): Whether rule findings are included.
            domain (str | None): Optional term-domain filter.
            topic (str | None): Optional rule-topic filter.
            style (str | None): Optional rule-style filter.
            start_line (int | None): One-based first source line.
            end_line (int | None): Inclusive last source line.
            limit (int): Page size.
            cursor (str | None): Opaque cursor from the same file content and
                filters.

        Returns:
            dict[str, object]: Scan envelope plus redacted file metadata.

        Raises:
            GlossWiseError: If authority, file type, size, encoding, decoding,
                or delegated text policy fails.
        """
        text, file_meta = self._read_authorized_text(
            path,
            encoding=encoding,
            start_line=start_line,
            end_line=end_line,
        )
        result = self.scan_text(
            text,
            text_lang=text_lang,
            target_lang=target_lang,
            include_rules=include_rules,
            domain=domain,
            topic=topic,
            style=style,
            limit=limit,
            cursor=cursor,
        )
        result["request"]["file"] = file_meta
        return result

    def prepare_file(
        self,
        path: str | os.PathLike[str],
        *,
        target_lang: str,
        encoding: str = "utf-8",
        source_lang: str = "auto",
        domain: str | None = None,
        topic: str | None = None,
        style: str | None = None,
        start_line: int | None = None,
        end_line: int | None = None,
        term_limit: int = 20,
        rule_limit: int = 20,
        example_limit: int = 10,
    ) -> dict[str, object]:
        """Prepare a translation brief from an authorized file line range.

        Args:
            path (str | os.PathLike[str]): Server-local authorized text file.
            target_lang (str): Concrete target BCP 47 tag.
            encoding (str): Strict decoder from the configured allowlist.
            source_lang (str): Concrete source language or `auto`.
            domain (str | None): Optional terminology domain.
            topic (str | None): Optional rule/example topic.
            style (str | None): Optional translation style.
            start_line (int | None): One-based first source line.
            end_line (int | None): Inclusive last source line.
            term_limit (int): Maximum terminology candidates.
            rule_limit (int): Maximum rules.
            example_limit (int): Maximum examples.

        Returns:
            dict[str, object]: Translation brief with redacted file metadata.

        Raises:
            GlossWiseError: If file authority, decoding, range, or brief input
                is invalid.
        """
        text, file_meta = self._read_authorized_text(
            path,
            encoding=encoding,
            start_line=start_line,
            end_line=end_line,
        )
        result = self.prepare_translation(
            text,
            target_lang=target_lang,
            source_lang=source_lang,
            domain=domain,
            topic=topic,
            style=style,
            term_limit=term_limit,
            rule_limit=rule_limit,
            example_limit=example_limit,
        )
        result["request"]["file"] = file_meta
        return result

    def ocr_pdf(
        self,
        path: str | os.PathLike[str],
        *,
        preset: str | None = None,
        start_page: int | None = None,
        end_page: int | None = None,
        dpi: int = DEFAULT_OCR_DPI,
    ) -> dict[str, object]:
        """OCR authorized PDF pages into short-handle temporary text.

        Args:
            path (str | os.PathLike[str]): Server-local authorized PDF.
            preset (str | None): HeavenBase LLM preset override. Omit it to
                use global GlossWise OCR configuration.
            start_page (int | None): One-based first page.
            end_page (int | None): Inclusive last page.
            dpi (int): Render resolution from 72 through 600.

        Returns:
            dict[str, object]: Short handle and redacted page metadata.

        Raises:
            GlossWiseError: If file authority, rendering, range, or OCR fails.
        """
        policy = self._file_policy()
        resolved, _ = self._authorized_file(
            path,
            max_bytes=int(policy.get("max_pdf_bytes", MAX_PDF_BYTES)),
            partial=False,
        )
        config = GlossWiseConfig(self.context)
        return PdfProcessor(
            self.context,
            workspace=self.workspace,
            store=self._document_store(),
        ).ocr(
            resolved,
            preset=str(preset or config.ocr_preset()),
            start_page=start_page,
            end_page=end_page,
            dpi=dpi,
        )

    def list_documents(self) -> list[dict[str, object]]:
        """List temporary OCR document handles for this workspace.

        Args:
            None.

        Returns:
            list[dict[str, object]]: Redacted manifests newest first.
        """
        return self._document_store().list()

    def get_document(self, handle: str) -> dict[str, object]:
        """Describe one temporary OCR document.

        Args:
            handle (str): Short `gw-...` handle.

        Returns:
            dict[str, object]: Redacted document manifest.
        """
        return self._document_store().describe(handle)

    def read_document(
        self,
        handle: str,
        page: int,
        *,
        start_line: int | None = None,
        end_line: int | None = None,
    ) -> dict[str, object]:
        """Read a bounded line range from one OCR page.

        Args:
            handle (str): Short `gw-...` handle.
            page (int): One-based source PDF page.
            start_line (int | None): One-based first OCR text line.
            end_line (int | None): Inclusive last OCR text line.

        Returns:
            dict[str, object]: Page text and selection metadata.
        """
        return self._document_store().read_page(
            handle,
            page,
            start_line=start_line,
            end_line=end_line,
        )

    def remove_document(self, handle: str) -> dict[str, object]:
        """Remove one temporary OCR document.

        Args:
            handle (str): Short `gw-...` handle.

        Returns:
            dict[str, object]: Removal result.
        """
        return self._document_store().remove(handle)

    def search_terms(
        self,
        query: str,
        *,
        query_lang: str = "auto",
        target_lang: str | None = None,
        domain: str | None = None,
        limit: int = 10,
    ) -> dict[str, object]:
        """Return fused lexical and semantic terminology candidates.

        Args:
            query (str): Bounded natural-language query.
            query_lang (str): Concrete BCP 47 tag or `auto`.
            target_lang (str | None): Optional target-form language.
            domain (str | None): Optional exact domain filter.
            limit (int): Maximum returned concepts.

        Returns:
            dict[str, object]: Versioned bounded search envelope.
        """
        return GlossWiseRetrieval(self).search_terms(
            query,
            query_lang=query_lang,
            target_lang=target_lang,
            domain=domain,
            limit=limit,
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
        """Return fused lexical, always-on, and semantic rules.

        Args:
            query (str): Bounded natural-language query.
            source_lang (str): Concrete BCP 47 tag or `auto`.
            target_lang (str | None): Optional concrete target language.
            topic (str | None): Optional exact topic.
            style (str | None): Optional exact style.
            limit (int): Maximum returned rules.

        Returns:
            dict[str, object]: Versioned bounded search envelope.
        """
        return GlossWiseRetrieval(self).search_rules(
            query,
            source_lang=source_lang,
            target_lang=target_lang,
            topic=topic,
            style=style,
            limit=limit,
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
        """Return filtered semantic example pairs.

        Args:
            query (str): Bounded natural-language query.
            source_lang (str | None): Optional concrete source language.
            target_lang (str | None): Optional concrete target language.
            topic (str | None): Optional exact topic.
            style (str | None): Optional exact style.
            tag (str | None): Optional exact tag.
            limit (int): Maximum returned examples.

        Returns:
            dict[str, object]: Versioned bounded search envelope.
        """
        return GlossWiseRetrieval(self).search_examples(
            query,
            source_lang=source_lang,
            target_lang=target_lang,
            topic=topic,
            style=style,
            tag=tag,
            limit=limit,
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
        """Build one bounded terminology, rule, and example brief.

        Args:
            text (str): Source passage.
            target_lang (str): Required concrete target language.
            source_lang (str): Concrete BCP 47 tag or `auto`.
            domain (str | None): Optional term domain.
            topic (str | None): Optional rule/example topic.
            style (str | None): Optional rule/example style.
            term_limit (int): Maximum term candidates.
            rule_limit (int): Maximum rule candidates.
            example_limit (int): Maximum examples.

        Returns:
            dict[str, object]: Versioned bounded translation brief.
        """
        return GlossWiseRetrieval(self).prepare_translation(
            text,
            target_lang=target_lang,
            source_lang=source_lang,
            domain=domain,
            topic=topic,
            style=style,
            term_limit=term_limit,
            rule_limit=rule_limit,
            example_limit=example_limit,
        )

    def to_mcp(
        self,
        *,
        name: str | None = None,
        profile: str = "glosswise",
        description: str | None = None,
        tools: list[str] | None = None,
    ) -> Any:
        """Build a Toolkit through one GlossWise-owned profile.

        Args:
            name (str | None): Optional runtime Toolkit name.
            profile (str): Supported values:
                - `glosswise`: Read-only text, retrieval, and Skill tools.
                - `glosswise-local`: Read-only tools plus authorized
                  server-local file scanning.
                - `glosswise-curator`: Read-only tools plus domain-specific
                  term, rule, and example curation.
            description (str | None): Optional Toolkit description.
            tools (list[str] | None): Optional subset of profile tools.

        Returns:
            Any: HeavenBase runtime Toolkit bound to this workspace.

        Raises:
            ValueError: If the profile is not owned by GlossWise.
        """
        from .lifecycle import _setup_workspace_agent

        _setup_workspace_agent(self.workspace)
        profile_id = str(profile or "glosswise")
        allowed = (
            "glosswise",
            "glosswise-local",
            "glosswise-curator",
        )
        if profile_id not in allowed:
            expected = ", ".join(repr(item) for item in allowed)
            raise ValueError(f"GlossWise MCP profile must be one of {expected}; got {profile_id!r}.")
        return self.workspace.to_mcp(
            name=name,
            description=description,
            profile=profile_id,
            tools=tools,
        )

    def put_term(
        self,
        term: Mapping[str, object],
        forms: Sequence[Mapping[str, object]],
    ) -> dict[str, object]:
        """Create or update one concept and its supplied term forms.

        Args:
            term (Mapping[str, object]): Term row with explicit `object_id`.
            forms (Sequence[Mapping[str, object]]): Forms belonging to the term.
                Every form needs its own explicit `object_id`.

        Returns:
            dict[str, object]: Hydrated term with all stored forms.

        Raises:
            GlossWiseError: If identity, status, key, form role, language,
                parent, or active-term invariants fail.
        """
        term_row = dict(term)
        term_id = self._require_id(term_row, "term")
        term_row["status"] = self._choice(term_row.get("status", "draft"), _STATUSES, "term status")
        term_key = self._nonempty(term_row.pop("key", None), "term key")
        term_row.pop("term_key", None)
        term_row["term_key"] = term_key
        term_row["domains"] = self._string_list(term_row.get("domains", []), "term domain")
        term_row["tags"] = self._string_list(term_row.get("tags", []), "term tag")
        self._require_unique_term_key(term_key, term_id)

        Term = self.workspace.entities["glosswise-term"]
        TermForm = self.workspace.entities["glosswise-term-form"]
        previous_term = self.workspace.get(term_id, entity=Term)
        previous_forms = {row["object_id"]: row for row in self.workspace.query(TermForm).where(TermForm.term_id == term_id).execute().rows()}
        supplied_forms = [self._prepare_form(form, term_id, term_row) for form in forms]
        supplied_ids = {str(form["object_id"]) for form in supplied_forms}
        retained_forms = [self._prepare_form(form, term_id, term_row) for object_id, form in previous_forms.items() if str(object_id) not in supplied_ids]
        effective_forms = [*retained_forms, *supplied_forms]
        self._require_unique_forms(effective_forms)
        if term_row["status"] == "active" and not any(form["role"] == "preferred" and form["status"] == "active" for form in effective_forms):
            raise GlossWiseError(
                "term_conflict",
                "An active term requires at least one active preferred form.",
                object_ids=(term_id,),
            )

        graph = list(
            term_row.pop(
                "related_terms",
                previous_term.get("related_terms", []) if previous_term else [],
            )
        )
        self._validate_links(
            {"related_terms": graph},
            (("related_terms", "term", "glosswise-term"),),
            pending={("glosswise-term", term_id)},
        )
        try:
            self.workspace.upsert(Term, {**term_row, "related_terms": []})
            for form in effective_forms:
                self.workspace.upsert(TermForm, form)
            self.workspace.set(
                {"object_id": term_id, "related_terms": graph},
                entity=Term,
            )
        except Exception:
            self._restore_rows(
                TermForm,
                previous_forms,
                [str(form["object_id"]) for form in effective_forms],
            )
            self._restore_row(Term, term_id, previous_term)
            raise
        result = self.get_term(term_id)
        if result is None:
            raise GlossWiseError("internal_error", "Stored term could not be reloaded.")
        return result

    def put_rule(self, rule: Mapping[str, object]) -> dict[str, object]:
        """Create or replace one validated translation rule.

        Args:
            rule (Mapping[str, object]): Rule row with explicit `object_id`.

        Returns:
            dict[str, object]: Hydrated stored rule.

        Raises:
            GlossWiseError: If status, trigger mode, language, or activation
                invariants fail.
        """
        row = dict(rule)
        object_id = self._require_id(row, "rule")
        row["status"] = self._choice(row.get("status", "draft"), _STATUSES, "rule status")
        row["trigger_mode"] = self._choice(
            row.get("trigger_mode", "always"),
            _TRIGGER_MODES,
            "rule trigger mode",
        )
        row["source_langs"] = canonicalize_language_ranges(row.get("source_langs", ["*"]))
        row["target_langs"] = canonicalize_language_ranges(row.get("target_langs", ["*"]))
        row["triggers"] = self._string_list(row.get("triggers", []), "rule trigger")
        row["topics"] = self._string_list(row.get("topics", []), "rule topic")
        row["styles"] = self._string_list(row.get("styles", []), "rule style")
        row["tags"] = self._string_list(row.get("tags", []), "rule tag")
        if row["trigger_mode"] == "lexical" and not row["triggers"]:
            raise GlossWiseError(
                "term_conflict",
                "A lexical rule requires at least one trigger.",
                object_ids=(object_id,),
            )
        row["search_text"] = "\n".join(
            filter(
                None,
                [
                    str(row.get("title", "")),
                    str(row.get("instruction", "")),
                    *row["triggers"],
                ],
            )
        )
        self._apply_embedding_space(row)
        self._validate_links(
            row,
            (
                ("related_rules", "rule", "glosswise-rule"),
                ("referenced_terms", "term", "glosswise-term"),
            ),
            pending={("glosswise-rule", object_id)},
        )
        Rule = self.workspace.entities["glosswise-rule"]
        self.workspace.upsert(Rule, row)
        stored = self.workspace.get(object_id, entity=Rule)
        if stored is None:
            raise GlossWiseError("internal_error", "Stored rule could not be reloaded.")
        return stored

    def put_example(self, example: Mapping[str, object]) -> dict[str, object]:
        """Create or replace one validated translation example.

        Args:
            example (Mapping[str, object]): Example row with explicit
                `object_id`, source language, and target language.

        Returns:
            dict[str, object]: Hydrated stored example.

        Raises:
            GlossWiseError: If status or language values are invalid.
        """
        row = dict(example)
        object_id = self._require_id(row, "example")
        row["status"] = self._choice(row.get("status", "draft"), _STATUSES, "example status")
        row["source_lang"] = canonicalize_language(str(row.get("source_lang", "")))
        row["target_lang"] = canonicalize_language(str(row.get("target_lang", "")))
        row["tags"] = self._string_list(row.get("tags", []), "example tag")
        row["search_text"] = "\n".join(
            filter(
                None,
                [
                    str(row.get("source_text", "")),
                    str(row.get("target_text", "")),
                    str(row.get("notes", "")),
                ],
            )
        )
        self._apply_embedding_space(row)
        self._validate_links(
            row,
            (
                ("referenced_terms", "term", "glosswise-term"),
                ("referenced_rules", "rule", "glosswise-rule"),
            ),
        )
        Example = self.workspace.entities["glosswise-example"]
        self.workspace.upsert(Example, row)
        stored = self.workspace.get(object_id, entity=Example)
        if stored is None:
            raise GlossWiseError("internal_error", "Stored example could not be reloaded.")
        return stored

    def get_term(self, term_id: str) -> dict[str, object] | None:
        """Return one term with all stored forms.

        Args:
            term_id (str): Term `object_id`.

        Returns:
            dict[str, object] | None: Term plus a `forms` list, or `None` when
            the term is absent.
        """
        Term = self.workspace.entities["glosswise-term"]
        term = self.workspace.get(str(term_id), entity=Term)
        if term is None:
            return None
        return self._hydrate_terms([term])[str(term_id)]

    def list_terms(
        self,
        *,
        status: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, object]]:
        """List terminology concepts in deterministic identity order.

        Args:
            status (str | None): Optional `draft`, `active`, or `deprecated`
                filter.
            limit (int): Maximum rows from 1 through 200.

        Returns:
            list[dict[str, object]]: Public term payloads including forms.

        Raises:
            GlossWiseError: If `status` or `limit` is invalid.
        """
        Term = self.workspace.entities["glosswise-term"]
        query = self.workspace.query(Term)
        if status is not None:
            selected = self._choice(status, _STATUSES, "term status")
            query = query.where(Term.status == selected)
        rows = query.order_by(Term.object_id).limit(self._record_limit(limit)).execute().rows()
        hydrated = self._hydrate_terms(rows)
        return [hydrated[str(row["object_id"])] for row in rows]

    def get_rule(self, rule_id: str) -> dict[str, object] | None:
        """Return one translation rule by identity.

        Args:
            rule_id (str): Rule `object_id`.

        Returns:
            dict[str, object] | None: Stored rule, or `None` when absent.
        """
        return self.workspace.get(
            str(rule_id),
            entity="glosswise-rule",
        )

    def list_rules(
        self,
        *,
        status: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, object]]:
        """List translation rules in deterministic identity order.

        Args:
            status (str | None): Optional `draft`, `active`, or `deprecated`
                filter.
            limit (int): Maximum rows from 1 through 200.

        Returns:
            list[dict[str, object]]: Stored rule payloads.

        Raises:
            GlossWiseError: If `status` or `limit` is invalid.
        """
        return self._list_records(
            "glosswise-rule",
            status=status,
            limit=limit,
        )

    def get_example(self, example_id: str) -> dict[str, object] | None:
        """Return one translation example by identity.

        Args:
            example_id (str): Example `object_id`.

        Returns:
            dict[str, object] | None: Stored example, or `None` when absent.
        """
        return self.workspace.get(
            str(example_id),
            entity="glosswise-example",
        )

    def list_examples(
        self,
        *,
        status: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, object]]:
        """List translation examples in deterministic identity order.

        Args:
            status (str | None): Optional `draft`, `active`, or `deprecated`
                filter.
            limit (int): Maximum rows from 1 through 200.

        Returns:
            list[dict[str, object]]: Stored example payloads.

        Raises:
            GlossWiseError: If `status` or `limit` is invalid.
        """
        return self._list_records(
            "glosswise-example",
            status=status,
            limit=limit,
        )

    def archive(self, object_id: str) -> dict[str, object]:
        """Mark one unambiguous GlossWise row as deprecated.

        Args:
            object_id (str): Row identity unique across GlossWise entities.

        Returns:
            dict[str, object]: Hydrated archived row.

        Raises:
            GlossWiseError: If no row or more than one entity matches the id.
        """
        matches = [(entity_id, self.workspace.get(object_id, entity=entity_id)) for entity_id in _ENTITY_IDS]
        found = [(entity_id, row) for entity_id, row in matches if row is not None]
        if len(found) != 1:
            raise GlossWiseError(
                "term_conflict",
                f"Archive requires one matching GlossWise row; found {len(found)}.",
                object_ids=(object_id,),
            )
        entity_id, _ = found[0]
        self.workspace.set(
            {"object_id": object_id, "status": "deprecated"},
            entity=entity_id,
        )
        if entity_id == "glosswise-term":
            term = self.get_term(object_id)
            if term is None:
                raise GlossWiseError("internal_error", "Archived term could not be reloaded.")
            return term
        stored = self.workspace.get(object_id, entity=entity_id)
        if stored is None:
            raise GlossWiseError("internal_error", "Archived row could not be reloaded.")
        return stored

    def _scan_term_findings(
        self,
        text: str,
        *,
        source_lang: str,
        target_lang: str | None,
        domain: object,
    ) -> list[dict[str, object]]:
        TermForm = self.workspace.entities["glosswise-term-form"]
        query = self.workspace.query(TermForm).where(TermForm.triggers.contained_in(text)).where(TermForm.status == "active")
        if source_lang != "auto":
            query = query.where(TermForm.lang == source_lang)
        if domain is not None:
            query = query.where(TermForm.domains.array_contains(domain))
        forms = query.execute().rows()
        terms = self._terms_by_id(str(form["term_id"]) for form in forms)
        findings: list[dict[str, object]] = []
        for form in forms:
            term = terms.get(str(form["term_id"]))
            if term is None or term.get("status") != "active":
                continue
            target_forms = self._target_forms(term["forms"], target_lang)
            linked_ids = sorted({str(edge["term"]) for edge in term.get("related_terms", []) if isinstance(edge, Mapping) and edge.get("term")})
            for occurrence, match in enumerate(form.get("match", [])):
                raw_span = match.get("query_span")
                findings.append(
                    {
                        "id": self._finding_id(
                            "term",
                            str(term["object_id"]),
                            str(form["object_id"]),
                            raw_span,
                            occurrence,
                        ),
                        "kind": "term",
                        "object_id": term["object_id"],
                        "matched_text": match.get("query_text", ""),
                        "raw_span": raw_span,
                        "normalized_span": match.get("query_norm_span"),
                        "match_method": "substring",
                        "match_precision": self._match_precision(
                            str(match.get("keyword", "")),
                            str(match.get("query_text", "")),
                        ),
                        "score": None,
                        "priority": int(term.get("priority", 0)),
                        "source_forms": [self._form_summary(form)],
                        "target_forms": target_forms,
                        "definition_or_instruction": term.get("definition", ""),
                        "use_when": term.get("use_when", ""),
                        "avoid_when": term.get("avoid_when", ""),
                        "linked_ids": linked_ids,
                        "conflict_ids": [],
                    }
                )
        merged: dict[tuple[object, ...], dict[str, object]] = {}
        for finding in findings:
            key = (
                finding["object_id"],
                tuple(finding["raw_span"] or []),
                tuple(finding["normalized_span"] or []),
                finding["matched_text"],
            )
            existing = merged.get(key)
            if existing is None:
                span = finding["raw_span"]
                start = span[0] if isinstance(span, list) and len(span) == 2 else "none"
                end = span[1] if isinstance(span, list) and len(span) == 2 else "none"
                finding["id"] = f"term:{finding['object_id']}:{start}:{end}"
                merged[key] = finding
                continue
            known = {str(form["object_id"]) for form in existing["source_forms"]}
            existing["source_forms"].extend(form for form in finding["source_forms"] if str(form["object_id"]) not in known)
            existing["source_forms"].sort(
                key=lambda form: (
                    str(form["lang"]),
                    str(form["role"]),
                    str(form["object_id"]),
                )
            )
        return list(merged.values())

    def _scan_rule_findings(
        self,
        text: str,
        *,
        source_lang: str,
        target_lang: str | None,
        topic: object,
        style: object,
    ) -> list[dict[str, object]]:
        Rule = self.workspace.entities["glosswise-rule"]
        trigger_query = (
            self.workspace.query(Rule)
            .where(Rule.triggers.contained_in(text))
            .where(Rule.status == "active")
            .where((Rule.trigger_mode == "lexical") | (Rule.trigger_mode == "hybrid"))
        )
        trigger_query = self._scope_rule_query(
            trigger_query,
            Rule,
            source_lang=source_lang,
            target_lang=target_lang,
            topic=topic,
            style=style,
        )
        findings: list[dict[str, object]] = []
        for rule in trigger_query.execute().rows():
            for occurrence, match in enumerate(rule.get("match", [])):
                raw_span = match.get("query_span")
                findings.append(
                    self._rule_finding(
                        rule,
                        finding_id=self._finding_id(
                            "rule",
                            str(rule["object_id"]),
                            str(rule["object_id"]),
                            raw_span,
                            occurrence,
                        ),
                        matched_text=str(match.get("query_text", "")),
                        raw_span=raw_span,
                        normalized_span=match.get("query_norm_span"),
                        method="substring",
                        precision=self._match_precision(
                            str(match.get("keyword", "")),
                            str(match.get("query_text", "")),
                        ),
                    )
                )

        always_query = self.workspace.query(Rule).where(Rule.status == "active").where(Rule.trigger_mode == "always")
        always_query = self._scope_rule_query(
            always_query,
            Rule,
            source_lang=source_lang,
            target_lang=target_lang,
            topic=topic,
            style=style,
        )
        for rule in always_query.execute().rows():
            findings.append(
                self._rule_finding(
                    rule,
                    finding_id=f"rule:{rule['object_id']}:always",
                    matched_text="",
                    raw_span=None,
                    normalized_span=None,
                    method="always",
                    precision=None,
                )
            )
        return findings

    def _list_records(
        self,
        entity_id: str,
        *,
        status: str | None,
        limit: int,
    ) -> list[dict[str, object]]:
        Entity = self.workspace.entities[entity_id]
        query = self.workspace.query(Entity)
        if status is not None:
            selected = self._choice(status, _STATUSES, "record status")
            query = query.where(Entity.status == selected)
        return query.order_by(Entity.object_id).limit(self._record_limit(limit)).execute().rows()

    def _terms_by_id(
        self,
        term_ids: Iterable[str],
    ) -> dict[str, dict[str, object]]:
        ids = list(dict.fromkeys(str(term_id) for term_id in term_ids))
        if not ids:
            return {}
        Term = self.workspace.entities["glosswise-term"]
        rows = self.workspace.query(Term).where(Term.object_id.in_(ids)).execute().rows()
        return self._hydrate_terms(rows)

    def _hydrate_terms(
        self,
        rows: Sequence[Mapping[str, object]],
    ) -> dict[str, dict[str, object]]:
        term_ids = [str(row["object_id"]) for row in rows]
        if not term_ids:
            return {}
        TermForm = self.workspace.entities["glosswise-term-form"]
        forms = self.workspace.query(TermForm).where(TermForm.term_id.in_(term_ids)).order_by(TermForm.object_id).execute().rows()
        forms_by_term: dict[str, list[dict[str, object]]] = {}
        for form in forms:
            forms_by_term.setdefault(str(form["term_id"]), []).append(form)
        return {
            str(row["object_id"]): {
                **{key: value for key, value in row.items() if key != "term_key"},
                "key": row["term_key"],
                "forms": forms_by_term.get(str(row["object_id"]), []),
            }
            for row in rows
        }

    @staticmethod
    def _scope_rule_query(
        query: Any,
        Rule: Any,
        *,
        source_lang: str,
        target_lang: str | None,
        topic: object,
        style: object,
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

    @staticmethod
    def _form_summary(form: Mapping[str, object]) -> dict[str, object]:
        return {
            "object_id": form["object_id"],
            "lang": form["lang"],
            "role": form["role"],
            "text": form["text"],
            "usage_note": form.get("usage_note", ""),
            "status": form.get("status", "active"),
        }

    def _target_forms(
        self,
        forms: Sequence[Mapping[str, object]],
        target_lang: str | None,
    ) -> list[dict[str, object]]:
        if target_lang is None:
            return []
        active = [form for form in forms if form.get("status") == "active"]
        exact = [form for form in active if form.get("lang") == target_lang]
        selected = exact
        language_match = "exact"
        if not selected and "-" in target_lang:
            base = target_lang.split("-", 1)[0]
            selected = [form for form in active if form.get("lang") == base]
            language_match = "base_fallback"
        output = []
        for form in selected:
            summary = self._form_summary(form)
            summary["language_match"] = language_match
            output.append(summary)
        return sorted(
            output,
            key=lambda item: (
                {"preferred": 0, "prohibited": 1, "alias": 2, "typo": 3}.get(
                    str(item["role"]),
                    4,
                ),
                str(item["object_id"]),
            ),
        )

    @staticmethod
    def _rule_finding(
        rule: Mapping[str, object],
        *,
        finding_id: str,
        matched_text: str,
        raw_span: object,
        normalized_span: object,
        method: str,
        precision: str | None,
    ) -> dict[str, object]:
        linked_ids = sorted(
            {
                str(edge.get(endpoint))
                for field, endpoint in (
                    ("related_rules", "rule"),
                    ("referenced_terms", "term"),
                )
                for edge in rule.get(field, [])
                if isinstance(edge, Mapping) and edge.get(endpoint)
            }
        )
        return {
            "id": finding_id,
            "kind": "rule",
            "object_id": rule["object_id"],
            "matched_text": matched_text,
            "raw_span": raw_span,
            "normalized_span": normalized_span,
            "match_method": method,
            "match_precision": precision,
            "score": None,
            "priority": int(rule.get("priority", 0)),
            "source_forms": [],
            "target_forms": [],
            "definition_or_instruction": rule.get("instruction", ""),
            "use_when": "",
            "avoid_when": "",
            "linked_ids": linked_ids,
            "conflict_ids": [],
        }

    @staticmethod
    def _term_conflicts(
        findings: Sequence[dict[str, object]],
    ) -> list[dict[str, object]]:
        """Surface equal-priority target-form contradictions without guessing."""
        groups: dict[tuple[object, ...], list[dict[str, object]]] = {}
        for finding in findings:
            if finding.get("kind") != "term":
                continue
            span = finding.get("raw_span")
            if not isinstance(span, list) or len(span) != 2:
                continue
            preferred = [form for form in finding.get("target_forms", []) if isinstance(form, Mapping) and form.get("role") == "preferred"]
            if not preferred:
                continue
            key = (span[0], span[1], int(finding.get("priority", 0)))
            groups.setdefault(key, []).append(finding)

        conflicts = []
        for (start, end, priority), members in sorted(groups.items()):
            preferred_forms = {
                str(form["text"]).casefold(): dict(form)
                for member in members
                for form in member["target_forms"]
                if isinstance(form, Mapping) and form.get("role") == "preferred"
            }
            if len(preferred_forms) < 2:
                continue
            finding_ids = sorted(str(member["id"]) for member in members)
            object_ids = sorted({str(member["object_id"]) for member in members})
            digest = sha256("\0".join([str(start), str(end), str(priority), *finding_ids]).encode("utf-8")).hexdigest()[:16]
            conflict_id = f"term-target:{digest}"
            for member in members:
                member["conflict_ids"].append(conflict_id)
            conflicts.append(
                {
                    "id": conflict_id,
                    "kind": "term_target_form",
                    "reason": ("Equal-priority term findings prescribe multiple preferred target forms for the same source span."),
                    "priority": priority,
                    "raw_span": [start, end],
                    "finding_ids": finding_ids,
                    "object_ids": object_ids,
                    "target_forms": sorted(
                        preferred_forms.values(),
                        key=lambda form: (
                            str(form.get("lang", "")),
                            str(form.get("text", "")).casefold(),
                            str(form.get("object_id", "")),
                        ),
                    ),
                }
            )
        return conflicts

    @staticmethod
    def _finding_id(
        kind: str,
        object_id: str,
        source_id: str,
        raw_span: object,
        occurrence: int,
    ) -> str:
        span = raw_span if isinstance(raw_span, list) else []
        start = span[0] if len(span) == 2 else "none"
        end = span[1] if len(span) == 2 else "none"
        return f"{kind}:{object_id}:{source_id}:{start}:{end}:{occurrence}"

    @staticmethod
    def _match_precision(keyword: str, matched: str) -> str:
        if matched == keyword:
            return "literal"
        if matched.casefold() == keyword.casefold():
            return "casefolded"
        return "normalized"

    @staticmethod
    def _finding_sort_key(
        finding: Mapping[str, object],
        text_length: int,
    ) -> tuple[object, ...]:
        span = finding.get("raw_span")
        start = span[0] if isinstance(span, list) and len(span) == 2 else text_length + 1
        end = span[1] if isinstance(span, list) and len(span) == 2 else text_length + 1
        return (
            start,
            -int(finding.get("priority", 0)),
            end,
            0 if finding.get("kind") == "term" else 1,
            str(finding.get("id", "")),
        )

    @staticmethod
    def _scan_limit(limit: int) -> int:
        try:
            value = int(limit)
        except (TypeError, ValueError) as error:
            raise GlossWiseError(
                "term_conflict",
                "Scan limit must be an integer.",
            ) from error
        if value < 1 or value > MAX_SCAN_LIMIT:
            raise GlossWiseError(
                "term_conflict",
                f"Scan limit must be between 1 and {MAX_SCAN_LIMIT}.",
            )
        return value

    @staticmethod
    def _record_limit(limit: int) -> int:
        try:
            value = int(limit)
        except (TypeError, ValueError) as error:
            raise GlossWiseError(
                "term_conflict",
                "Record limit must be an integer.",
            ) from error
        if value < 1 or value > MAX_SCAN_LIMIT:
            raise GlossWiseError(
                "term_conflict",
                f"Record limit must be between 1 and {MAX_SCAN_LIMIT}.",
            )
        return value

    @staticmethod
    def _optional_filter(value: str | None) -> str | None:
        if value is None:
            return None
        selected = str(value).strip()
        return selected or None

    def _workspace_scope(self) -> str:
        return f"{self.context.config.base_scope}.{self.workspace.id}"

    def _file_policy(self) -> dict[str, object]:
        policy = self.file_access_policy()
        if policy is None:
            raise GlossWiseError(
                "file_access_denied",
                "Local file access has not been authorized for this workspace.",
            )
        return policy

    def _read_authorized_text(
        self,
        path: str | os.PathLike[str],
        *,
        encoding: str,
        start_line: int | None,
        end_line: int | None,
    ) -> tuple[str, dict[str, object]]:
        policy = self._file_policy()
        try:
            canonical_encoding = codecs.lookup(str(encoding)).name
        except LookupError as error:
            raise GlossWiseError(
                "decode_failed",
                "The requested file encoding is unknown.",
            ) from error
        if canonical_encoding not in policy["encodings"]:
            raise GlossWiseError(
                "decode_failed",
                "The requested file encoding is not authorized.",
            )
        partial = start_line is not None or end_line is not None
        resolved, descriptor, source_bytes = self._open_authorized_file(
            path,
            max_bytes=int(policy["max_bytes"]),
            partial=partial,
        )
        try:
            with os.fdopen(
                descriptor,
                "r",
                encoding=canonical_encoding,
                errors="strict",
                newline="",
                closefd=False,
            ) as handle:
                selection = read_stream(
                    handle,
                    encoding=canonical_encoding,
                    start_line=start_line,
                    end_line=end_line,
                    max_bytes=int(policy["max_bytes"]),
                    max_chars=MAX_TEXT_CHARS,
                )
        finally:
            os.close(descriptor)
        return selection.text, {
            "name": resolved.name,
            "source_bytes": source_bytes,
            "encoding": canonical_encoding,
            "sha256": sha256(selection.text.encode("utf-8")).hexdigest(),
            "selection": selection.to_dict(),
        }

    def _authorized_file(
        self,
        path: str | os.PathLike[str],
        *,
        max_bytes: int,
        partial: bool,
    ) -> tuple[Path, int]:
        resolved, descriptor, source_bytes = self._open_authorized_file(
            path,
            max_bytes=max_bytes,
            partial=partial,
        )
        os.close(descriptor)
        return resolved, source_bytes

    def _open_authorized_file(
        self,
        path: str | os.PathLike[str],
        *,
        max_bytes: int,
        partial: bool,
    ) -> tuple[Path, int, int]:
        policy = self._file_policy()
        try:
            candidate = Path(path).expanduser()
        except TypeError as error:
            raise GlossWiseError(
                "file_access_denied",
                "File path must be a filesystem path.",
            ) from error
        if ".." in candidate.parts:
            raise GlossWiseError(
                "file_access_denied",
                "Traversal segments are not allowed in file paths.",
            )
        if candidate.is_symlink():
            raise GlossWiseError(
                "file_access_denied",
                "Symlink files are not allowed.",
            )
        try:
            resolved = candidate.resolve(strict=True)
        except OSError as error:
            raise GlossWiseError(
                "file_access_denied",
                "The requested file does not exist.",
            ) from error
        roots = [Path(value) for value in policy["allowed_roots"]]
        if not any(resolved != root and root in resolved.parents for root in roots):
            raise GlossWiseError(
                "file_access_denied",
                "The requested file is outside the authorized roots.",
            )
        if not resolved.is_file():
            raise GlossWiseError(
                "file_access_denied",
                "The requested path is not a regular file.",
            )
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
        try:
            descriptor = os.open(resolved, flags)
        except OSError as error:
            raise GlossWiseError(
                "file_access_denied",
                "The requested file could not be opened safely.",
            ) from error
        try:
            details = os.fstat(descriptor)
            if not stat.S_ISREG(details.st_mode):
                raise GlossWiseError(
                    "file_access_denied",
                    "The requested path is not a regular file.",
                )
            if not partial and details.st_size > max_bytes:
                raise GlossWiseError(
                    "input_too_large",
                    f"File exceeds the configured {max_bytes}-byte limit.",
                )
        except Exception:
            os.close(descriptor)
            raise
        return resolved, descriptor, int(details.st_size)

    def _document_store(self) -> DocumentStore:
        context_root = Path(self.context.config.root).expanduser().resolve()
        context_id = sha256(str(context_root).encode("utf-8")).hexdigest()[:12]
        root = Path("~/.glosswise/documents").expanduser() / context_id / str(self.workspace.id)
        return DocumentStore(root)

    def _prepare_form(
        self,
        form: Mapping[str, object],
        term_id: str,
        term: Mapping[str, object],
    ) -> dict[str, object]:
        row = dict(form)
        self._require_id(row, "term form")
        supplied_parent = str(row.get("term_id", term_id))
        if supplied_parent != term_id:
            raise GlossWiseError(
                "term_conflict",
                "Every supplied form must belong to the term being written.",
                object_ids=(term_id, supplied_parent),
            )
        row["term_id"] = term_id
        row["lang"] = canonicalize_language(str(row.get("lang", "")))
        row["role"] = self._choice(row.get("role", ""), _FORM_ROLES, "term-form role")
        row["status"] = self._choice(row.get("status", "active"), _STATUSES, "term-form status")
        row["text"] = self._nonempty(row.get("text"), "term-form text")
        row["normalized_text"] = self._normalize_text(row["text"])
        row["triggers"] = [row["text"]]
        row["domains"] = list(term.get("domains", []))
        row["search_text"] = "\n".join(
            filter(
                None,
                [
                    row["text"],
                    str(term.get("definition") or ""),
                    str(term.get("use_when") or ""),
                    str(term.get("avoid_when") or ""),
                    str(row.get("usage_note") or ""),
                ],
            )
        )
        self._apply_embedding_space(row)
        return row

    def _apply_embedding_space(self, row: dict[str, object]) -> None:
        policy = self.embedding_policy()
        vector = self._embed_text(str(row.get("search_text", ""))) if self._embedder is not None else row.get("embedding")
        if vector is not None:
            if isinstance(vector, (str, bytes)) or not isinstance(vector, Sequence):
                raise GlossWiseError(
                    "embedding_space_mismatch",
                    "Embedding must be a numeric sequence.",
                )
            values = list(vector)
            if policy is None or len(values) != EMBEDDING_DIM:
                raise GlossWiseError(
                    "embedding_space_mismatch",
                    f"Embedding vectors must use the configured {EMBEDDING_DIM}-dimension space.",
                )
            row["embedding"] = values
            row["embedding_space"] = policy["embedding_space"]
        else:
            row.pop("embedding", None)
            row["embedding_space"] = ""

    def _embed_text(self, text: str) -> list[float]:
        if self._embedder is None:
            raise GlossWiseError(
                "embedding_unavailable",
                "No compatible embedder is attached to this workspace.",
            )
        try:
            vectors = self._embedder.embed([str(text)])
            vector = list(vectors[0])
        except GlossWiseError:
            raise
        except Exception as error:
            raise GlossWiseError(
                "embedding_unavailable",
                "The configured embedding provider could not complete the request.",
            ) from error
        if len(vector) != EMBEDDING_DIM:
            raise GlossWiseError(
                "embedding_space_mismatch",
                f"Embedding vectors must use the configured {EMBEDDING_DIM}-dimension space.",
            )
        try:
            return [float(value) for value in vector]
        except (TypeError, ValueError) as error:
            raise GlossWiseError(
                "embedding_space_mismatch",
                "The embedding provider returned a non-numeric vector.",
            ) from error

    def _require_unique_term_key(self, key: object, object_id: str) -> None:
        Term = self.workspace.entities["glosswise-term"]
        rows = self.workspace.query(Term).where(Term.term_key == key).execute().rows()
        conflicts = [row["object_id"] for row in rows if row["object_id"] != object_id]
        if conflicts:
            raise GlossWiseError(
                "term_conflict",
                f"Term key {key!r} is already in use.",
                object_ids=(object_id, *conflicts),
            )

    def _require_unique_forms(self, forms: Sequence[Mapping[str, object]]) -> None:
        TermForm = self.workspace.entities["glosswise-term-form"]
        seen: dict[tuple[object, ...], str] = {}
        for form in forms:
            key = (
                form["term_id"],
                form["lang"],
                form["role"],
                form["normalized_text"],
            )
            object_id = str(form["object_id"])
            if key in seen and seen[key] != object_id:
                raise GlossWiseError(
                    "term_conflict",
                    "Duplicate normalized term forms were supplied.",
                    object_ids=(seen[key], object_id),
                )
            seen[key] = object_id
            rows = (
                self.workspace.query(TermForm)
                .where(TermForm.term_id == form["term_id"])
                .where(TermForm.lang == form["lang"])
                .where(TermForm.role == form["role"])
                .where(TermForm.normalized_text == form["normalized_text"])
                .execute()
                .rows()
            )
            conflicts = [row["object_id"] for row in rows if row["object_id"] != object_id]
            if conflicts:
                raise GlossWiseError(
                    "term_conflict",
                    "An equivalent normalized term form already exists.",
                    object_ids=(object_id, *conflicts),
                )

    def _validate_links(
        self,
        row: Mapping[str, object],
        specifications: Sequence[tuple[str, str, str]],
        *,
        pending: set[tuple[str, str]] | None = None,
    ) -> None:
        pending = pending or set()
        for field, endpoint, entity_id in specifications:
            edges = row.get(field, [])
            if isinstance(edges, (str, bytes)) or not isinstance(edges, Sequence):
                raise GlossWiseError(
                    "term_conflict",
                    f"{field} must be a list of relationship objects.",
                )
            for edge in edges:
                if not isinstance(edge, Mapping):
                    raise GlossWiseError(
                        "term_conflict",
                        f"{field} must contain relationship objects.",
                    )
                target_id = str(edge.get(endpoint, "")).strip()
                if not target_id:
                    raise GlossWiseError(
                        "term_conflict",
                        f"{field} relationship target must not be blank.",
                    )
                if (entity_id, target_id) not in pending and self.workspace.get(target_id, entity=entity_id) is None:
                    raise GlossWiseError(
                        "term_conflict",
                        f"{field} relationship target does not exist.",
                        object_ids=(target_id,),
                    )

    def _restore_rows(
        self,
        entity: Any,
        previous: Mapping[str, Mapping[str, object]],
        touched: Sequence[str],
    ) -> None:
        for object_id in reversed(tuple(touched)):
            self._restore_row(entity, object_id, previous.get(object_id))

    def _restore_row(
        self,
        entity: Any,
        object_id: str,
        previous: Mapping[str, object] | None,
    ) -> None:
        if previous is None:
            if self.workspace.get(object_id, entity=entity) is not None:
                self.workspace.delete((entity.identifier, object_id), edges="schema")
            return
        self.workspace.upsert(entity, dict(previous))

    @staticmethod
    def _require_id(row: Mapping[str, object], label: str) -> str:
        value = str(row.get("object_id", "")).strip()
        if not value:
            raise GlossWiseError(
                "term_conflict",
                f"{label.capitalize()} requires an explicit object_id.",
            )
        return value

    @staticmethod
    def _choice(value: object, choices: frozenset[str], label: str) -> str:
        selected = str(value).strip().lower()
        if selected not in choices:
            expected = ", ".join(sorted(choices))
            raise GlossWiseError(
                "term_conflict",
                f"Invalid {label} {value!r}; expected one of: {expected}.",
            )
        return selected

    @staticmethod
    def _nonempty(value: object, label: str) -> str:
        selected = str(value or "").strip()
        if not selected:
            raise GlossWiseError("term_conflict", f"{label.capitalize()} must not be blank.")
        return selected

    @classmethod
    def _string_list(cls, value: object, label: str) -> list[str]:
        if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
            raise GlossWiseError(
                "term_conflict",
                f"{label.capitalize()} values must be a list.",
            )
        return list(dict.fromkeys(cls._nonempty(item, label) for item in value))

    @staticmethod
    def _normalize_text(text: str) -> str:
        out: list[str] = []
        last_space = False
        for char in text:
            for normalized in unicodedata.normalize("NFKC", char).casefold():
                category = unicodedata.category(normalized)
                if normalized.isspace() or category.startswith("P"):
                    if out and not last_space:
                        out.append(" ")
                    last_space = True
                elif not category.startswith("C"):
                    out.append(normalized)
                    last_space = False
        return "".join(out).rstrip()
