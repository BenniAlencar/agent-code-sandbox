"""
Diagnostic probe (doctor) for agent-code-sandbox.
Validates AST guardrails, ephemeral workspace isolation, subprocess execution, and token shielding.
"""

from __future__ import annotations

import platform
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List

from ..core.ast_guard import ASTSecurityScanner
from ..core.engine import SandboxEngine
from ..core.token_shield import TokenShield
from ..serve.health_monitor import HealthMonitor


@dataclass
class ProbeCheck:
    name: str
    passed: bool
    latency_ms: float
    detail: str


@dataclass
class DoctorReport:
    overall_ok: bool
    python_version: str
    platform_info: str
    checks: List[ProbeCheck] = field(default_factory=list)
    total_latency_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_ok": self.overall_ok,
            "python_version": self.python_version,
            "platform": self.platform_info,
            "total_latency_ms": round(self.total_latency_ms, 3),
            "checks": [
                {
                    "name": c.name,
                    "passed": c.passed,
                    "latency_ms": round(c.latency_ms, 3),
                    "detail": c.detail,
                }
                for c in self.checks
            ],
        }

    def format_report(self) -> str:
        lines = [
            f"agent-code-sandbox doctor | Python {self.python_version} | {self.platform_info}",
            "-" * 72,
        ]
        for c in self.checks:
            tag = "[PASS]" if c.passed else "[FAIL]"
            lines.append(f"{tag} {c.name:<28} {c.latency_ms:7.3f} ms  {c.detail}")
        lines.append("-" * 72)
        status = "ALL CHECKS PASSED" if self.overall_ok else "DEGRADED / CHECKS FAILED"
        lines.append(f"Status: {status} ({self.total_latency_ms:.2f} ms total)")
        return "\n".join(lines)


class SandboxDoctor:
    """Runs end-to-end diagnostic probes on the local sandbox environment."""

    def run(self) -> DoctorReport:
        t_start = time.perf_counter()
        checks: List[ProbeCheck] = []

        # 1. HealthMonitor probe
        t0 = time.perf_counter()
        health = HealthMonitor().check()
        checks.append(
            ProbeCheck(
                name="runtime_health",
                passed=health.status == "healthy",
                latency_ms=(time.perf_counter() - t0) * 1000.0,
                detail=f"status={health.status}, free_tmp={health.temp_free_mb:.0f}MB",
            )
        )

        # 2. AST Security Scanner probe
        t0 = time.perf_counter()
        scanner = ASTSecurityScanner()
        safe = scanner.scan("import math\nprint(math.sqrt(16))")
        blocked = scanner.scan("import subprocess; subprocess.run(['ls'])")
        ast_ok = safe.is_safe and (not blocked.is_safe)
        checks.append(
            ProbeCheck(
                name="ast_security_guard",
                passed=ast_ok,
                latency_ms=(time.perf_counter() - t0) * 1000.0,
                detail=f"safe_ok={safe.is_safe}, exploit_blocked={not blocked.is_safe}",
            )
        )

        # 3. Ephemeral Sandbox Execution probe
        t0 = time.perf_counter()
        engine = SandboxEngine()
        res = engine.execute_python("print('doctor_ok')", timeout=3.0)
        exec_ok = res.exit_code == 0 and "doctor_ok" in res.stdout
        checks.append(
            ProbeCheck(
                name="ephemeral_execution",
                passed=exec_ok,
                latency_ms=(time.perf_counter() - t0) * 1000.0,
                detail=f"exit_code={res.exit_code}, exec_ms={res.execution_time_ms:.2f}",
            )
        )

        # 4. Token Shield probe
        t0 = time.perf_counter()
        shield = TokenShield(max_chars=200)
        long_text = "\n".join(f"line {i}: payload" for i in range(100))
        shielded = shield.shield(long_text)
        shield_ok = shielded.was_truncated and shielded.tokens_saved_est > 0
        checks.append(
            ProbeCheck(
                name="adaptive_token_shield",
                passed=shield_ok,
                latency_ms=(time.perf_counter() - t0) * 1000.0,
                detail=f"truncated={shielded.was_truncated}, tokens_saved={shielded.tokens_saved_est}",
            )
        )

        overall_ok = all(c.passed for c in checks)
        total_ms = (time.perf_counter() - t_start) * 1000.0
        return DoctorReport(
            overall_ok=overall_ok,
            python_version=platform.python_version(),
            platform_info=f"{platform.system()} {platform.release()}",
            checks=checks,
            total_latency_ms=total_ms,
        )
