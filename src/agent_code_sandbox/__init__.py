"""
agent-code-sandbox: Micro-Second Zero-Dependency Code Sandbox & Execution Shield
Part of Benni Master OS v9.4 ecosystem.
"""

from .core import SandboxEngine, ExecutionResult
from .ast_guard import ASTSecurityScanner, SecurityCheckResult
from .token_shield import TokenShield, ShieldedOutput
from .workspace import EphemeralWorkspace, WorkspaceDiff

__version__ = "1.0.0"
__author__ = "Benni Alencar"
__email__ = "bennialencar@gmail.com"
__all__ = [
    "SandboxEngine",
    "ExecutionResult",
    "ASTSecurityScanner",
    "SecurityCheckResult",
    "TokenShield",
    "ShieldedOutput",
    "EphemeralWorkspace",
    "WorkspaceDiff",
    "__version__",
]
