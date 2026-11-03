import pytest
from agent_code_sandbox.core import SandboxEngine


def test_mcp_inspection_logic():
    engine = SandboxEngine()
    safe_check = engine.ast_scanner.scan("print('Safe')")
    assert safe_check.is_safe is True

    unsafe_check = engine.ast_scanner.scan("import socket\ns = socket.socket()")
    assert unsafe_check.is_safe is False
    assert any("socket" in v for v in unsafe_check.violations)
