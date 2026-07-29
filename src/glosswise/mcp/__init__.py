"""Workspace-bound and global MCP adapters for GlossWise."""

from __future__ import annotations

__all__ = [
    "GENERIC_FULL_TOOL_NAMES",
    "GENERIC_LOCAL_TOOL_NAMES",
    "GENERIC_READ_TOOL_NAMES",
    "GLOSSWISE_TOOL_NAMES",
    "generic_tool_functions",
    "generic_toolkit",
    "glosswise_tool_functions",
]

from .factory import GLOSSWISE_TOOL_NAMES, glosswise_tool_functions
from .generic import (
    GENERIC_FULL_TOOL_NAMES,
    GENERIC_LOCAL_TOOL_NAMES,
    GENERIC_READ_TOOL_NAMES,
    generic_tool_functions,
    generic_toolkit,
)
