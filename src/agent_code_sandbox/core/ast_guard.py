"""
Pre-Execution Static AST Security Scanner (Tier-0 Guardrail).
Inspects Abstract Syntax Trees in sub-millisecond latency to halt dangerous code before execution.
"""

from __future__ import annotations

import ast
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Set


@dataclass
class SecurityCheckResult:
    is_safe: bool
    violations: List[str] = field(default_factory=list)
    latency_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_safe": self.is_safe,
            "violations": self.violations,
            "latency_ms": round(self.latency_ms, 3),
        }


class ASTSecurityScanner(ast.NodeVisitor):
    """
    Scans Python AST to detect unsafe imports, syscalls, reflective breakouts,
    and filesystem tampering.
    """

    FORBIDDEN_MODULES: Set[str] = {
        "os", "sys", "subprocess", "shutil", "socket", "ctypes", "builtins",
        "importlib", "pty", "commands", "posix", "nt", "signal", "multiprocessing",
        "threading", "asyncio", "inspect"
    }

    FORBIDDEN_CALLS: Set[str] = {
        "eval", "exec", "compile", "open", "__import__", "globals", "locals",
        "breakpoint", "exit", "quit"
    }

    FORBIDDEN_ATTRIBUTES: Set[str] = {
        "__subclasses__", "__bases__", "__mro__", "__globals__", "__code__",
        "__closure__", "__dict__", "__class__"
    }

    def __init__(self, allowed_modules: Set[str] | None = None) -> None:
        self.violations: List[str] = []
        self.allowed_modules = allowed_modules or {"math", "random", "re", "json", "time", "datetime", "collections", "itertools", "functools", "heapq", "bisect", "typing"}

    def scan(self, code: str) -> SecurityCheckResult:
        t0 = time.perf_counter()
        self.violations.clear()

        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            elapsed = (time.perf_counter() - t0) * 1000.0
            return SecurityCheckResult(
                is_safe=False,
                violations=[f"SyntaxError: {str(e)}"],
                latency_ms=elapsed,
            )

        self.visit(tree)
        elapsed = (time.perf_counter() - t0) * 1000.0
        return SecurityCheckResult(
            is_safe=len(self.violations) == 0,
            violations=list(self.violations),
            latency_ms=elapsed,
        )

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            base_module = alias.name.split(".")[0]
            if base_module in self.FORBIDDEN_MODULES or base_module not in self.allowed_modules:
                self.violations.append(f"Forbidden import: '{alias.name}' (line {node.lineno})")
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.module:
            base_module = node.module.split(".")[0]
            if base_module in self.FORBIDDEN_MODULES or base_module not in self.allowed_modules:
                self.violations.append(f"Forbidden from-import: '{node.module}' (line {node.lineno})")
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        if isinstance(node.func, ast.Name):
            if node.func.id in self.FORBIDDEN_CALLS:
                self.violations.append(f"Forbidden function call: '{node.func.id}()' (line {node.lineno})")
        elif isinstance(node.func, ast.Attribute):
            if node.func.attr in self.FORBIDDEN_CALLS:
                self.violations.append(f"Forbidden method call: '{node.func.attr}()' (line {node.lineno})")
            if node.func.attr in self.FORBIDDEN_ATTRIBUTES:
                self.violations.append(f"Forbidden reflective attribute call: '{node.func.attr}' (line {node.lineno})")
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        if node.attr in self.FORBIDDEN_ATTRIBUTES:
            self.violations.append(f"Forbidden reflective attribute access: '{node.attr}' (line {node.lineno})")
        self.generic_visit(node)
