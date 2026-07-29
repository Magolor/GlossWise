"""GlossWise-scoped workspace directory and managed local defaults."""

from __future__ import annotations

__all__ = [
    "DEFAULT_WORKSPACE_ID",
    "GlossWiseWorkspaces",
    "managed_database_path",
]

from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from pathlib import Path
from threading import RLock
from types import TracebackType
from typing import Any

import heavenbase as hb
from heavenbase.utils import check_workspace_id
from heavenbase.workspace import WorkspaceManifest, WorkspaceSpec

from ..config import GlossWiseConfig
from ..errors import GlossWiseError
from ..language import (
    DEFAULT_LANGUAGES_CONFIG_KEY,
    canonicalize_languages,
)
from ..lifecycle import install, setup_workspace

DEFAULT_WORKSPACE_ID = "default"
_DEFAULT_HOME = Path("~/.glosswise")
_PROFILES = ("full", "read", "local")
_MCP_TRANSPORTS = ("stdio", "http", "streamable-http", "sse")
DEFAULT_MCP_HOST = "127.0.0.1"
DEFAULT_MCP_PORT = 61055


def managed_database_path(workspace_id: str = DEFAULT_WORKSPACE_ID) -> Path:
    """Return the managed SQLite path for one GlossWise workspace.

    Args:
        workspace_id (str): Valid HeavenBase workspace identifier.

    Returns:
        Path: Expanded absolute path below `~/.glosswise`.

    Raises:
        ValueError: If `workspace_id` is not a valid HeavenBase identifier.
    """
    clean_id = check_workspace_id(str(workspace_id))
    return (_DEFAULT_HOME.expanduser() / f"{clean_id}.db").resolve()


