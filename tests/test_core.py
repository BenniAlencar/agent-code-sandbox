import pytest
from agent_code_sandbox.core import SandboxEngine, ExecutionResult


def test_execute_safe_python_code():
    engine = SandboxEngine()
    code = "import math\nprint(f'PI={math.pi:.4f}')"
    res = engine.execute_python(code=code)
    assert res.exit_code == 0
    assert "PI=3.1416" in res.stdout
    assert res.is_safe is True
    assert res.timed_out is False
    assert res.execution_time_ms > 0


def test_execute_blocked_unsafe_python_code():
    engine = SandboxEngine()
    unsafe_code = "import os\nos.system('echo hacked')"
    res = engine.execute_python(code=unsafe_code)
    assert res.exit_code == -1
    assert res.is_safe is False
    assert "SecurityViolationError" in res.stderr
    assert len(res.violations) > 0


def test_execute_python_with_timeout():
    engine = SandboxEngine()
    # Code that runs an infinite loop
    loop_code = "import time\nwhile True:\n    pass"
    res = engine.execute_python(code=loop_code, timeout=0.5)
    assert res.timed_out is True
    assert res.exit_code == -124
    assert "TimeoutExpired" in res.stderr


def test_execute_command():
    engine = SandboxEngine()
    res = engine.execute_command("python -c \"print('Hello from shell')\"")
    assert res.exit_code == 0
    assert "Hello from shell" in res.stdout
