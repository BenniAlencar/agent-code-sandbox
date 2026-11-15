"""Security gate runner verifying AST guardrails and runtime health."""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from agent_code_sandbox.tools import SandboxDoctor


def main() -> None:
    report = SandboxDoctor().run()
    print(report.format_report())
    if not report.overall_ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