class GlossWiseWorkspaces:
    """Own GlossWise workspace discovery and selection for one Context."""

    def __init__(
        self,
        context: hb.Context,
        *,
        owns_context: bool = False,
        bootstrap: str | Path | None = None,
    ) -> None:
        """Bind a workspace directory to one HeavenBase Context.

        Args:
            context (hb.Context): Context owning the workspace registry.
            owns_context (bool): Whether `close()` retires `context`.
            bootstrap (str | Path | None): Bootstrap argument used to build
                portable child CLI configurations.

        Returns:
            None: This initializer stores lifecycle authority.
        """
        self.context = context
        self.owns_context = bool(owns_context)
        self.bootstrap = None if bootstrap is None else str(bootstrap)
        self._opened: dict[str, Any] = {}
        self._lock = RLock()
        self._closed = False

    @classmethod
    def load(
        cls,
        *,
        bootstrap: str | Path | None = None,
    ) -> "GlossWiseWorkspaces":
        """Open the configured HeavenBase workspace directory.

        Args:
            bootstrap (str | Path | None): Optional HeavenBase bootstrap YAML.

        Returns:
            GlossWiseWorkspaces: Owning directory object.
        """
        context = hb.Context.load(
            home_path=None if bootstrap is None else str(bootstrap),
        )
        return cls(
            context,
            owns_context=True,
            bootstrap=bootstrap,
        )

    def list(self) -> list[dict[str, object]]:
        """List only registered GlossWise workspaces.

        Args:
            None.

        Returns:
            list[dict[str, object]]: Redacted summaries ordered by workspace
                identifier.
        """
        return [self._summary(spec) for spec in WorkspaceSpec.list(context=self.context) if self._is_glosswise(spec)]

    def user_config(self) -> dict[str, object]:
        """Return global defaults shared by all GlossWise workspaces.

        Args:
            None.

        Returns:
            dict[str, object]: Non-secret user configuration.
        """
        return GlossWiseConfig(self.context).describe()

    def configure_user_languages(
        self,
        languages: Sequence[str],
    ) -> list[str]:
        """Set languages inherited by newly created workspaces.

        Args:
            languages (Sequence[str]): Non-empty ordered concrete BCP 47 tags.

        Returns:
            list[str]: Canonical user-default languages.
        """
        return GlossWiseConfig(self.context).configure_default_languages(languages)

    def configure_translation(
        self,
        mode: str,
        *,
        custom_prompt: str | None = None,
    ) -> dict[str, object]:
        """Set global translation behavior.

        Args:
            mode (str): `auto`, `yolo`, `elicit`, `explain`, or `custom`.
            custom_prompt (str | None): Required only for `custom`.

        Returns:
            dict[str, object]: Canonical translation configuration.
        """
        return GlossWiseConfig(self.context).configure_translation(
            mode,
            custom_prompt=custom_prompt,
        )

    def configure_translation_preset(self, preset: str) -> str:
        """Set the HeavenBase LLM preset used for direct translation.

        Args:
            preset (str): Non-blank HeavenBase LLM preset.

        Returns:
            str: Canonical preset name.
        """
        return GlossWiseConfig(self.context).configure_translation_preset(preset)

    def configure_ocr(self, preset: str) -> str:
        """Set the HeavenBase LLM preset used for PDF OCR.

        Args:
            preset (str): Non-blank HeavenBase LLM preset.

        Returns:
            str: Canonical preset name.
        """
        return GlossWiseConfig(self.context).configure_ocr(preset)

    def get(
        self,
        workspace_id: str | None = None,
        *,
        ensure_default: bool = False,
    ) -> dict[str, object]:
        """Return one redacted GlossWise workspace record.

        Args:
            workspace_id (str | None): Explicit id, or active/default
                resolution when omitted.
            ensure_default (bool): Whether absence creates the managed default.

        Returns:
            dict[str, object]: Workspace metadata without backend credentials
                or database paths.

        Raises:
            KeyError: If no matching GlossWise workspace exists.
        """
        return self._summary(
            self._resolve_spec(
                workspace_id,
                ensure_default=ensure_default,
            )
        )

    def create(
        self,
        workspace_id: str = DEFAULT_WORKSPACE_ID,
        *,
        database: str | Path | None = None,
        activate: bool = True,
    ) -> dict[str, object]:
        """Create or compatibly reopen one managed SQLite workspace.

        Args:
            workspace_id (str): Stable workspace identifier.
            database (str | Path | None): Advanced SQLite file override.
                Omit it to use `~/.glosswise/<workspace_id>.db`.
            activate (bool): Whether to persist this workspace as active.

        Returns:
            dict[str, object]: Redacted workspace summary.

        Raises:
            FileExistsError: If the id belongs to a non-GlossWise workspace or
                has a conflicting construction contract.
            GlossWiseError: If a new managed workspace is requested before
                global languages have been configured.
        """
        clean_id = check_workspace_id(str(workspace_id))
        with self._lock:
            return self._create(
                clean_id,
                database=database,
                activate=activate,
            )

    def configure_default_languages(
        self,
        languages: Sequence[str],
        workspace_id: str | None = None,
        *,
        ensure_default: bool = True,
    ) -> dict[str, object]:
        """Set advisory default languages for one workspace.

        Args:
            languages (Sequence[str]): Ordered concrete BCP 47 tags. An empty
                sequence clears the annotation.
            workspace_id (str | None): Explicit id or active/default
                selection.
            ensure_default (bool): Whether absence creates the managed default.

        Returns:
            dict[str, object]: Updated redacted workspace summary.
        """
        workspace = self.open(
            workspace_id,
            ensure_default=ensure_default,
        )
        workspace.glosswise.configure_default_languages(languages)
        return self.get(workspace.id)

    def _create(
        self,
        workspace_id: str,
        *,
        database: str | Path | None,
        activate: bool,
    ) -> dict[str, object]:
        """Create one workspace while the directory mutation lock is held."""
        clean_id = workspace_id
        config = GlossWiseConfig(self.context)
        languages = config.default_languages()
        if self._load_spec(clean_id) is None and not languages:
            raise GlossWiseError(
                "setup_required",
                ("Configure global languages before creating a managed " "workspace. Run `glosswise setup -l en -l <language>`."),
            )
        self._ensure_installed()
        existing = self._load_spec(clean_id)
        is_new = existing is None
        if existing is not None and not self._is_glosswise(existing):
            raise FileExistsError(f"Workspace {clean_id!r} exists but is not a GlossWise workspace.")
        if existing is not None and database is None:
            workspace = self._open_spec(existing)
        else:
            path = managed_database_path(clean_id) if database is None else Path(database).expanduser().resolve()
            path.parent.mkdir(parents=True, exist_ok=True)
            with self._minimal_defaults(clean_id):
                workspace = hb.HeavenBase(
                    clean_id,
                    context=self.context,
                    backends={
                        "main": {
                            "type": "sqlite",
                            "database": path.as_uri(),
                        }
                    },
                )
        workspace.enable_extension("glosswise")
        setup_workspace(workspace)
        if is_new:
            workspace.glosswise.configure_default_languages(languages)
        self._opened[clean_id] = workspace
        if activate:
            self.context.activate_workspace(clean_id)
        spec = WorkspaceSpec.load(clean_id, context=self.context)
        return self._summary(spec)

    def ensure_default(self, *, activate: bool = True) -> dict[str, object]:
        """Ensure the managed default workspace exists.

        Args:
            activate (bool): Whether a newly created or existing default
                becomes the Context's active workspace.

        Returns:
            dict[str, object]: Redacted default-workspace summary.
        """
        spec = self._load_spec(DEFAULT_WORKSPACE_ID)
        if spec is None:
            return self.create(
                DEFAULT_WORKSPACE_ID,
                activate=activate,
            )
        if not self._is_glosswise(spec):
            raise FileExistsError(f"Workspace {DEFAULT_WORKSPACE_ID!r} exists but is not a GlossWise workspace.")
        if activate:
            self.context.activate_workspace(DEFAULT_WORKSPACE_ID)
            spec = WorkspaceSpec.load(DEFAULT_WORKSPACE_ID, context=self.context)
        return self._summary(spec)

    def activate(self, workspace_id: str) -> dict[str, object]:
        """Select one registered GlossWise workspace.

        Args:
            workspace_id (str): Registered GlossWise workspace id.

        Returns:
            dict[str, object]: Redacted selected-workspace summary.

        Raises:
            KeyError: If the workspace is absent or not GlossWise-enabled.
        """
        spec = self._require_glosswise(workspace_id)
        self.context.activate_workspace(spec.id)
        return self._summary(WorkspaceSpec.load(spec.id, context=self.context))

    def deactivate(self) -> dict[str, object]:
        """Clear an explicitly active GlossWise workspace selection.

        Args:
            None.

        Returns:
            dict[str, object]: Previous selection and effective fallback.
                An unrelated active HeavenBase workspace is left unchanged.
        """
        previous = self.context.active_workspace_id
        if previous is None:
            return {
                "deactivated": None,
                "effective": DEFAULT_WORKSPACE_ID,
            }
        spec = self._load_spec(previous)
        if spec is None or not self._is_glosswise(spec):
            return {
                "deactivated": None,
                "effective": previous,
            }
        self.context.deactivate_workspace()
        return {
            "deactivated": previous,
            "effective": DEFAULT_WORKSPACE_ID,
        }

    def remove(self, workspace_id: str) -> dict[str, object]:
        """Unregister one GlossWise workspace without deleting its data file.

        Args:
            workspace_id (str): Registered GlossWise workspace id.

        Returns:
            dict[str, object]: Removal status and explicit data-retention flag.

        Raises:
            KeyError: If the workspace is absent or not GlossWise-enabled.
        """
        with self._lock:
            spec = self._require_glosswise(workspace_id)
            removed = WorkspaceSpec.unregister(
                spec.id,
                context=self.context,
            )
            self._opened.pop(spec.id, None)
            return {
                "removed": spec.id if removed else None,
                "data_retained": True,
            }

    def open(
        self,
        workspace_id: str | None = None,
        *,
        ensure_default: bool = True,
    ) -> Any:
        """Open and prepare one live GlossWise workspace.

        Args:
            workspace_id (str | None): Explicit id, or active/default
                resolution when omitted.
            ensure_default (bool): Whether absence creates the managed default.

        Returns:
            Any: Live extension-enabled HeavenBase workspace.
        """
        spec = self._resolve_spec(
            workspace_id,
            ensure_default=ensure_default,
        )
        return self._open_spec(spec)

    def info(
        self,
        workspace_id: str | None = None,
        *,
        ensure_default: bool = True,
    ) -> dict[str, object]:
        """Open one workspace and return its redacted GlossWise capabilities.

        Args:
            workspace_id (str | None): Explicit id or active/default selection.
            ensure_default (bool): Whether absence creates the managed default.

        Returns:
            dict[str, object]: Workspace summary plus GlossWise capabilities.
        """
        workspace = self.open(
            workspace_id,
            ensure_default=ensure_default,
        )
        return {
            **self.get(workspace.id),
            "capabilities": workspace.glosswise.info(),
        }

    def health(
        self,
        workspace_id: str | None = None,
        *,
        ensure_default: bool = True,
    ) -> dict[str, object]:
        """Return registry and redacted runtime health.

        Args:
            workspace_id (str | None): Explicit id or active/default selection.
            ensure_default (bool): Whether absence creates the managed default.

        Returns:
            dict[str, object]: Registry summary and runtime entity/backend
                identities without database paths.
        """
        workspace = self.open(
            workspace_id,
            ensure_default=ensure_default,
        )
        runtime = workspace.health()
        backends = [{key: backend[key] for key in ("name", "type", "provider") if key in backend} for backend in runtime.get("backends", [])]
        return {
            "registered": self.get(workspace.id),
            "runtime": {
                "workspace": workspace.id,
                "entities": runtime.get("entities", []),
                "backends": backends,
            },
        }

    def manifest(
        self,
        workspace_id: str | None = None,
    ) -> dict[str, object]:
        """Export an explicit HeavenBase construction/schema manifest.

        Manifest export is an advanced operation and intentionally includes
        replayable backend construction details.

        Args:
            workspace_id (str | None): Explicit id or active/default selection.

        Returns:
            dict[str, object]: HeavenBase workspace manifest.
        """
        return self.open(workspace_id).to_manifest()

    def import_manifest(
        self,
        path: str | Path,
        *,
        activate: bool = True,
    ) -> dict[str, object]:
        """Import a HeavenBase manifest and ensure GlossWise is enabled.

        Args:
            path (str | Path): JSON or YAML workspace manifest path.
            activate (bool): Whether to select the imported workspace.

        Returns:
            dict[str, object]: Redacted imported-workspace summary.
        """
        self._ensure_installed()
        manifest = WorkspaceManifest.load(str(path))
        workspace = manifest.open(context=self.context)
        workspace.enable_extension("glosswise")
        setup_workspace(workspace)
        self._opened[workspace.id] = workspace
        if activate:
            self.context.activate_workspace(workspace.id)
        return self.get(workspace.id)

    def mcp_config(
        self,
        *,
        profile: str | None = None,
        server_name: str = "glosswise",
        command: str = "glosswise",
        transport: str = "stdio",
        host: str = DEFAULT_MCP_HOST,
        port: int = DEFAULT_MCP_PORT,
    ) -> dict[str, object]:
        """Build MCP client JSON for the global workspace directory.

        Args:
            profile (str | None): Optional advanced restriction profile.
                Supported values are `full`, `read`, and `local`. Omit it for
                the default full surface.
            server_name (str): Key below the standard `mcpServers` object.
            command (str): Executable available to the MCP client.
            transport (str): MCP connection style. Supported values:
                - `stdio`: Launch `glosswise mcp` as a local child process.
                - `http`: Connect to streamable HTTP at `/mcp`.
                - `streamable-http`: Explicit streamable HTTP alias at `/mcp`.
                - `sse`: Connect to the legacy SSE endpoint at `/sse`.
            host (str): MCP server host used by network transports.
            port (int): MCP server port used by network transports.

        Returns:
            dict[str, object]: Paste-ready MCP client configuration.

        Raises:
            ValueError: If the profile, server name, transport, host, or port
                is invalid.
        """
        selected_profile = str(profile or "").strip()
        if selected_profile and selected_profile not in _PROFILES:
            expected = ", ".join(_PROFILES)
            raise ValueError(f"GlossWise MCP profile must be one of {expected}; got {profile!r}.")
        selected_name = str(server_name).strip()
        if not selected_name:
            raise ValueError("MCP server name must not be blank.")
        selected_transport = str(transport).strip().lower()
        if selected_transport not in _MCP_TRANSPORTS:
            expected = ", ".join(_MCP_TRANSPORTS)
            raise ValueError(f"GlossWise MCP transport must be one of {expected}; got {transport!r}.")
        selected_host = str(host).strip()
        if not selected_host:
            raise ValueError("MCP host must not be blank.")
        if "://" in selected_host or "/" in selected_host:
            raise ValueError(f"MCP host must be a hostname or address without a URL scheme or path; got {host!r}.")
        selected_port = int(port)
        if not 1 <= selected_port <= 65535:
            raise ValueError(f"MCP port must be from 1 through 65535; got {port!r}.")
        if selected_transport != "stdio":
            path = "sse" if selected_transport == "sse" else "mcp"
            url_host = f"[{selected_host}]" if ":" in selected_host and not selected_host.startswith("[") else selected_host
            return {
                "mcpServers": {
                    selected_name: {
                        "transport": selected_transport,
                        "url": f"http://{url_host}:{selected_port}/{path}",
                    }
                }
            }
        args = ["mcp"]
        if selected_profile:
            args.extend(["--profile", selected_profile])
        if self.bootstrap is not None:
            args.extend(["--bootstrap", self.bootstrap])
        return {
            "mcpServers": {
                selected_name: {
                    "command": str(command),
                    "args": args,
                }
            }
        }

    def close(self) -> None:
        """Close this directory's Context exactly once when owned.

        Args:
            None.

        Returns:
            None: Owned resources are retired.
        """
        if not self._closed and self.owns_context:
            self.context.close()
        self._closed = True

    def __enter__(self) -> "GlossWiseWorkspaces":
        """Enter this directory as a context manager.

        Args:
            None.

        Returns:
            GlossWiseWorkspaces: This open directory.
        """
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Close this directory after a context-managed operation.

        Args:
            exc_type (type[BaseException] | None): Active exception class.
            exc (BaseException | None): Active exception instance.
            traceback (TracebackType | None): Active exception traceback.

        Returns:
            None: Owned resources are retired.
        """
        del exc_type, exc, traceback
        self.close()

    def _resolve_spec(
        self,
        workspace_id: str | None,
        *,
        ensure_default: bool,
    ) -> WorkspaceSpec:
        if workspace_id is not None and str(workspace_id).strip():
            return self._require_glosswise(str(workspace_id))
        active_id = self.context.active_workspace_id
        if active_id is not None:
            active = self._load_spec(active_id)
            if active is not None and self._is_glosswise(active):
                return active
        default = self._load_spec(DEFAULT_WORKSPACE_ID)
        if default is not None:
            if not self._is_glosswise(default):
                raise KeyError(f"Workspace {DEFAULT_WORKSPACE_ID!r} exists but is not GlossWise-enabled.")
            return default
        if ensure_default:
            self.create(DEFAULT_WORKSPACE_ID, activate=True)
            return self._require_glosswise(DEFAULT_WORKSPACE_ID)
        raise KeyError("No active or default GlossWise workspace. Run `glosswise ws create`.")

    def _require_glosswise(self, workspace_id: str) -> WorkspaceSpec:
        clean_id = check_workspace_id(str(workspace_id))
        spec = self._load_spec(clean_id)
        if spec is None or not self._is_glosswise(spec):
            raise KeyError(f"No registered GlossWise workspace {clean_id!r}.")
        return spec

    def _ensure_installed(self) -> None:
        rows = self.context.modules().inspect("extension", "glosswise")
        version = str(rows[0]["record"].get("meta", {}).get("version", "")) if rows else ""
        from .. import __version__

        if version != __version__:
            install(self.context)

    def _load_spec(self, workspace_id: str) -> WorkspaceSpec | None:
        try:
            return WorkspaceSpec.load(
                workspace_id,
                context=self.context,
            )
        except KeyError:
            return None

    def _open_spec(self, spec: WorkspaceSpec) -> Any:
        with self._lock:
            self._ensure_installed()
            cached = self._opened.get(spec.id)
            if cached is not None:
                return cached
            if tuple(spec.extension_roots or ()) == ("glosswise",):
                workspace = spec.open_detached(context=self.context)
            else:
                with self._minimal_defaults(spec.id):
                    workspace = hb.HeavenBase(
                        spec.id,
                        context=self.context,
                        detached=True,
                        **spec.config,
                    )
            workspace.enable_extension("glosswise")
            setup_workspace(workspace)
            self._opened[spec.id] = workspace
            return workspace

    @contextmanager
    def _minimal_defaults(self, workspace_id: str) -> Iterator[None]:
        """Temporarily suppress unrelated default extensions during open."""
        scope = f"{self.context.config.base_scope}.{workspace_id}"
        with self.context.config.scoped(scope):
            current = self.context.config.get(
                "heavenbase.extensions.default",
                default=[],
            )
        changed = tuple(current or ()) != ()
        temporary_version: int | None = None
        if changed:
            self.context.config.set(
                "heavenbase.extensions.default",
                [],
                scope=scope,
            )
            latest = self.context.config.history(scope=scope, limit=1)
            if not latest:
                raise RuntimeError("HeavenBase did not retain the temporary config layer.")
            temporary_version = int(latest[0]["ver"])
        try:
            yield
        finally:
            if temporary_version is not None:
                removed = self.context.config.remove(
                    scope=scope,
                    version=temporary_version,
                )
                if not removed:
                    raise RuntimeError("HeavenBase did not remove the temporary config layer.")

    @staticmethod
    def _is_glosswise(spec: WorkspaceSpec) -> bool:
        return "glosswise" in tuple(spec.extension_roots or ())

    def _summary(self, spec: WorkspaceSpec) -> dict[str, object]:
        return {
            "id": spec.id,
            "active": self.context.active_workspace_id == spec.id,
            "created_at": spec.created_at,
            "updated_at": spec.updated_at,
            "extensions": list(spec.extension_roots or ()),
            "profiles": list(_PROFILES),
            "default_languages": self._default_languages(spec.id),
            "storage": ("managed" if self._uses_managed_storage(spec) else "external"),
        }

    def _default_languages(self, workspace_id: str) -> list[str]:
        scope = f"{self.context.config.base_scope}.{workspace_id}"
        with self.context.config.scoped(scope):
            value = self.context.config.get(
                DEFAULT_LANGUAGES_CONFIG_KEY,
                default=[],
            )
        return canonicalize_languages(value or ())

    @staticmethod
    def _uses_managed_storage(spec: WorkspaceSpec) -> bool:
        try:
            backends = spec.config.get("backends", {})
            main = backends.get("main", {})
            return str(main.get("type", "")).strip().lower() == "sqlite" and str(main.get("database", "")) == managed_database_path(spec.id).as_uri()
        except (AttributeError, RuntimeError, TypeError, ValueError):
            return False
