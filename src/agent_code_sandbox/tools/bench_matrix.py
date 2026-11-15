"""
Multi-workload automated benchmark matrix for agent-code-sandbox.
Measures AST scan latency, sandbox execution latency, and token shield savings across workloads.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from ..core.ast_guard import ASTSecurityScanner
from ..core.engine import SandboxEngine
from ..core.token_shield import TokenShield


@dataclass
class MatrixRow:
    workload: str
    ast_scan_ms: float
    exec_ms: float
    tokens_saved: int
    is_safe: bool
    speedup_vs_docker: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "workload": self.workload,
            "ast_scan_ms": round(self.ast_scan_ms, 3),
            "exec_ms": round(self.exec_ms, 2),
            "tokens_saved": self.tokens_saved,
            "is_safe": self.is_safe,
            "speedup_vs_docker": round(self.speedup_vs_docker, 1),
        }


DEFAULT_WORKLOADS: Dict[str, str] = {
    "hello_math": "import math\nprint(math.factorial(12))\n",
    "prime_sieve": (
        "primes = [n for n in range(2, 200) if all(n % d != 0 for d in range(2, int(n**0.5) + 1))]\n"
        "print(len(primes))\n"
    ),
    "runaway_stdout": "for i in range(600):\n    print(f'log_entry_{i:04d}_payload_data')\n",
    "blocked_exploit": "import os\nos.system('whoami')\n",
}


class BenchmarkMatrix:
    """Runs a reproducible multi-workload latency and token-savings matrix."""

    DOCKER_COLD_START_MS = 3200.0

    def __init__(self, token_shield_max_chars: int = 1200) -> None:
        self.scanner = ASTSecurityScanner()
        self.engine = SandboxEngine(token_shield=TokenShield(max_chars=token_shield_max_chars))

    def run(self, workloads: Optional[Dict[str, str]] = None, reps: int = 1) -> List[MatrixRow]:
        suite = workloads or DEFAULT_WORKLOADS
        rows: List[MatrixRow] = []
        reps = max(1, int(reps))

        for name, code in suite.items():
            ast_total = 0.0
            exec_total = 0.0
            last_res = None
            for _ in range(reps):
                t0 = time.perf_counter()
                self.scanner.scan(code)
                ast_total += (time.perf_counter() - t0) * 1000.0

                t1 = time.perf_counter()
                last_res = self.engine.execute_python(code, timeout=5.0)
                exec_total += (time.perf_counter() - t1) * 1000.0

            avg_ast = ast_total / reps
            avg_exec = max(0.01, exec_total / reps)
            tokens_saved = (last_res.shielded_metrics or {}).get("tokens_saved", 0) if last_res else 0
            is_safe = last_res.is_safe if last_res else False
            rows.append(
                MatrixRow(
                    workload=name,
                    ast_scan_ms=avg_ast,
                    exec_ms=avg_exec,
                    tokens_saved=tokens_saved,
                    is_safe=is_safe,
                    speedup_vs_docker=self.DOCKER_COLD_START_MS / avg_exec,
                )
            )
        return rows

    @staticmethod
    def format_table(rows: List[MatrixRow]) -> str:
        header = f"{'Workload':<18} | {'AST (ms)':>9} | {'Exec (ms)':>9} | {'Tokens Saved':>12} | {'Safe':>5} | {'vs Docker':>10}"
        sep = "-" * len(header)
        lines = [header, sep]
        for r in rows:
            lines.append(
                f"{r.workload:<18} | {r.ast_scan_ms:9.3f} | {r.exec_ms:9.2f} | "
                f"{r.tokens_saved:12d} | {str(r.is_safe):>5} | {r.speedup_vs_docker:8.1f}x"
            )
        return "\n".join(lines)
