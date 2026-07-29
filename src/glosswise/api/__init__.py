"""Application-facing GlossWise lifecycle and curation API."""

from __future__ import annotations

__all__ = [
    "DEFAULT_WORKSPACE_ID",
    "TranslationService",
    "GlossWiseApp",
    "GlossWiseWorkspaces",
    "managed_database_path",
]

from .app import GlossWiseApp
from .translation import TranslationService
from .workspaces import (
    DEFAULT_WORKSPACE_ID,
    GlossWiseWorkspaces,
    managed_database_path,
)
