"""Benchmark script comparing AST scan and ephemeral sandbox startup against container baselines."""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from agent_code_sandbox.tools import BenchmarkMatrix


def main() -> None:
    matrix = BenchmarkMatrix()
    rows = matrix.run(reps=2)
    print(matrix.format_table(rows))


if __name__ == "__main__":
    main()
