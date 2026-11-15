"""Backwards-compatible shim for agent_code_sandbox.core.ast_guard."""

from .core.ast_guard import ASTSecurityScanner, SecurityCheckResult

__all__ = ["ASTSecurityScanner", "SecurityCheckResult"]
