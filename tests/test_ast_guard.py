import pytest
from agent_code_sandbox.ast_guard import ASTSecurityScanner, SecurityCheckResult


def test_safe_python_code():
    scanner = ASTSecurityScanner()
    code = """
import math
import json

def fib(n):
    if n <= 1:
        return n
    return fib(n - 1) + fib(n - 2)

val = fib(10)
print(f"Fib 10 = {val}")
"""
    res = scanner.scan(code)
    assert res.is_safe is True
    assert len(res.violations) == 0
    assert res.latency_ms > 0.0


def test_blocked_os_and_subprocess_imports():
    scanner = ASTSecurityScanner()
    bad_code_1 = "import os\nos.system('calc.exe')"
    res1 = scanner.scan(bad_code_1)
    assert res1.is_safe is False
    assert any("os" in v for v in res1.violations)

    bad_code_2 = "from subprocess import Popen"
    res2 = scanner.scan(bad_code_2)
    assert res2.is_safe is False
    assert any("subprocess" in v for v in res2.violations)


def test_blocked_reflective_escapes():
    scanner = ASTSecurityScanner()
    reflective_code = """
subclasses = ().__class__.__base__.__subclasses__()
for sc in subclasses:
    if 'Popen' in sc.__name__:
        print('Found Popen escape')
"""
    res = scanner.scan(reflective_code)
    assert res.is_safe is False
    assert any("__subclasses__" in v or "__class__" in v or "__base__" in v for v in res.violations)


def test_blocked_eval_and_open():
    scanner = ASTSecurityScanner()
    res1 = scanner.scan("eval('2 + 2')")
    assert res1.is_safe is False
    assert any("eval" in v for v in res1.violations)

    res2 = scanner.scan("f = open('/etc/passwd', 'r')")
    assert res2.is_safe is False
    assert any("open" in v for v in res2.violations)
