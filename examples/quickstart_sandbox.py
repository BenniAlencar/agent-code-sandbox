"""Minimal quickstart example for agent-code-sandbox."""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from agent_code_sandbox import SandboxEngine


def main() -> None:
    engine = SandboxEngine()
    result = engine.execute_python(
        code=(
            "import json, math\n"
            "payload = {'factorial_12': math.factorial(12), 'sqrt_144': math.sqrt(144)}\n"
            "print(json.dumps(payload))\n"
        ),
        timeout=3.0,
    )
    print("Exit Code:", result.exit_code)
    print("Stdout:", result.stdout.strip())
    print(f"Latency: {result.execution_time_ms:.2f} ms")


if __name__ == "__main__":
    main()
