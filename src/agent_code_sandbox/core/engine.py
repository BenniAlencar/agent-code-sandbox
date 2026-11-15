"""
Core Sandbox Execution Engine.
Orchestrates pre-execution AST validation, ephemeral process isolation, and output shielding.
"""

from __future__ import annotations

import os
import subprocess
import sys
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .ast_guard import ASTSecurityScanner, SecurityCheckResult
from .token_shield import ShieldedOutput, TokenShield
from .workspace import EphemeralWorkspace, WorkspaceDiff


@dataclass
class ExecutionResult:
    exit_code: int
    stdout: str
    stderr: str
    execution_time_ms: float
    is_safe: bool
    violations: List[str] = field(default_factory=list)
    diff: Optional[WorkspaceDiff] = None
    shielded_metrics: Optional[Dict[str, Any]] = None
    timed_out: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "exit_code": self.exit_code,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "execution_time_ms": round(self.execution_time_ms, 3),
            "is_safe": self.is_safe,
            "violations": self.violations,
            "diff": self.diff.to_dict() if self.diff else None,
            "shielded_metrics": self.shielded_metrics,
            "timed_out": self.timed_out,
        }


class SandboxEngine:
    """
    Sub-millisecond secure code execution engine for autonomous AI agents.
    """

    def __init__(
        self,
        ast_scanner: Optional[ASTSecurityScanner] = None,
        token_shield: Optional[TokenShield] = None,
    ) -> None:
        self.ast_scanner = ast_scanner or ASTSecurityScanner()
        self.token_shield = token_shield or TokenShield()

    def execute_python(
        self,
        code: str,
        timeout: float = 5.0,
        allow_unsafe_ast: bool = False,
        initial_files: Optional[Dict[str, str]] = None,
    ) -> ExecutionResult:
        """
        Executes Python code safely within an ephemeral scratchpad after AST verification.
        """
        t0 = time.perf_counter()

        # 1. Pre-Execution AST Static Analysis
        if not allow_unsafe_ast:
            sec_check = self.ast_scanner.scan(code)
            if not sec_check.is_safe:
                elapsed = (time.perf_counter() - t0) * 1000.0
                violations_msg = "\n".join(f"[BLOCKED] {v}" for v in sec_check.violations)
                return ExecutionResult(
                    exit_code=-1,
                    stdout="",
                    stderr=f"SecurityViolationError: Code execution halted by agent-code-sandbox AST Guardrail.\n{violations_msg}",
                    execution_time_ms=elapsed,
                    is_safe=False,
                    violations=sec_check.violations,
                )

        # 2. Ephemeral Workspace Setup
        with EphemeralWorkspace() as ws:
            if initial_files:
                for rel_path, content in initial_files.items():
                    ws.write_file(rel_path, content)
            ws.snapshot_initial_state()

            script_path = ws.write_file("__sandbox_main__.py", code)

            # 3. Subprocess Execution
            timed_out = False
            try:
                proc = subprocess.run(
                    [sys.executable, script_path],
                    cwd=ws.workspace_dir,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                )
                raw_stdout = proc.stdout
                raw_stderr = proc.stderr
                exit_code = proc.returncode
            except subprocess.TimeoutExpired as te:
                timed_out = True
                raw_stdout = te.stdout or "" if isinstance(te.stdout, str) else ""
                raw_stderr = f"TimeoutExpired: Execution exceeded hard limit of {timeout:.1f}s."
                exit_code = -124

            elapsed = (time.perf_counter() - t0) * 1000.0

            # 4. Token Shielding & Output Truncation
            shielded_out = self.token_shield.shield(raw_stdout)
            shielded_err = self.token_shield.shield(raw_stderr)

            # 5. Compute Workspace Diff
            diff = ws.compute_diff()
            # Exclude the script itself from the diff
            if "__sandbox_main__.py" in diff.added_files:
                diff.added_files.remove("__sandbox_main__.py")

            return ExecutionResult(
                exit_code=exit_code,
                stdout=shielded_out.text,
                stderr=shielded_err.text,
                execution_time_ms=elapsed,
                is_safe=True,
                diff=diff,
                shielded_metrics={
                    "tokens_saved": shielded_out.tokens_saved_est + shielded_err.tokens_saved_est,
                    "stdout_truncated": shielded_out.was_truncated,
                },
                timed_out=timed_out,
            )

    def execute_command(
        self,
        command: str,
        timeout: float = 5.0,
        initial_files: Optional[Dict[str, str]] = None,
    ) -> ExecutionResult:
        """
        Executes terminal commands within an isolated ephemeral workspace.
        """
        t0 = time.perf_counter()

        with EphemeralWorkspace() as ws:
            if initial_files:
                for rel_path, content in initial_files.items():
                    ws.write_file(rel_path, content)
            ws.snapshot_initial_state()

            timed_out = False
            try:
                proc = subprocess.run(
                    command,
                    cwd=ws.workspace_dir,
                    capture_output=True,
                    text=True,
                    shell=True,
                    timeout=timeout,
                )
                raw_stdout = proc.stdout
                raw_stderr = proc.stderr
                exit_code = proc.returncode
            except subprocess.TimeoutExpired as te:
                timed_out = True
                raw_stdout = te.stdout or "" if isinstance(te.stdout, str) else ""
                raw_stderr = f"TimeoutExpired: Execution exceeded hard limit of {timeout:.1f}s."
                exit_code = -124

            elapsed = (time.perf_counter() - t0) * 1000.0

            shielded_out = self.token_shield.shield(raw_stdout)
            shielded_err = self.token_shield.shield(raw_stderr)
            diff = ws.compute_diff()

            return ExecutionResult(
                exit_code=exit_code,
                stdout=shielded_out.text,
                stderr=shielded_err.text,
                execution_time_ms=elapsed,
                is_safe=True,
                diff=diff,
                shielded_metrics={
                    "tokens_saved": shielded_out.tokens_saved_est + shielded_err.tokens_saved_est,
                    "stdout_truncated": shielded_out.was_truncated,
                },
                timed_out=timed_out,
            )
