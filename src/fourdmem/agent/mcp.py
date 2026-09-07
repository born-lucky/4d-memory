"""Stdio MCP server for fourdmem.

Inspired by:
- @modelcontextprotocol/server-memory (always-on tools + a resource)
- agent-memory-mcp / mcp-memory-service (store / recall / stats, local-first)
- Headroom CCR (retrieve by hash; never rewrite the prefix; tools do not flip)

Protocol: JSON-RPC 2.0 over stdio, MCP Content-Length framing with NDJSON fallback.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, TextIO

from fourdmem import __version__
from fourdmem.agent.tools import TOOL_DEFS, TOOL_NAMES, dispatch
from fourdmem.api import Store

SERVER_NAME = "fourdmem"
PROTOCOL_VERSION = "2024-11-05"

INSTRUCTIONS = (
    "fourdmem is a 4D memory harness. Set a goal, then store notes. "
    "Kind (good/bad) is judged against the goal at store time, not the live prompt. "
    "Default fourdmem_recall returns only the plan (good). Bad is kept in CAS but "
    "not tied to the plan — do not dump it into the prompt. "
    "Never rewrite earlier chat turns; use the tool result as the only injection."
)


def make_store(root: str | None = None) -> Store:
    path = root or os.environ.get("FOURDMEM_STORE")
    return Store(Path(path) if path else Path.cwd() / ".fourdmem")


def handle(store: Store, message: dict[str, Any]) -> dict[str, Any] | None:
    """One JSON-RPC message in, one response out (None = notification)."""
    mid = message.get("id")
    method = message.get("method")
    params = message.get("params") or {}
    client_proto = params.get("protocolVersion") if method == "initialize" else None

    if method is None:
        return _err(mid, -32600, "invalid request")

    if method == "notifications/initialized":
        return None
    if method == "ping":
        return _ok(mid, {})

    if method == "initialize":
        return _ok(
            mid,
            {
                "protocolVersion": client_proto or PROTOCOL_VERSION,
                "serverInfo": {"name": SERVER_NAME, "version": __version__},
                "capabilities": {
                    "tools": {"listChanged": False},
                    "resources": {"listChanged": False},
                    "prompts": {},
                },
                "instructions": INSTRUCTIONS,
            },
        )

    if method == "tools/list":
        return _ok(mid, {"tools": TOOL_DEFS})

    if method == "tools/call":
        name = params.get("name")
        arguments = params.get("arguments") or {}
        if name not in TOOL_NAMES:
            return _ok(
                mid,
                {
                    "content": [{"type": "text", "text": f"unknown tool: {name}"}],
                    "isError": True,
                },
            )
        try:
            result = dispatch(store, name, arguments)
        except Exception as exc:  # noqa: BLE001 — surface to the agent
            return _ok(
                mid,
                {
                    "content": [{"type": "text", "text": f"{type(exc).__name__}: {exc}"}],
                    "isError": True,
                },
            )
        text = result if isinstance(result, str) else json.dumps(result, indent=2)
        return _ok(mid, {"content": [{"type": "text", "text": text}], "isError": False})

    if method == "resources/list":
        return _ok(
            mid,
            {
                "resources": [
                    {
                        "uri": "fourdmem://status",
                        "name": "status",
                        "mimeType": "application/json",
                        "description": "goal, good/bad counts",
                    },
                    {
                        "uri": "fourdmem://plan",
                        "name": "plan",
                        "mimeType": "text/plain",
                        "description": "current plan good-recall (unclouded)",
                    },
                ]
            },
        )

    if method == "resources/read":
        uri = params.get("uri", "")
        if uri == "fourdmem://status":
            body = json.dumps(store.status(), indent=2)
            mime = "application/json"
        elif uri == "fourdmem://plan":
            body = store.recall()
            mime = "text/plain"
        else:
            return _err(mid, -32602, f"unknown resource {uri}")
        return _ok(
            mid,
            {"contents": [{"uri": uri, "mimeType": mime, "text": body}]},
        )

    if method == "prompts/list":
        return _ok(
            mid,
            {
                "prompts": [
                    {
                        "name": "work_loop",
                        "description": "Use fourdmem during a task: goal, store, recall good only.",
                    }
                ]
            },
        )

    if method == "prompts/get":
        return _ok(
            mid,
            {
                "description": "Work loop",
                "messages": [
                    {
                        "role": "user",
                        "content": {
                            "type": "text",
                            "text": (
                                "Set fourdmem_goal to the current task. "
                                "Store notes with fourdmem_store. "
                                "Recall with fourdmem_recall (default good). "
                                "Do not put bad memories in the prompt. "
                                "Do not rewrite earlier turns."
                            ),
                        },
                    }
                ],
            },
        )

    if method.startswith("notifications/"):
        return None
    return _err(mid, -32601, f"method not found: {method}")


def _ok(mid: Any, result: Any) -> dict:
    return {"jsonrpc": "2.0", "id": mid, "result": result}


def _err(mid: Any, code: int, message: str) -> dict:
    return {"jsonrpc": "2.0", "id": mid, "error": {"code": code, "message": message}}


def _stdio_binary() -> None:
    if sys.platform != "win32":
        return
    try:
        import msvcrt

        msvcrt.setmode(sys.stdin.fileno(), os.O_BINARY)
        msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)
    except (AttributeError, OSError, ValueError):
        pass


def _raw(stream):
    return stream.buffer if hasattr(stream, "buffer") else stream


def _read(stdin, framing: dict) -> dict | None:
    """Content-Length framing, else one NDJSON line. Remember how the client speaks."""
    raw_in = _raw(stdin)
    first = raw_in.readline()
    if not first:
        return None
    header = first.decode("utf-8", errors="replace")
    if header.lower().startswith("content-length:"):
        framing["mode"] = "cl"
        n = int(header.split(":", 1)[1].strip())
        while True:
            line = raw_in.readline()
            if line in (b"\r\n", b"\n", b""):
                break
        body = raw_in.read(n)
        return json.loads(body.decode("utf-8"))
    framing["mode"] = "ndjson"
    line = header.strip()
    if not line:
        return _read(stdin, framing)
    return json.loads(line)


def _write(msg: dict, stdout: TextIO, framing: dict) -> None:
    blob = json.dumps(msg, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    out = _raw(stdout)
    if framing.get("mode") == "ndjson":
        out.write(blob + b"\n")
    else:
        out.write(f"Content-Length: {len(blob)}\r\n\r\n".encode("ascii") + blob)
    out.flush()


def serve(store: Store | None = None, stdin=None, stdout=None) -> None:
    _stdio_binary()
    st = store or make_store()
    inn = stdin or sys.stdin
    out = stdout or sys.stdout
    framing = {"mode": "cl"}
    while True:
        try:
            msg = _read(inn, framing)
        except json.JSONDecodeError as exc:
            _write(_err(None, -32700, f"parse error: {exc}"), out, framing)
            continue
        except ValueError as exc:
            _write(_err(None, -32700, str(exc)), out, framing)
            continue
        if msg is None:
            break
        reply = handle(st, msg)
        if reply is not None:
            _write(reply, out, framing)


def main(argv: list[str] | None = None) -> int:
    serve()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
