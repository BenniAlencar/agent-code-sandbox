"""Demonstrates AST pre-execution blocking, token shielding, and telemetry."""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from agent_code_sandbox import ASTSecurityScanner, SandboxEngine, SandboxTelemetry


def main() -> None:
    scanner = ASTSecurityScanner()
    engine = SandboxEngine()
    telemetry = SandboxTelemetry()

    malicious = "import os; os.system('whoami')"
    check = scanner.scan(malicious)
    print("Malicious safe?:", check.is_safe, "| Violations:", check.violations)

    res = engine.execute_python(malicious)
    telemetry.record("python", res.execution_time_ms, is_safe=res.is_safe, exit_code=res.exit_code)

    safe_res = engine.execute_python("for i in range(400): print(f'line-{i}')")
    tokens_saved = (safe_res.shielded_metrics or {}).get("tokens_saved", 0)
    telemetry.record(
        "python",
        safe_res.execution_time_ms,
        is_safe=safe_res.is_safe,
        exit_code=safe_res.exit_code,
        tokens_saved=tokens_saved,
    )

    print("Telemetry Snapshot:", telemetry.snapshot())


if __name__ == "__main__":
    main()
