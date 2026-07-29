"""Terminology-safe translation context for AI agents."""

from __future__ import annotations

__all__ = [
    "GlossWiseError",
    "DEFAULT_WORKSPACE_ID",
    "GlossWiseApp",
    "GlossWiseService",
    "GlossWiseWorkspaces",
    "HeavenBaseEmbedder",
    "__version__",
    "install",
    "install_agent_skill",
    "install_agent_skills",
    "is_glosswise_error",
    "managed_database_path",
    "setup_workspace",
]

__version__ = "0.1.0.5"

from .errors import GlossWiseError, is_glosswise_error
from .embedding import HeavenBaseEmbedder
from .api import (
    DEFAULT_WORKSPACE_ID,
    GlossWiseApp,
    GlossWiseWorkspaces,
    managed_database_path,
)
from .lifecycle import (
    install,
    install_agent_skill,
    install_agent_skills,
    setup_workspace,
)
from .service import GlossWiseService
