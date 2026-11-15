"""
Runtime health monitor for agent-code-sandbox.
Verifies Python interpreter availability, ephemeral temp storage, and AST guard readiness.
"""

from __future__ import annotations

import os
import platform
import shutil
import sys
import tempfile
import time
from dataclasses import dataclass
from typing import Any, Dict

from ..core.ast_guard import ASTSecurityScanner


@dataclass
class HealthSnapshot:
    status: str  # "healthy" | "degraded" | "unhealthy"
    python_version: str
    platform_system: str
    temp_dir: str
    temp_free_mb: float
    temp_writable: bool
    ast_guard_ok: bool
    check_latency_ms: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "python_version": self.python_version,
            "platform_system": self.platform_system,
            "temp_dir": self.temp_dir,
            "temp_free_mb": round(self.temp_free_mb, 2),
            "temp_writable": self.temp_writable,
            "ast_guard_ok": self.ast_guard_ok,
            "check_latency_ms": round(self.check_latency_ms, 3),
        }


class HealthMonitor:
    """Performs lightweight runtime health checks for the sandbox subsystem."""

    def __init__(self, min_free_mb: float = 50.0) -> None:
        self.min_free_mb = min_free_mb

    def check(self) -> HealthSnapshot:
        t0 = time.perf_counter()
        tmp_dir = tempfile.gettempdir()
        usage = shutil.disk_usage(tmp_dir)
        free_mb = usage.free / (1024.0 * 1024.0)

        temp_writable = False
        try:
            with tempfile.NamedTemporaryFile(dir=tmp_dir, prefix="acs_health_", delete=True) as fh:
                fh.write(b"ok")
                fh.flush()
                temp_writable = True
        except OSError:
            temp_writable = False

        ast_ok = False
        try:
            scanner = ASTSecurityScanner()
            safe_res = scanner.scan("x = 1 + 2")
            unsafe_res = scanner.scan("import os; os.system('id')")
            ast_ok = safe_res.is_safe and (not unsafe_res.is_safe)
        except Exception:
            ast_ok = False

        if not temp_writable or not ast_ok:
            status = "unhealthy"
        elif free_mb < self.min_free_mb:
            status = "degraded"
        else:
            status = "healthy"

        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        return HealthSnapshot(
            status=status,
            python_version=platform.python_version(),
            platform_system=f"{platform.system()} {platform.release()}",
            temp_dir=tmp_dir,
            temp_free_mb=free_mb,
            temp_writable=temp_writable,
            ast_guard_ok=ast_ok,
            check_latency_ms=elapsed_ms,
        )
