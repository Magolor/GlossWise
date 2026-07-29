"""Flat async adapters over workspace-selectable GlossWise services."""

from __future__ import annotations

__all__ = [
    "build_get_document",
    "build_list_documents",
    "build_ocr_pdf",
    "build_prepare_file",
    "build_prepare_translation",
    "build_archive",
    "build_get_record",
    "build_list_records",
    "build_put_example",
    "build_put_rule",
    "build_put_term",
    "build_scan_file",
    "build_scan_text",
    "build_search_examples",
    "build_search_rules",
    "build_search_terms",
    "build_workspace_info",
    "build_read_document",
    "build_remove_document",
]

import asyncio
from collections.abc import Callable, Mapping
from hashlib import sha256
import json
from typing import Any

from ..contracts import error_envelope, result_envelope
from ..errors import GlossWiseError, is_glosswise_error

MAX_MCP_RESULT_CHARS = 512_000
_RECORD_METHODS = {
    "term": ("get_term", "list_terms"),
    "rule": ("get_rule", "list_rules"),
    "example": ("get_example", "list_examples"),
}


def build_workspace_info(context: Any) -> Any:
    """Build the redacted workspace capability tool."""

    async def workspace_info(workspace_id: str = "") -> dict[str, object]:
        """Describe one or the active GlossWise workspace."""
        request = {
            "kind": "workspace_info",
            "workspace_id": str(workspace_id),
        }
        return await _invoke(
            request,
            lambda: result_envelope(
                request=request,
                detected_language={},
                items=[_service(context, workspace_id).info()],
            ),
        )

    return workspace_info


def build_prepare_translation(context: Any) -> Any:
    """Build the main translation-brief tool."""

    async def prepare_translation(
        text: str,
        target_lang: str,
        source_lang: str = "auto",
        domain: str = "",
        topic: str = "",
        style: str = "",
        term_limit: int = 20,
        rule_limit: int = 20,
        example_limit: int = 10,
        workspace_id: str = "",
    ) -> dict[str, object]:
        """Prepare bounded terminology, rules, examples, and conflicts."""
        request = _content_request(
            "translation_brief",
            "text",
            text,
            source_lang=source_lang,
            target_lang=target_lang,
            workspace_id=workspace_id,
        )
        return await _invoke(
            request,
            lambda: _service(context, workspace_id).prepare_translation(
                text,
                target_lang=target_lang,
                source_lang=source_lang,
                domain=_optional(domain),
                topic=_optional(topic),
                style=_optional(style),
                term_limit=term_limit,
                rule_limit=rule_limit,
                example_limit=example_limit,
            ),
        )

    return prepare_translation


def build_search_terms(context: Any) -> Any:
    """Build terminology search."""

    async def search_terms(
        query: str,
        query_lang: str = "auto",
        target_lang: str = "",
        domain: str = "",
        limit: int = 10,
        workspace_id: str = "",
    ) -> dict[str, object]:
        """Search terminology with inspectable lexical/vector evidence."""
        request = _content_request(
            "terms",
            "query",
            query,
            query_lang=query_lang,
            target_lang=target_lang,
            workspace_id=workspace_id,
        )
        return await _invoke(
            request,
            lambda: _service(context, workspace_id).search_terms(
                query,
                query_lang=query_lang,
                target_lang=_optional(target_lang),
                domain=_optional(domain),
                limit=limit,
            ),
        )

    return search_terms


def build_search_rules(context: Any) -> Any:
    """Build rule search."""

    async def search_rules(
        query: str,
        source_lang: str = "auto",
        target_lang: str = "",
        topic: str = "",
        style: str = "",
        limit: int = 10,
        workspace_id: str = "",
    ) -> dict[str, object]:
        """Search scoped rules with inspectable lexical/vector evidence."""
        request = _content_request(
            "rules",
            "query",
            query,
            source_lang=source_lang,
            target_lang=target_lang,
            workspace_id=workspace_id,
        )
        return await _invoke(
            request,
            lambda: _service(context, workspace_id).search_rules(
                query,
                source_lang=source_lang,
                target_lang=_optional(target_lang),
                topic=_optional(topic),
                style=_optional(style),
                limit=limit,
            ),
        )

    return search_rules


