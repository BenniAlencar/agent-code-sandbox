# Architecture — `agent-code-sandbox`

`agent-code-sandbox` follows the **Benni Master OS v9.4** modular three-tier package layout:

1. **`core/` (Execution & Security Primitives)**
   - `ast_guard.py`: Sub-millisecond static AST security scanner blocking forbidden imports (`os`, `subprocess`, `socket`, `ctypes`), reflective escapes (`__subclasses__`, `getattr`), and `eval`/`exec`/`open` abuse.
   - `workspace.py`: Ephemeral temporary directory lifecycle with SHA-256 pre/post snapshotting and atomic file diffing.
   - `token_shield.py`: Adaptive head/tail stdout/stderr truncation preventing LLM context blowouts.
   - `engine.py`: `SandboxEngine` orchestrating AST verification, subprocess isolation, timeout enforcement, and workspace diffing.

2. **`serve/` (Runtime Interfaces & Observability)**
   - `mcp_bridge.py`: Native JSON-RPC 2.0 stdio Model Context Protocol server (`execute_python`, `execute_command`, `inspect_code_security`).
   - `telemetry.py`: Thread-safe rolling P50/P90/P99 latency, block-rate, and token-savings collector.
   - `health_monitor.py`: Runtime health probe checking temp storage writability, free disk space, and AST guard integrity.
   - `__main__.py`: Unified CLI entrypoint (`run`, `check`, `mcp`, `benchmark`, `doctor`, `matrix`, `health`).

3. **`tools/` (Diagnostics & Benchmarks)**
   - `doctor.py`: End-to-end diagnostic probe (`SandboxDoctor`) with structured JSON and human-readable reports.
   - `bench_matrix.py`: Multi-workload latency & token-savings matrix (`BenchmarkMatrix`).
