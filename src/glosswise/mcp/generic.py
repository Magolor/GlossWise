"""One generic GlossWise MCP Toolkit for every registered workspace."""

from __future__ import annotations

__all__ = [
    "GENERIC_FULL_TOOL_NAMES",
    "GENERIC_LOCAL_TOOL_NAMES",
    "GENERIC_READ_TOOL_NAMES",
    "generic_tool_functions",
    "generic_toolkit",
]

from importlib.resources import files
from typing import Any

from ..contracts import result_envelope
from .tools import (
    _invoke,
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
from .workspaces import (
    build_activate_workspace,
    build_create_workspace,
    build_deactivate_workspace,
    build_get_workspace,
    build_health_workspace,
    build_list_workspaces,
    build_open_workspace,
    build_remove_workspace,
    build_set_workspace_languages,
)

GENERIC_READ_TOOL_NAMES = (
    "glosswise_workspace_info",
    "glosswise_prepare_translation",
    "glosswise_search_terms",
    "glosswise_search_rules",
    "glosswise_scan_text",
    "glosswise_search_examples",
    "glosswise_list_records",
    "glosswise_get_record",
    "glosswise_list_workspaces",
    "glosswise_get_workspace",
    "glosswise_open_workspace",
    "glosswise_health_workspace",
    "glosswise_read_skill",
)
GENERIC_FULL_TOOL_NAMES = (
    *GENERIC_READ_TOOL_NAMES,
    "glosswise_put_term",
    "glosswise_put_rule",
    "glosswise_put_example",
    "glosswise_archive",
    "glosswise_create_workspace",
    "glosswise_set_workspace_languages",
    "glosswise_activate_workspace",
    "glosswise_deactivate_workspace",
    "glosswise_remove_workspace",
)
GENERIC_LOCAL_TOOL_NAMES = (
    *GENERIC_FULL_TOOL_NAMES,
    "glosswise_scan_file",
    "glosswise_prepare_file",
    "glosswise_ocr_pdf",
    "glosswise_list_documents",
    "glosswise_get_document",
    "glosswise_read_document",
    "glosswise_remove_document",
)
_PROFILE_TOOLS = {
    "read": GENERIC_READ_TOOL_NAMES,
    "full": GENERIC_FULL_TOOL_NAMES,
    "local": GENERIC_LOCAL_TOOL_NAMES,
}


def _build_read_skill() -> Any:
    async def read_skill() -> dict[str, object]:
        """Read the exact packaged GlossWise agent Skill."""
        request = {"kind": "read_skill", "skill": "glosswise"}

        def call() -> dict[str, object]:
            text = files("glosswise").joinpath("skills").joinpath("glosswise").joinpath("SKILL.md").read_text(encoding="utf-8")
            return result_envelope(
                request=request,
                detected_language={},
                items=[{"name": "glosswise", "text": text}],
            )

        return await _invoke(request, call)

    return read_skill


def generic_tool_functions(
    directory: Any,
    *,
    profile: str = "full",
) -> dict[str, Any]:
    """Build the selected global GlossWise MCP callable mapping.

    Args:
        directory (Any): Open `GlossWiseWorkspaces` directory.
        profile (str): Advanced tool restriction. Supported values:
            - `full`: Read, domain CRUD, Skill, and workspace management.
            - `read`: Read-only data, context, Skill, and workspace inspection.
            - `local`: Full profile plus authorized server-local file scans.

    Returns:
        dict[str, Any]: Ordered tool-name to async-callable mapping.

    Raises:
        ValueError: If `profile` is unsupported.
        RuntimeError: If the implementation inventory drifts.
    """
    selected = str(profile).strip().lower()
    if selected not in _PROFILE_TOOLS:
        expected = ", ".join(sorted(_PROFILE_TOOLS))
        raise ValueError(f"GlossWise MCP profile must be one of {expected}; got {profile!r}.")
    functions = {
        "glosswise_workspace_info": build_workspace_info(directory),
        "glosswise_prepare_translation": build_prepare_translation(directory),
        "glosswise_search_terms": build_search_terms(directory),
        "glosswise_search_rules": build_search_rules(directory),
        "glosswise_scan_text": build_scan_text(directory),
        "glosswise_search_examples": build_search_examples(directory),
        "glosswise_list_records": build_list_records(directory),
        "glosswise_get_record": build_get_record(directory),
        "glosswise_list_workspaces": build_list_workspaces(directory),
        "glosswise_get_workspace": build_get_workspace(directory),
        "glosswise_open_workspace": build_open_workspace(directory),
        "glosswise_health_workspace": build_health_workspace(directory),
        "glosswise_read_skill": _build_read_skill(),
        "glosswise_put_term": build_put_term(directory),
        "glosswise_put_rule": build_put_rule(directory),
        "glosswise_put_example": build_put_example(directory),
        "glosswise_archive": build_archive(directory),
        "glosswise_create_workspace": build_create_workspace(directory),
        "glosswise_set_workspace_languages": build_set_workspace_languages(directory),
        "glosswise_activate_workspace": build_activate_workspace(directory),
        "glosswise_deactivate_workspace": build_deactivate_workspace(directory),
        "glosswise_remove_workspace": build_remove_workspace(directory),
        "glosswise_scan_file": build_scan_file(directory),
        "glosswise_prepare_file": build_prepare_file(directory),
        "glosswise_ocr_pdf": build_ocr_pdf(directory),
        "glosswise_list_documents": build_list_documents(directory),
        "glosswise_get_document": build_get_document(directory),
        "glosswise_read_document": build_read_document(directory),
        "glosswise_remove_document": build_remove_document(directory),
    }
    selected_names = _PROFILE_TOOLS[selected]
    if any(name not in functions for name in GENERIC_LOCAL_TOOL_NAMES):
        raise RuntimeError("GlossWise generic MCP implementation inventory drifted.")
    return {name: functions[name] for name in selected_names}


def generic_toolkit(
    directory: Any,
    *,
    profile: str = "full",
) -> Any:
    """Build one runtime Toolkit spanning all GlossWise workspaces.

    Args:
        directory (Any): Open `GlossWiseWorkspaces` directory whose Context
            remains alive for the Toolkit lifetime.
        profile (str): Advanced profile documented by
            `generic_tool_functions`.

    Returns:
        Any: Runtime-only HeavenBase Toolkit ready for MCP serving.
    """
    from heavenbase.toolkit import Toolkit

    functions = generic_tool_functions(directory, profile=profile)
    toolkit = Toolkit(
        "glosswise",
        description=("Global GlossWise terminology, translation-context, curation, Skill, and workspace tools."),
        namespace="glosswise-global",
        resolver=directory.context.modules(),
        config=directory.context.config,
    )
    for name, function in functions.items():
        toolkit.add(
            function,
            name=name,
            description=str(function.__doc__ or name).strip(),
            namespace="glosswise-global",
        )
        toolkit.tools[name].metadata["runtime_only"] = True
        toolkit.tools[name].capsule.manifest.capabilities["registry_persistence"] = {
            "ok": False,
            "reasons": ["generic GlossWise tools close over a live workspace directory"],
        }
    return toolkit