def build_scan_text(context: Any) -> Any:
    """Build transient text scanning."""

    async def scan_text(
        text: str,
        text_lang: str = "auto",
        target_lang: str = "",
        include_rules: bool = True,
        domain: str = "",
        topic: str = "",
        style: str = "",
        limit: int = 50,
        cursor: str = "",
        workspace_id: str = "",
    ) -> dict[str, object]:
        """Scan bounded transient text without persisting its contents."""
        request = _content_request(
            "scan_text",
            "text",
            text,
            text_lang=text_lang,
            target_lang=target_lang,
            workspace_id=workspace_id,
        )
        return await _invoke(
            request,
            lambda: _service(context, workspace_id).scan_text(
                text,
                text_lang=text_lang,
                target_lang=_optional(target_lang),
                include_rules=include_rules,
                domain=_optional(domain),
                topic=_optional(topic),
                style=_optional(style),
                limit=limit,
                cursor=_optional(cursor),
            ),
        )

    return scan_text


def build_scan_file(context: Any) -> Any:
    """Build authorized server-local file scanning."""

    async def scan_file(
        path: str,
        encoding: str = "utf-8",
        text_lang: str = "auto",
        target_lang: str = "",
        include_rules: bool = True,
        domain: str = "",
        topic: str = "",
        style: str = "",
        start_line: int = 0,
        end_line: int = 0,
        limit: int = 50,
        cursor: str = "",
        workspace_id: str = "",
    ) -> dict[str, object]:
        """Scan one authorized local regular file with strict decoding."""
        request = {
            "kind": "scan_file",
            "path_chars": len(str(path)),
            "encoding": str(encoding),
            "text_lang": str(text_lang),
            "target_lang": str(target_lang),
            "start_line": int(start_line),
            "end_line": int(end_line),
            "workspace_id": str(workspace_id),
        }
        return await _invoke(
            request,
            lambda: _service(context, workspace_id).scan_file(
                path,
                encoding=encoding,
                text_lang=text_lang,
                target_lang=_optional(target_lang),
                include_rules=include_rules,
                domain=_optional(domain),
                topic=_optional(topic),
                style=_optional(style),
                start_line=_optional_index(start_line),
                end_line=_optional_index(end_line),
                limit=limit,
                cursor=_optional(cursor),
            ),
        )

    return scan_file


def build_prepare_file(context: Any) -> Any:
    """Build authorized server-local file translation preparation."""

    async def prepare_file(
        path: str,
        target_lang: str,
        encoding: str = "utf-8",
        source_lang: str = "auto",
        domain: str = "",
        topic: str = "",
        style: str = "",
        start_line: int = 0,
        end_line: int = 0,
        term_limit: int = 20,
        rule_limit: int = 20,
        example_limit: int = 10,
        workspace_id: str = "",
    ) -> dict[str, object]:
        """Prepare a brief from one authorized local file line range."""
        request = {
            "kind": "prepare_file",
            "path_chars": len(str(path)),
            "encoding": str(encoding),
            "source_lang": str(source_lang),
            "target_lang": str(target_lang),
            "start_line": int(start_line),
            "end_line": int(end_line),
            "workspace_id": str(workspace_id),
        }
        return await _invoke(
            request,
            lambda: _service(context, workspace_id).prepare_file(
                path,
                target_lang=target_lang,
                encoding=encoding,
                source_lang=source_lang,
                domain=_optional(domain),
                topic=_optional(topic),
                style=_optional(style),
                start_line=_optional_index(start_line),
                end_line=_optional_index(end_line),
                term_limit=term_limit,
                rule_limit=rule_limit,
                example_limit=example_limit,
            ),
        )

    return prepare_file


