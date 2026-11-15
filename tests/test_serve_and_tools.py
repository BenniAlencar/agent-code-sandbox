"""Unit tests for agent_code_sandbox.serve and agent_code_sandbox.tools."""

from agent_code_sandbox import (
    BenchmarkMatrix,
    HealthMonitor,
    SandboxDoctor,
    SandboxTelemetry,
)


def test_sandbox_telemetry_percentiles_and_counts():
    tel = SandboxTelemetry(max_events=50)
    tel.record("python", 10.0, is_safe=True, exit_code=0, tokens_saved=120)
    tel.record("python", 30.0, is_safe=False, exit_code=-1, tokens_saved=0)
    tel.record("command", 20.0, is_safe=True, exit_code=0, timed_out=True, tokens_saved=80)

    snap = tel.snapshot()
    assert snap["total_executions"] == 3
    assert snap["blocked_count"] == 1
    assert snap["timeout_count"] == 1
    assert snap["tokens_saved_total"] == 200
    assert snap["latency_ms"]["p50"] == 20.0
    assert snap["latency_ms"]["p90"] >= 20.0

    tel.reset()
    assert tel.snapshot()["total_executions"] == 0


def test_health_monitor_reports_healthy():
    snap = HealthMonitor().check()
    data = snap.to_dict()
    assert snap.status == "healthy"
    assert data["temp_writable"] is True
    assert data["ast_guard_ok"] is True


def test_sandbox_doctor_all_checks_pass():
    report = SandboxDoctor().run()
    assert report.overall_ok is True
    assert len(report.checks) == 4
    text = report.format_report()
    assert "ALL CHECKS PASSED" in text
    assert report.to_dict()["overall_ok"] is True


def test_benchmark_matrix_runs_workloads():
    matrix = BenchmarkMatrix(token_shield_max_chars=300)
    rows = matrix.run(
        workloads={
            "simple": "print(1 + 1)",
            "blocked": "import os; os.system('echo hi')",
        },
        reps=1,
    )
    assert len(rows) == 2
    assert rows[0].is_safe is True
    assert rows[1].is_safe is False
    table = matrix.format_table(rows)
    assert "simple" in table and "blocked" in table
