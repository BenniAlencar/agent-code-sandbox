"""Backwards-compatible shim for agent_code_sandbox.core.token_shield."""

from .core.token_shield import ShieldedOutput, TokenShield

__all__ = ["ShieldedOutput", "TokenShield"]