def build_ocr_pdf(context: Any) -> Any:
    """Build authorized page-wise PDF OCR."""

    async def ocr_pdf(
        path: str,
        preset: str = "",
        start_page: int = 0,
        end_page: int = 0,
        dpi: int = 144,
        workspace_id: str = "",
    ) -> dict[str, object]:
        """OCR authorized PDF pages into a short temporary handle."""
        request = {
            "kind": "ocr_pdf",
            "path_chars": len(str(path)),
            "preset": str(preset),
            "start_page": int(start_page),
            "end_page": int(end_page),
            "dpi": int(dpi),
            "workspace_id": str(workspace_id),
        }
        return await _invoke(
            request,
            lambda: result_envelope(
                request=request,
                detected_language={},
                items=[
                    _service(context, workspace_id).ocr_pdf(
                        path,
                        preset=_optional(preset),
                        start_page=_optional_index(start_page),
                        end_page=_optional_index(end_page),
                        dpi=dpi,
                    )
                ],
            ),
        )

    return ocr_pdf


def build_list_documents(context: Any) -> Any:
    """Build temporary OCR-document listing."""

    async def list_documents(
        workspace_id: str = "",
    ) -> dict[str, object]:
        """List temporary OCR handles for one workspace."""
        request = {
            "kind": "list_documents",
            "workspace_id": str(workspace_id),
        }
        return await _invoke(
            request,
            lambda: result_envelope(
                request=request,
                detected_language={},
                items=_service(context, workspace_id).list_documents(),
            ),
        )

    return list_documents


def build_get_document(context: Any) -> Any:
    """Build temporary OCR-document inspection."""

    async def get_document(
        handle: str,
        workspace_id: str = "",
    ) -> dict[str, object]:
        """Describe one temporary OCR document."""
        request = {
            "kind": "get_document",
            "handle": str(handle),
            "workspace_id": str(workspace_id),
        }
        return await _invoke(
            request,
            lambda: result_envelope(
                request=request,
                detected_language={},
                items=[_service(context, workspace_id).get_document(handle)],
            ),
        )

    return get_document


def build_read_document(context: Any) -> Any:
    """Build bounded OCR-page reading."""

    async def read_document(
        handle: str,
        page: int,
        start_line: int = 0,
        end_line: int = 0,
        workspace_id: str = "",
    ) -> dict[str, object]:
        """Read a line range from one OCR page by short handle."""
        request = {
            "kind": "read_document",
            "handle": str(handle),
            "page": int(page),
            "start_line": int(start_line),
            "end_line": int(end_line),
            "workspace_id": str(workspace_id),
        }
        return await _invoke(
            request,
            lambda: result_envelope(
                request=request,
                detected_language={},
                items=[
                    _service(context, workspace_id).read_document(
                        handle,
                        page,
                        start_line=_optional_index(start_line),
                        end_line=_optional_index(end_line),
                    )
                ],
            ),
        )

    return read_document


def build_remove_document(context: Any) -> Any:
    """Build temporary OCR-document removal."""

    async def remove_document(
        handle: str,
        workspace_id: str = "",
    ) -> dict[str, object]:
        """Remove one temporary OCR document by short handle."""
        request = {
            "kind": "remove_document",
            "handle": str(handle),
            "workspace_id": str(workspace_id),
        }
        return await _invoke(
            request,
            lambda: result_envelope(
                request=request,
                detected_language={},
                items=[_service(context, workspace_id).remove_document(handle)],
            ),
        )

    return remove_document


def build_search_examples(context: Any) -> Any:
    """Build filtered example retrieval."""

    async def search_examples(
        query: str,
        source_lang: str = "",
        target_lang: str = "",
        topic: str = "",
        style: str = "",
        tag: str = "",
        limit: int = 10,
        workspace_id: str = "",
    ) -> dict[str, object]:
        """Search comparable examples through the configured embedding space."""
        request = _content_request(
            "examples",
            "query",
            query,
            source_lang=source_lang,
            target_lang=target_lang,
            workspace_id=workspace_id,
        )
        return await _invoke(
            request,
            lambda: _service(context, workspace_id).search_examples(
                query,
                source_lang=_optional(source_lang),
                target_lang=_optional(target_lang),
                topic=_optional(topic),
                style=_optional(style),
                tag=_optional(tag),
                limit=limit,
            ),
        )

    return search_examples


