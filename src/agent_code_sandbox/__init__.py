"""
agent-code-sandbox: Micro-Second Zero-Dependency Code Sandbox & Execution Shield
Part of Benni Master OS v9.4 ecosystem.
"""

from .core import (
    ASTSecurityScanner,
    EphemeralWorkspace,
    ExecutionResult,
    SandboxEngine,
    SecurityCheckResult,
    ShieldedOutput,
    TokenShield,
    WorkspaceDiff,
)
from .serve import HealthMonitor, HealthSnapshot, SandboxTelemetry
from .tools import BenchmarkMatrix, DoctorReport, MatrixRow, SandboxDoctor

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
    "HealthMonitor",
    "HealthSnapshot",
    "SandboxTelemetry",
    "SandboxDoctor",
    "DoctorReport",
    "BenchmarkMatrix",
    "MatrixRow",
    "__version__",
]
