import pytest
from agent_code_sandbox.token_shield import TokenShield, ShieldedOutput


def test_token_shield_short_output_passthrough():
    shield = TokenShield(max_lines=50, max_chars=4000)
    raw = "Line 1: Hello World\nLine 2: Success\n"
    res = shield.shield(raw)
    assert res.was_truncated is False
    assert res.text == raw
    assert res.tokens_saved_est == 0


def test_token_shield_truncation_with_banner():
    shield = TokenShield(max_lines=20, max_chars=500, head_ratio=0.5)
    raw = "".join([f"Line {i}: Log event payload testing\n" for i in range(100)])
    res = shield.shield(raw)
    assert res.was_truncated is True
    assert res.tokens_saved_est > 0
    assert "Output Truncated by agent-code-sandbox" in res.text
    assert res.text.startswith("Line 0:")
    assert res.text.strip().endswith("Line 99: Log event payload testing")