def build_list_records(context: Any) -> Any:
    """Build bounded curator record listing."""

    async def list_records(
        kind: str,
        status: str = "",
        limit: int = 50,
        workspace_id: str = "",
    ) -> dict[str, object]:
        """List terms, rules, or examples through domain curation policy."""
        request = {
            "kind": "list_records",
            "record_kind": str(kind),
            "status": str(status),
            "limit": int(limit),
            "workspace_id": str(workspace_id),
        }

        def call() -> dict[str, object]:
            selected = _record_kind(kind)
            method = getattr(
                _service(context, workspace_id),
                _RECORD_METHODS[selected][1],
            )
            return result_envelope(
                request={**request, "record_kind": selected},
                detected_language={},
                items=method(
                    status=_optional(status),
                    limit=limit,
                ),
            )

        return await _invoke(
            request,
            call,
        )

    return list_records


def build_get_record(context: Any) -> Any:
    """Build exact curator record lookup."""

    async def get_record(
        kind: str,
        object_id: str,
        workspace_id: str = "",
    ) -> dict[str, object]:
        """Get one term, rule, or example by object id."""
        clean_id = str(object_id).strip()
        request = {
            "kind": "get_record",
            "record_kind": str(kind),
            "object_id": clean_id,
            "workspace_id": str(workspace_id),
        }

        def call() -> dict[str, object]:
            selected = _record_kind(kind)
            method = getattr(
                _service(context, workspace_id),
                _RECORD_METHODS[selected][0],
            )
            row = method(clean_id)
            if row is None:
                raise GlossWiseError(
                    "not_found",
                    f"GlossWise {selected} {clean_id!r} was not found.",
                    object_ids=(clean_id,),
                )
            return result_envelope(
                request={**request, "record_kind": selected},
                detected_language={},
                items=[row],
            )

        return await _invoke(request, call)

    return get_record


def build_put_term(context: Any) -> Any:
    """Build domain-validated term upsert."""

    async def put_term(
        term_json: str,
        forms_json: str = "[]",
        workspace_id: str = "",
    ) -> dict[str, object]:
        """Create or update one term from flat JSON arguments."""
        request = {
            "kind": "put_term",
            **_json_request("term", term_json),
            **_json_request("forms", forms_json),
            "workspace_id": str(workspace_id),
        }

        def call() -> dict[str, object]:
            term = _json_object(term_json, "term")
            forms = _json_array(forms_json, "forms")
            service = _service(context, workspace_id)
            row = service.put_term(term, forms)
            advisory = service.term_language_advisory(row)
            missing = [str(language) for language in advisory["missing_languages"]]
            warnings = (
                [f"Term is missing active preferred forms for workspace default languages: {', '.join(missing)}. Defaults are advisory; the term was stored."]
                if missing
                else []
            )
            return result_envelope(
                request=request,
                detected_language={},
                items=[row],
                warnings=warnings,
            )

        return await _invoke(request, call)

    return put_term


def build_put_rule(context: Any) -> Any:
    """Build domain-validated rule upsert."""

    async def put_rule(
        rule_json: str,
        workspace_id: str = "",
    ) -> dict[str, object]:
        """Create or update one rule from a JSON object."""
        request = {
            "kind": "put_rule",
            **_json_request("rule", rule_json),
            "workspace_id": str(workspace_id),
        }

        def call() -> dict[str, object]:
            row = _service(context, workspace_id).put_rule(_json_object(rule_json, "rule"))
            return result_envelope(
                request=request,
                detected_language={},
                items=[row],
            )

        return await _invoke(request, call)

    return put_rule


def build_put_example(context: Any) -> Any:
    """Build domain-validated example upsert."""

    async def put_example(
        example_json: str,
        workspace_id: str = "",
    ) -> dict[str, object]:
        """Create or update one example from a JSON object."""
        request = {
            "kind": "put_example",
            **_json_request("example", example_json),
            "workspace_id": str(workspace_id),
        }

        def call() -> dict[str, object]:
            row = _service(context, workspace_id).put_example(_json_object(example_json, "example"))
            return result_envelope(
                request=request,
                detected_language={},
                items=[row],
            )

        return await _invoke(request, call)

    return put_example


def build_archive(context: Any) -> Any:
    """Build safe curator soft deletion."""

    async def archive(
        object_id: str,
        workspace_id: str = "",
    ) -> dict[str, object]:
        """Mark one unambiguous GlossWise record as deprecated."""
        clean_id = str(object_id).strip()
        request = {
            "kind": "archive",
            "object_id": clean_id,
            "workspace_id": str(workspace_id),
        }
        return await _invoke(
            request,
            lambda: result_envelope(
                request=request,
                detected_language={},
                items=[_service(context, workspace_id).archive(clean_id)],
            ),
        )

    return archive


