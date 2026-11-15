"""
Model Context Protocol (MCP) Server for agent-code-sandbox.
Provides secure code and command execution primitives to Claude Code, Cursor, and Benni OS.
"""

from __future__ import annotations

import json
import sys
from typing import Any, Dict

from ..core import SandboxEngine


def run_stdio() -> None:
    """Standard JSON-RPC 2.0 stdio server loop for Model Context Protocol."""
    engine = SandboxEngine()

    while True:
        line = sys.stdin.readline()
        if not line:
            break

        line = line.strip()
        if not line:
            continue

        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            continue

        req_id = req.get("id")
        method = req.get("method")
        params = req.get("params", {})

        if method == "initialize":
            resp = {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {
                        "name": "agent-code-sandbox",
                        "version": "1.0.0",
                    },
                },
            }
            sys.stdout.write(json.dumps(resp) + "\n")
            sys.stdout.flush()

        elif method == "notifications/initialized":
            pass

        elif method == "tools/list":
            tools = [
                {
                    "name": "execute_python",
                    "description": "Executes Python code in an isolated ephemeral workspace with AST security analysis and stdout token shielding.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "code": {
                                "type": "string",
                                "description": "Python source code to execute.",
                            },
                            "timeout": {
                                "type": "number",
                                "description": "Maximum execution time in seconds.",
                                "default": 5.0,
                            },
                            "allow_unsafe_ast": {
                                "type": "boolean",
                                "description": "Bypass AST security checks (use with extreme caution).",
                                "default": false,
                            },
                        },
                        "required": ["code"],
                    },
                },
                {
                    "name": "execute_command",
                    "description": "Executes a shell command inside an isolated scratchpad directory with output token shielding.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "command": {
                                "type": "string",
                                "description": "Shell command to run.",
                            },
                            "timeout": {
                                "type": "number",
                                "description": "Execution timeout in seconds.",
                                "default": 5.0,
                            },
                        },
                        "required": ["command"],
                    },
                },
                {
                    "name": "inspect_code_security",
                    "description": "Performs static AST security analysis on Python code without executing it, flagging unsafe imports, syscalls, and reflective escapes.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "code": {
                                "type": "string",
                                "description": "Python code to inspect.",
                            },
                        },
                        "required": ["code"],
                    },
                },
            ]
            resp = {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"tools": tools},
            }
            sys.stdout.write(json.dumps(resp) + "\n")
            sys.stdout.flush()

        elif method == "tools/call":
            name = params.get("name")
            args = params.get("arguments", {})

            try:
                if name == "execute_python":
                    code = args.get("code", "")
                    timeout = float(args.get("timeout", 5.0))
                    allow_unsafe = bool(args.get("allow_unsafe_ast", False))
                    res = engine.execute_python(code=code, timeout=timeout, allow_unsafe_ast=allow_unsafe)
                    text_out = json.dumps(res.to_dict(), indent=2)

                elif name == "execute_command":
                    command = args.get("command", "")
                    timeout = float(args.get("timeout", 5.0))
                    res = engine.execute_command(command=command, timeout=timeout)
                    text_out = json.dumps(res.to_dict(), indent=2)

                elif name == "inspect_code_security":
                    code = args.get("code", "")
                    sec = engine.ast_scanner.scan(code)
                    text_out = json.dumps(sec.to_dict(), indent=2)

                else:
                    text_out = f"Unknown tool: {name}"

                resp = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [{"type": "text", "text": text_out}],
                    },
                }
            except Exception as e:
                resp = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32000, "message": str(e)},
                }

            sys.stdout.write(json.dumps(resp) + "\n")
            sys.stdout.flush()

        elif method == "ping":
            resp = {"jsonrpc": "2.0", "id": req_id, "result": {}}
            sys.stdout.write(json.dumps(resp) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    run_stdio()
