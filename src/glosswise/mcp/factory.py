"""Workspace-bound GlossWise MCP family factory."""

from __future__ import annotations

__all__ = ["GLOSSWISE_TOOL_NAMES", "glosswise_tool_functions"]

from typing import Any

from heavenbase.toolkit.families.workspace import WorkspaceToolContext

from .tools import (
    build_archive,
    build_get_document,
    build_get_record,
    build_list_documents,
    build_list_records,
    build_ocr_pdf,
    build_prepare_file,
    build_prepare_translation,
    build_put_example,
    build_put_rule,
    build_put_term,
    build_read_document,
    build_remove_document,
    build_scan_file,
    build_scan_text,
    build_search_examples,
    build_search_rules,
    build_search_terms,
    build_workspace_info,
)

GLOSSWISE_TOOL_NAMES = (
    "glosswise_workspace_info",
    "glosswise_prepare_translation",
    "glosswise_prepare_file",
    "glosswise_search_terms",
    "glosswise_search_rules",
    "glosswise_scan_text",
    "glosswise_scan_file",
    "glosswise_ocr_pdf",
    "glosswise_list_documents",
    "glosswise_get_document",
    "glosswise_read_document",
    "glosswise_remove_document",
    "glosswise_search_examples",
    "glosswise_list_records",
    "glosswise_get_record",
    "glosswise_put_term",
    "glosswise_put_rule",
    "glosswise_put_example",
    "glosswise_archive",
)


def glosswise_tool_functions(
    context: WorkspaceToolContext,
) -> dict[str, Any]:
    """Return the exact declared GlossWise tool mapping.

    Args:
        context (WorkspaceToolContext): Profile-scoped workspace authority.

    Returns:
        dict[str, Any]: Declared tool name to async callable mapping.

    Raises:
        RuntimeError: If the implementation inventory drifts from the
            declaration or a tool loses the GlossWise namespace.
        ValueError: If the profile excludes a required GlossWise entity.
    """
    for entity_id in (
        "glosswise-term",
        "glosswise-term-form",
        "glosswise-rule",
        "glosswise-example",
    ):
        context.require_entity(entity_id)
    functions = {
        "glosswise_workspace_info": build_workspace_info(context),
        "glosswise_prepare_translation": build_prepare_translation(context),
        "glosswise_prepare_file": build_prepare_file(context),
        "glosswise_search_terms": build_search_terms(context),
        "glosswise_search_rules": build_search_rules(context),
        "glosswise_scan_text": build_scan_text(context),
        "glosswise_scan_file": build_scan_file(context),
        "glosswise_ocr_pdf": build_ocr_pdf(context),
        "glosswise_list_documents": build_list_documents(context),
        "glosswise_get_document": build_get_document(context),
        "glosswise_read_document": build_read_document(context),
        "glosswise_remove_document": build_remove_document(context),
        "glosswise_search_examples": build_search_examples(context),
        "glosswise_list_records": build_list_records(context),
        "glosswise_get_record": build_get_record(context),
        "glosswise_put_term": build_put_term(context),
        "glosswise_put_rule": build_put_rule(context),
        "glosswise_put_example": build_put_example(context),
        "glosswise_archive": build_archive(context),
    }
    if tuple(functions) != GLOSSWISE_TOOL_NAMES:
        raise RuntimeError("GlossWise MCP implementation does not match its declared tools.")
    if any(not name.startswith("glosswise_") for name in GLOSSWISE_TOOL_NAMES):
        raise RuntimeError("Every GlossWise MCP tool must be namespaced.")
    return functions
