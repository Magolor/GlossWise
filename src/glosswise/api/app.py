"""Owning application object for persistent GlossWise workspaces."""

from __future__ import annotations

__all__ = ["GlossWiseApp"]

from collections.abc import Mapping, Sequence
from pathlib import Path
from types import TracebackType
from typing import Any

import heavenbase as hb

from ..contracts import MAX_FILE_BYTES
from ..documents import DEFAULT_OCR_DPI, MAX_PDF_BYTES
from .workspaces import (
    DEFAULT_WORKSPACE_ID,
    GlossWiseWorkspaces,
)
from .translation import TranslationService


class GlossWiseApp:
    """Own one GlossWise workspace and its machine Context.

    Use `open` for the managed active/default workflow, `create` for explicit
    workspace provisioning, or `load` when absence must fail. Closing the app
    retires its Context and all live workspace resources.
    """

    def __init__(self, context: hb.Context, workspace: hb.HeavenBase) -> None:
        """Bind an already prepared workspace to its owning Context.

        Args:
            context (hb.Context): Machine Context owned by this app.
            workspace (hb.HeavenBase): Prepared GlossWise workspace.

        Returns:
            None: This initializer stores lifecycle authority.
        """
        self.context = context
        self.workspace = workspace
        self.service = workspace.glosswise
        self._closed = False

    @classmethod
    def create(
        cls,
        workspace_id: str = DEFAULT_WORKSPACE_ID,
        *,
        database: str | Path | None = None,
        activate: bool = True,
        bootstrap: str | Path | None = None,
    ) -> "GlossWiseApp":
        """Create or compatibly reopen a persistent SQLite workspace.

        Args:
            workspace_id (str): Stable HeavenBase workspace identity.
            database (str | Path | None): Advanced SQLite database override.
                Omit it to use `~/.glosswise/<workspace_id>.db`.
            activate (bool): Whether this becomes the active workspace.
            bootstrap (str | Path | None): Optional HeavenBase bootstrap YAML.
                Omit it to use `~/.heavenbase/bootstrap.yaml`.

        Returns:
            GlossWiseApp: Open application with curation and retrieval methods.

        Raises:
            FileExistsError: If the workspace id is already registered with a
                conflicting construction contract.
            GlossWiseError: If global languages have not been configured for
                a new managed workspace.
            ValueError: If the workspace or database path is invalid.
        """
        return cls._open(
            workspace_id,
            bootstrap=bootstrap,
            ensure_default=False,
            create=True,
            database=database,
            activate=activate,
        )

    @classmethod
    def load(
        cls,
        workspace_id: str | None = None,
        *,
        bootstrap: str | Path | None = None,
    ) -> "GlossWiseApp":
        """Load an existing explicit, active, or managed-default workspace.

        Args:
            workspace_id (str | None): Existing workspace id. Omit it to use
                the active GlossWise workspace, then the managed default.
            bootstrap (str | Path | None): Optional HeavenBase bootstrap YAML.
                Omit it to use `~/.heavenbase/bootstrap.yaml`.

        Returns:
            GlossWiseApp: Open application with curation and retrieval methods.

        Raises:
            KeyError: If no registered workspace matches `workspace_id`.
        """
        return cls._open(
            workspace_id,
            bootstrap=bootstrap,
            ensure_default=False,
            create=False,
            database=None,
            activate=False,
        )

    @classmethod
    def open(
        cls,
        workspace_id: str | None = None,
        *,
        bootstrap: str | Path | None = None,
    ) -> "GlossWiseApp":
        """Open the active/default workspace, creating the default on demand.

        Args:
            workspace_id (str | None): Explicit workspace id. Omit it to use
                the active GlossWise workspace, then managed `default`.
            bootstrap (str | Path | None): Optional HeavenBase bootstrap YAML.

        Returns:
            GlossWiseApp: Open application facade.

        Raises:
            GlossWiseError: If the managed default does not exist and global
                languages have not been configured.
        """
        return cls._open(
            workspace_id,
            bootstrap=bootstrap,
            ensure_default=True,
            create=False,
            database=None,
            activate=False,
        )

    @classmethod
    def _open(
        cls,
        workspace_id: str | None,
        *,
        bootstrap: str | Path | None,
        ensure_default: bool,
        create: bool,
        database: str | Path | None,
        activate: bool,
    ) -> "GlossWiseApp":
        context = hb.Context.load(
            home_path=None if bootstrap is None else str(bootstrap),
        )
        try:
            directory = GlossWiseWorkspaces(
                context,
                bootstrap=bootstrap,
            )
            if create:
                directory.create(
                    workspace_id or DEFAULT_WORKSPACE_ID,
                    database=database,
                    activate=activate,
                )
            workspace = directory.open(
                workspace_id,
                ensure_default=ensure_default,
            )
            return cls(context, workspace)
        except Exception:
            context.close()
            raise

    def info(self) -> dict[str, object]:
        """Describe the active workspace and safe capabilities.

        Args:
            None.

        Returns:
            dict[str, object]: Redacted workspace capability summary.
        """
        return self.service.info()

    def configure_default_languages(
        self,
        languages: Sequence[str],
    ) -> list[str]:
        """Persist advisory default languages for this workspace.

        Args:
            languages (Sequence[str]): Ordered concrete BCP 47 tags. An empty
                sequence clears the annotation.

        Returns:
            list[str]: Canonical, deduplicated language tags.
        """
        return self.service.configure_default_languages(languages)

    def default_languages(self) -> list[str]:
        """Return this workspace's advisory default languages.

        Args:
            None.

        Returns:
            list[str]: Canonical language tags, or an empty list.
        """
        return self.service.default_languages()

    def term_language_advisory(
        self,
        term: Mapping[str, object],
    ) -> dict[str, object]:
        """Describe non-enforcing default-language coverage for one term.

        Args:
            term (Mapping[str, object]): Hydrated term with stored forms.

        Returns:
            dict[str, object]: Present and missing default languages.
        """
        return self.service.term_language_advisory(term)

    def configure_file_access(
        self,
        allowed_roots: Sequence[str | Path],
        *,
        max_bytes: int = MAX_FILE_BYTES,
        max_pdf_bytes: int = MAX_PDF_BYTES,
        encodings: Sequence[str] = ("utf-8",),
    ) -> dict[str, object]:
        """Authorize server-local text and PDF roots for this workspace.

        Args:
            allowed_roots (Sequence[str | Path]): Existing non-symlink
                directories.
            max_bytes (int): Maximum selected text bytes.
            max_pdf_bytes (int): Maximum PDF source bytes.
            encodings (Sequence[str]): Strict text-decoding allowlist.

        Returns:
            dict[str, object]: Canonical persisted file-access policy.
        """
        return self.service.configure_file_access(
            allowed_roots,
            max_bytes=max_bytes,
            max_pdf_bytes=max_pdf_bytes,
            encodings=encodings,
        )

    def put_term(
        self,
        term: Mapping[str, object],
        forms: Sequence[Mapping[str, object]],
    ) -> dict[str, object]:
        """Create or update one term and supplied language forms.

        Args:
            term (Mapping[str, object]): Public term payload with `object_id`
                and `key`.
            forms (Sequence[Mapping[str, object]]): Language-specific forms.

        Returns:
            dict[str, object]: Hydrated public term and all stored forms.
        """
        return self.service.put_term(term, forms)

    def get_term(self, object_id: str) -> dict[str, object] | None:
        """Return one term by identity.

        Args:
            object_id (str): Term `object_id`.

        Returns:
            dict[str, object] | None: Public term payload, or `None`.
        """
        return self.service.get_term(object_id)

    def list_terms(
        self,
        *,
        status: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, object]]:
        """List terms in deterministic order.

        Args:
            status (str | None): Optional status filter.
            limit (int): Maximum rows from 1 through 200.

        Returns:
            list[dict[str, object]]: Public terms with forms.
        """
        return self.service.list_terms(status=status, limit=limit)

    def put_rule(self, rule: Mapping[str, object]) -> dict[str, object]:
        """Create or update one translation rule.

        Args:
            rule (Mapping[str, object]): Rule payload with explicit
                `object_id`.

        Returns:
            dict[str, object]: Hydrated stored rule.
        """
        return self.service.put_rule(rule)

    def get_rule(self, object_id: str) -> dict[str, object] | None:
        """Return one rule by identity.

        Args:
            object_id (str): Rule `object_id`.

        Returns:
            dict[str, object] | None: Stored rule, or `None`.
        """
        return self.service.get_rule(object_id)

    def list_rules(
        self,
        *,
        status: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, object]]:
        """List rules in deterministic order.

        Args:
            status (str | None): Optional status filter.
            limit (int): Maximum rows from 1 through 200.

        Returns:
            list[dict[str, object]]: Stored rules.
        """
        return self.service.list_rules(status=status, limit=limit)

    def put_example(
        self,
        example: Mapping[str, object],
    ) -> dict[str, object]:
        """Create or update one approved translation example.

        Args:
            example (Mapping[str, object]): Example payload with explicit
                `object_id`.

        Returns:
            dict[str, object]: Hydrated stored example.
        """
        return self.service.put_example(example)

    def get_example(self, object_id: str) -> dict[str, object] | None:
        """Return one example by identity.

        Args:
            object_id (str): Example `object_id`.

        Returns:
            dict[str, object] | None: Stored example, or `None`.
        """
        return self.service.get_example(object_id)

    def list_examples(
        self,
        *,
        status: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, object]]:
        """List examples in deterministic order.

        Args:
            status (str | None): Optional status filter.
            limit (int): Maximum rows from 1 through 200.

        Returns:
            list[dict[str, object]]: Stored examples.
        """
        return self.service.list_examples(status=status, limit=limit)

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
        limit: int = 50,
        cursor: str | None = None,
    ) -> dict[str, object]:
        """Find literal/normalized term and rule occurrences in source text.

        Args:
            text (str): Source passage to scan without persistence.
            text_lang (str): Concrete BCP 47 source language or `auto`.
            target_lang (str | None): Optional target-form language.
            include_rules (bool): Whether applicable rules are included.
            domain (str | None): Optional exact terminology domain.
            topic (str | None): Optional exact rule topic.
            style (str | None): Optional exact rule style.
            limit (int): Maximum findings on this page.
            cursor (str | None): Opaque cursor from a matching prior scan.

        Returns:
            dict[str, object]: Versioned scan envelope.
        """
        return self.service.scan_text(
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

    def scan_file(
        self,
        path: str | Path,
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
        limit: int = 50,
        cursor: str | None = None,
    ) -> dict[str, object]:
        """Scan an authorized local text-file line range.

        Args:
            path (str | Path): Server-local authorized text file.
            encoding (str): Strict configured decoder.
            text_lang (str): Concrete BCP 47 source language or `auto`.
            target_lang (str | None): Optional target-form language.
            include_rules (bool): Whether applicable rules are included.
            domain (str | None): Optional exact terminology domain.
            topic (str | None): Optional exact rule topic.
            style (str | None): Optional exact rule style.
            start_line (int | None): One-based first source line.
            end_line (int | None): Inclusive last source line.
            limit (int): Maximum findings on this page.
            cursor (str | None): Opaque cursor from a matching prior scan.

        Returns:
            dict[str, object]: Versioned scan envelope with range metadata.
        """
        return self.service.scan_file(
            path,
            encoding=encoding,
            text_lang=text_lang,
            target_lang=target_lang,
            include_rules=include_rules,
            domain=domain,
            topic=topic,
            style=style,
            start_line=start_line,
            end_line=end_line,
            limit=limit,
            cursor=cursor,
        )

    def search_terms(
        self,
        query: str,
        *,
        query_lang: str = "auto",
        target_lang: str | None = None,
        domain: str | None = None,
        limit: int = 10,
    ) -> dict[str, object]:
        """Search curated terminology for focused candidate discovery.

        Args:
            query (str): Natural-language terminology query.
            query_lang (str): Query language or `auto`.
            target_lang (str | None): Optional target-form language.
            domain (str | None): Optional exact domain.
            limit (int): Maximum returned concepts.

        Returns:
            dict[str, object]: Versioned lexical/semantic search envelope.
        """
        return self.service.search_terms(
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
        """Search curated translation rules for focused guidance.

        Args:
            query (str): Natural-language rule query.
            source_lang (str): Source language or `auto`.
            target_lang (str | None): Optional target language.
            topic (str | None): Optional exact topic.
            style (str | None): Optional exact style.
            limit (int): Maximum returned rules.

        Returns:
            dict[str, object]: Versioned lexical/semantic search envelope.
        """
        return self.service.search_rules(
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
        """Search curated translation examples for comparable evidence.

        Args:
            query (str): Natural-language example query.
            source_lang (str | None): Optional source language.
            target_lang (str | None): Optional target language.
            topic (str | None): Optional exact topic.
            style (str | None): Optional exact style.
            tag (str | None): Optional exact tag.
            limit (int): Maximum returned examples.

        Returns:
            dict[str, object]: Versioned semantic search envelope.
        """
        return self.service.search_examples(
            query,
            source_lang=source_lang,
            target_lang=target_lang,
            topic=topic,
            style=style,
            tag=tag,
            limit=limit,
        )

    def archive(self, object_id: str) -> dict[str, object]:
        """Soft-delete one unambiguous term, form, rule, or example.

        Args:
            object_id (str): GlossWise object identity.

        Returns:
            dict[str, object]: Archived row with `status="deprecated"`.
        """
        return self.service.archive(object_id)

    def prepare_translation(
        self,
        text: str,
        *,
        target_lang: str,
        source_lang: str = "auto",
        domain: str | None = None,
        topic: str | None = None,
        style: str | None = None,
    ) -> dict[str, object]:
        """Prepare terminology and policy context for a translation model.

        GlossWise does not invoke or conceal a translation model. The caller
        remains responsible for generation and must inspect conflicts first.

        Args:
            text (str): Source passage.
            target_lang (str): Concrete target BCP 47 language.
            source_lang (str): Concrete source language or `auto`.
            domain (str | None): Optional terminology domain.
            topic (str | None): Optional rule/example topic.
            style (str | None): Optional rule/example style.

        Returns:
            dict[str, object]: Versioned translation brief.
        """
        return self.service.prepare_translation(
            text,
            target_lang=target_lang,
            source_lang=source_lang,
            domain=domain,
            topic=topic,
            style=style,
        )

    def prepare_file(
        self,
        path: str | Path,
        *,
        target_lang: str,
        encoding: str = "utf-8",
        source_lang: str = "auto",
        domain: str | None = None,
        topic: str | None = None,
        style: str | None = None,
        start_line: int | None = None,
        end_line: int | None = None,
    ) -> dict[str, object]:
        """Prepare a translation brief from an authorized file line range.

        Args:
            path (str | Path): Server-local authorized text file.
            target_lang (str): Concrete target BCP 47 language.
            encoding (str): Strict configured decoder.
            source_lang (str): Concrete source language or `auto`.
            domain (str | None): Optional terminology domain.
            topic (str | None): Optional rule/example topic.
            style (str | None): Optional translation style.
            start_line (int | None): One-based first source line.
            end_line (int | None): Inclusive last source line.

        Returns:
            dict[str, object]: Versioned translation brief with range metadata.
        """
        return self.service.prepare_file(
            path,
            target_lang=target_lang,
            encoding=encoding,
            source_lang=source_lang,
            domain=domain,
            topic=topic,
            style=style,
            start_line=start_line,
            end_line=end_line,
        )

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
        """Translate with fresh GlossWise briefs and HeavenBase LLMSession.

        Args:
            text (str): Source text.
            target_langs (Sequence[str] | None): Concrete target tags. Omit
                them to use workspace, then global default languages.
            source_lang (str): Concrete source tag or `auto`.
            domain (str | None): Optional terminology domain.
            topic (str | None): Optional rule/example topic.
            style (str | None): Optional translation style.
            preset (str | None): HeavenBase LLM preset override. When omitted,
                the global GlossWise translation preset is used.

        Returns:
            dict[str, object]: Translation or elicitation questions plus
                evidence and resolved LLM identity.
        """
        return TranslationService(self.workspace).translate(
            text,
            target_langs=target_langs,
            source_lang=source_lang,
            domain=domain,
            topic=topic,
            style=style,
            preset=preset,
        )

    def ocr_pdf(
        self,
        path: str | Path,
        *,
        preset: str | None = None,
        start_page: int | None = None,
        end_page: int | None = None,
        dpi: int = DEFAULT_OCR_DPI,
    ) -> dict[str, object]:
        """OCR authorized PDF pages into per-page temporary text.

        Args:
            path (str | Path): Server-local authorized PDF.
            preset (str | None): HeavenBase LLM preset override.
            start_page (int | None): One-based first PDF page.
            end_page (int | None): Inclusive last PDF page.
            dpi (int): Render resolution from 72 through 600.

        Returns:
            dict[str, object]: Short handle and redacted page metadata.
        """
        return self.service.ocr_pdf(
            path,
            preset=preset,
            start_page=start_page,
            end_page=end_page,
            dpi=dpi,
        )

    def list_documents(self) -> list[dict[str, object]]:
        """List temporary OCR document handles.

        Args:
            None.

        Returns:
            list[dict[str, object]]: Redacted manifests newest first.
        """
        return self.service.list_documents()

    def get_document(self, handle: str) -> dict[str, object]:
        """Describe one temporary OCR document.

        Args:
            handle (str): Short `gw-...` handle.

        Returns:
            dict[str, object]: Redacted document manifest.
        """
        return self.service.get_document(handle)

    def read_document(
        self,
        handle: str,
        page: int,
        *,
        start_line: int | None = None,
        end_line: int | None = None,
    ) -> dict[str, object]:
        """Read a bounded range from one OCR page.

        Args:
            handle (str): Short `gw-...` handle.
            page (int): One-based source PDF page.
            start_line (int | None): One-based first OCR text line.
            end_line (int | None): Inclusive last OCR text line.

        Returns:
            dict[str, object]: OCR text and range metadata.
        """
        return self.service.read_document(
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
        return self.service.remove_document(handle)

    def to_mcp(self, *, profile: str = "glosswise") -> Any:
        """Build one GlossWise-owned MCP Toolkit.

        Args:
            profile (str): `glosswise`, `glosswise-local`, or
                `glosswise-curator`.

        Returns:
            Any: HeavenBase Toolkit bound to this workspace.
        """
        return self.service.to_mcp(profile=profile)

    def close(self) -> None:
        """Close this app's machine Context exactly once.

        Args:
            None.

        Returns:
            None: This method releases owned resources.
        """
        if not self._closed:
            self.context.close()
            self._closed = True

    def __enter__(self) -> "GlossWiseApp":
        """Enter this app as a context manager.

        Args:
            None.

        Returns:
            GlossWiseApp: This open application.
        """
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Close this app after a context-managed operation.

        Args:
            exc_type (type[BaseException] | None): Active exception class.
            exc (BaseException | None): Active exception instance.
            traceback (TracebackType | None): Active exception traceback.

        Returns:
            None: This method does not suppress exceptions.
        """
        self.close()
