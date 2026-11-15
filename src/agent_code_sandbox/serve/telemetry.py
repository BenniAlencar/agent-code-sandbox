"""
Rolling telemetry collector for agent-code-sandbox.
Tracks P50/P90/P99 execution latency, AST scan overhead, blocked exploits, and token savings.
"""

from __future__ import annotations

import threading
import time
from collections import deque
from dataclasses import dataclass
from typing import Any, Deque, Dict, List


def _percentile(sorted_vals: List[float], pct: float) -> float:
    if not sorted_vals:
        return 0.0
    if len(sorted_vals) == 1:
        return sorted_vals[0]
    idx = (len(sorted_vals) - 1) * (pct / 100.0)
    lo = int(idx)
    hi = min(lo + 1, len(sorted_vals) - 1)
    frac = idx - lo
    return sorted_vals[lo] * (1.0 - frac) + sorted_vals[hi] * frac


@dataclass
class ExecutionEvent:
    timestamp: float
    kind: str  # "python" | "command" | "ast_scan"
    latency_ms: float
    is_safe: bool
    exit_code: int
    timed_out: bool
    tokens_saved: int = 0


class SandboxTelemetry:
    """Thread-safe rolling window telemetry for sandbox executions."""

    def __init__(self, max_events: int = 1000) -> None:
        self._events: Deque[ExecutionEvent] = deque(maxlen=max_events)
        self._lock = threading.Lock()
        self._total_executions = 0
        self._total_blocked = 0
        self._total_timeouts = 0
        self._total_tokens_saved = 0

    def record(
        self,
        kind: str,
        latency_ms: float,
        is_safe: bool = True,
        exit_code: int = 0,
        timed_out: bool = False,
        tokens_saved: int = 0,
    ) -> None:
        event = ExecutionEvent(
            timestamp=time.time(),
            kind=kind,
            latency_ms=max(0.0, float(latency_ms)),
            is_safe=is_safe,
            exit_code=exit_code,
            timed_out=timed_out,
            tokens_saved=max(0, int(tokens_saved)),
        )
        with self._lock:
            self._events.append(event)
            self._total_executions += 1
            if not is_safe:
                self._total_blocked += 1
            if timed_out:
                self._total_timeouts += 1
            self._total_tokens_saved += event.tokens_saved

    def snapshot(self) -> Dict[str, Any]:
        with self._lock:
            latencies = sorted(e.latency_ms for e in self._events)
            total = self._total_executions
            blocked = self._total_blocked
            timeouts = self._total_timeouts
            tokens_saved = self._total_tokens_saved
            window_count = len(self._events)

        return {
            "total_executions": total,
            "window_events": window_count,
            "blocked_count": blocked,
            "timeout_count": timeouts,
            "block_rate_pct": round((blocked / total) * 100.0, 2) if total else 0.0,
            "tokens_saved_total": tokens_saved,
            "latency_ms": {
                "p50": round(_percentile(latencies, 50.0), 3),
                "p90": round(_percentile(latencies, 90.0), 3),
                "p99": round(_percentile(latencies, 99.0), 3),
                "mean": round(sum(latencies) / len(latencies), 3) if latencies else 0.0,
            },
        }

    def reset(self) -> None:
        with self._lock:
            self._events.clear()
            self._total_executions = 0
            self._total_blocked = 0
            self._total_timeouts = 0
            self._total_tokens_saved = 0
