"""MCP adapters for the global GlossWise workspace directory."""

from __future__ import annotations

__all__ = [
    "build_activate_workspace",
    "build_create_workspace",
    "build_deactivate_workspace",
    "build_get_workspace",
    "build_health_workspace",
    "build_list_workspaces",
    "build_open_workspace",
    "build_remove_workspace",
    "build_set_workspace_languages",
]

from typing import Any

from ..contracts import result_envelope
from ..errors import GlossWiseError
from .tools import (
    _invoke,
    _json_request,
    _json_string_array,
    _optional,
)


def _result(request: dict[str, object], items: list[dict[str, object]]) -> dict[str, object]:
    return result_envelope(
        request=request,
        detected_language={},
        items=items,
    )


def _workspace_call(call: Any, workspace_id: str = "") -> Any:
    try:
        return call()
    except KeyError as error:
        selected = str(workspace_id).strip()
        raise GlossWiseError(
            "workspace_not_found",
            "No matching GlossWise workspace is registered.",
            object_ids=(selected,) if selected else (),
        ) from error


def build_list_workspaces(directory: Any) -> Any:
    """Build global GlossWise workspace listing."""

    async def list_workspaces() -> dict[str, object]:
        """List registered GlossWise workspaces and active selection."""
        request = {"kind": "list_workspaces"}
        return await _invoke(
            request,
            lambda: _result(request, directory.list()),
        )

    return list_workspaces


def build_get_workspace(directory: Any) -> Any:
    """Build exact or active workspace inspection."""

    async def get_workspace(workspace_id: str = "") -> dict[str, object]:
        """Get one workspace, defaulting to the active workspace."""
        request = {
            "kind": "get_workspace",
            "workspace_id": str(workspace_id),
        }
        return await _invoke(
            request,
            lambda: _result(
                request,
                [
                    _workspace_call(
                        lambda: directory.get(
                            _optional(workspace_id),
                            ensure_default=True,
                        ),
                        workspace_id,
                    )
                ],
            ),
        )

    return get_workspace


def build_create_workspace(directory: Any) -> Any:
    """Build managed workspace creation."""

    async def create_workspace(
        workspace_id: str,
        activate: bool = True,
    ) -> dict[str, object]:
        """Create a managed workspace and optionally activate it."""
        request = {
            "kind": "create_workspace",
            "workspace_id": str(workspace_id),
            "activate": bool(activate),
        }
        return await _invoke(
            request,
            lambda: _result(
                request,
                [
                    directory.create(
                        workspace_id,
                        activate=activate,
                    )
                ],
            ),
        )

    return create_workspace


def build_set_workspace_languages(directory: Any) -> Any:
    """Build advisory workspace-language configuration."""

    async def set_workspace_languages(
        languages_json: str,
        workspace_id: str = "",
    ) -> dict[str, object]:
        """Set non-enforcing default languages for one or the active workspace."""
        request = {
            "kind": "set_workspace_languages",
            **_json_request("languages", languages_json),
            "workspace_id": str(workspace_id),
        }
        return await _invoke(
            request,
            lambda: _result(
                request,
                [
                    _workspace_call(
                        lambda: directory.configure_default_languages(
                            _json_string_array(languages_json, "languages"),
                            _optional(workspace_id),
                            ensure_default=True,
                        ),
                        workspace_id,
                    )
                ],
            ),
        )

    return set_workspace_languages


def build_activate_workspace(directory: Any) -> Any:
    """Build active workspace selection."""

    async def activate_workspace(workspace_id: str) -> dict[str, object]:
        """Select a registered GlossWise workspace."""
        request = {
            "kind": "activate_workspace",
            "workspace_id": str(workspace_id),
        }
        return await _invoke(
            request,
            lambda: _result(
                request,
                [
                    _workspace_call(
                        lambda: directory.activate(workspace_id),
                        workspace_id,
                    )
                ],
            ),
        )

    return activate_workspace


def build_deactivate_workspace(directory: Any) -> Any:
    """Build active workspace clearing."""

    async def deactivate_workspace() -> dict[str, object]:
        """Clear the active GlossWise workspace selection."""
        request = {"kind": "deactivate_workspace"}
        return await _invoke(
            request,
            lambda: _result(request, [directory.deactivate()]),
        )

    return deactivate_workspace


def build_remove_workspace(directory: Any) -> Any:
    """Build non-destructive workspace unregistration."""

    async def remove_workspace(workspace_id: str) -> dict[str, object]:
        """Unregister a workspace while retaining its database."""
        request = {
            "kind": "remove_workspace",
            "workspace_id": str(workspace_id),
        }
        return await _invoke(
            request,
            lambda: _result(
                request,
                [
                    _workspace_call(
                        lambda: directory.remove(workspace_id),
                        workspace_id,
                    )
                ],
            ),
        )

    return remove_workspace


def build_open_workspace(directory: Any) -> Any:
    """Build workspace initialization and capability inspection."""

    async def open_workspace(workspace_id: str = "") -> dict[str, object]:
        """Open one workspace and return its redacted capabilities."""
        request = {
            "kind": "open_workspace",
            "workspace_id": str(workspace_id),
        }
        return await _invoke(
            request,
            lambda: _result(
                request,
                [
                    _workspace_call(
                        lambda: directory.info(
                            _optional(workspace_id),
                            ensure_default=True,
                        ),
                        workspace_id,
                    )
                ],
            ),
        )

    return open_workspace


def build_health_workspace(directory: Any) -> Any:
    """Build redacted workspace health inspection."""

    async def health_workspace(workspace_id: str = "") -> dict[str, object]:
        """Return registry and runtime health for one workspace."""
        request = {
            "kind": "health_workspace",
            "workspace_id": str(workspace_id),
        }
        return await _invoke(
            request,
            lambda: _result(
                request,
                [
                    _workspace_call(
                        lambda: directory.health(
                            _optional(workspace_id),
                            ensure_default=True,
                        ),
                        workspace_id,
                    )
                ],
            ),
        )

    return health_workspace
