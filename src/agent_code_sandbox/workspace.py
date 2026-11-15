"""Backwards-compatible shim for agent_code_sandbox.core.workspace."""

from .core.workspace import EphemeralWorkspace, WorkspaceDiff

__all__ = ["EphemeralWorkspace", "WorkspaceDiff"]