def _service(context: Any, workspace_id: str) -> Any:
    if hasattr(context, "workspace"):
        workspace = context.workspace
        selected = str(workspace_id).strip()
        if selected and selected != workspace.id:
            raise GlossWiseError(
                "workspace_not_found",
                f"This embedded Toolkit is bound to workspace {workspace.id!r}.",
                object_ids=(selected,),
            )
        return workspace.glosswise
    try:
        return context.open(
            _optional(workspace_id),
            ensure_default=True,
        ).glosswise
    except KeyError as error:
        selected = str(workspace_id).strip()
        raise GlossWiseError(
            "workspace_not_found",
            "No matching GlossWise workspace is registered.",
            object_ids=(selected,) if selected else (),
        ) from error


async def _invoke(
    request: Mapping[str, object],
    call: Callable[[], Mapping[str, object]],
) -> dict[str, object]:
    try:
        result = dict(await asyncio.to_thread(call))
        rendered = json.dumps(
            result,
            ensure_ascii=False,
            separators=(",", ":"),
        )
        if len(rendered) > MAX_MCP_RESULT_CHARS:
            return error_envelope(
                request=request,
                code="input_too_large",
                message=("The bounded GlossWise response exceeds the MCP output budget; reduce the requested limits."),
            )
        return result
    except Exception as error:
        if is_glosswise_error(error):
            payload = error.to_dict()
            return error_envelope(
                request=request,
                code=str(payload["code"]),
                message=str(payload["message"]),
                object_ids=payload.get("object_ids", ()),
            )
        return error_envelope(
            request=request,
            code="internal_error",
            message="GlossWise could not complete the request.",
        )


def _content_request(
    kind: str,
    field: str,
    value: object,
    **metadata: object,
) -> dict[str, object]:
    text = value if isinstance(value, str) else ""
    return {
        "kind": kind,
        f"{field}_sha256": sha256(text.encode("utf-8")).hexdigest(),
        f"{field}_chars": len(text),
        **{key: str(item) for key, item in metadata.items()},
    }


def _optional(value: object) -> str | None:
    selected = str(value).strip()
    return selected or None


def _optional_index(value: object) -> int | None:
    selected = int(value)
    return None if selected == 0 else selected


def _record_kind(value: object) -> str:
    selected = str(value).strip().lower()
    if selected not in _RECORD_METHODS:
        expected = ", ".join(sorted(_RECORD_METHODS))
        raise GlossWiseError(
            "invalid_record_kind",
            f"Record kind must be one of {expected}.",
        )
    return selected


def _json_object(value: str, name: str) -> dict[str, object]:
    decoded = _json_value(value, name)
    if not isinstance(decoded, dict):
        raise GlossWiseError(
            "invalid_json",
            f"{name} JSON must decode to an object.",
        )
    return decoded


def _json_array(value: str, name: str) -> list[dict[str, object]]:
    decoded = _json_value(value, name)
    if not isinstance(decoded, list) or any(not isinstance(item, dict) for item in decoded):
        raise GlossWiseError(
            "invalid_json",
            f"{name} JSON must decode to an array of objects.",
        )
    return decoded


def _json_string_array(value: str, name: str) -> list[str]:
    decoded = _json_value(value, name)
    if not isinstance(decoded, list) or any(not isinstance(item, str) for item in decoded):
        raise GlossWiseError(
            "invalid_json",
            f"{name} JSON must decode to an array of strings.",
        )
    return decoded


def _json_value(value: str, name: str) -> object:
    try:
        return json.loads(str(value))
    except (TypeError, ValueError, json.JSONDecodeError) as error:
        raise GlossWiseError(
            "invalid_json",
            f"{name} must contain valid JSON.",
        ) from error


def _json_request(name: str, value: str) -> dict[str, object]:
    text = str(value)
    return {
        f"{name}_sha256": sha256(text.encode("utf-8")).hexdigest(),
        f"{name}_chars": len(text),
    }
