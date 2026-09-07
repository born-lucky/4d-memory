"""MCP tools always listed; recall is a tool result; prefix stays frozen."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from fourdmem.agent.live_zone import LiveZoneError, append_tool_result, assert_prefix_frozen
from fourdmem.agent.mcp import handle
from fourdmem.agent.tools import TOOL_NAMES, dispatch
from fourdmem.api import Store

GOAL = "prove Hilbert 4D encode/decode is bijective"
HILBERT = "Hilbert encode/decode is a bijection on Lattice4."
CATS = "I saw cats on screen."


def _store(tmp_path: Path) -> Store:
    return Store(tmp_path / ".fourdmem")


def test_tools_list_is_frozen_and_complete(tmp_path: Path) -> None:
    st = _store(tmp_path)
    r1 = handle(st, {"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
    r2 = handle(st, {"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
    names1 = [t["name"] for t in r1["result"]["tools"]]
    names2 = [t["name"] for t in r2["result"]["tools"]]
    assert tuple(names1) == TOOL_NAMES
    assert names1 == names2


def test_initialize_advertises_stable_tools(tmp_path: Path) -> None:
    st = _store(tmp_path)
    r = handle(st, {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
    caps = r["result"]["capabilities"]
    assert caps["tools"]["listChanged"] is False
    assert "fourdmem" in r["result"]["serverInfo"]["name"]


def test_mcp_work_loop_cats_untied(tmp_path: Path) -> None:
    st = _store(tmp_path)
    dispatch(st, "fourdmem_goal", {"text": GOAL})
    good = dispatch(st, "fourdmem_store", {"text": HILBERT, "title": "Hilbert bijection"})
    bad = dispatch(st, "fourdmem_store", {"text": CATS, "title": "cats on screen"})
    assert good["kind"] == "good"
    assert bad["kind"] == "bad"
    recalled = dispatch(st, "fourdmem_recall", {})
    assert "Hilbert" in recalled["text"]
    assert "cats" not in recalled["text"].lower()
    blob = dispatch(st, "fourdmem_cas", {"oid": bad["oid"]})
    assert "cats" in blob["text"].lower()


def test_mcp_tools_call_jsonrpc(tmp_path: Path) -> None:
    st = _store(tmp_path)
    handle(
        st,
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {"name": "fourdmem_goal", "arguments": {"text": GOAL}},
        },
    )
    r = handle(
        st,
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "fourdmem_store",
                "arguments": {"text": HILBERT},
            },
        },
    )
    body = json.loads(r["result"]["content"][0]["text"])
    assert body["kind"] == "good"
    assert r["result"]["isError"] is False


def test_mcp_math_verify_tool(tmp_path: Path) -> None:
    st = _store(tmp_path)
    r = handle(
        st,
        {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "fourdmem_math_verify",
                "arguments": {"gold": "1/2", "answer": "0.5"},
            },
        },
    )
    body = json.loads(r["result"]["content"][0]["text"])
    assert body["ok"] is True


def test_resource_plan_is_good_only(tmp_path: Path) -> None:
    st = _store(tmp_path)
    dispatch(st, "fourdmem_goal", {"text": GOAL})
    dispatch(st, "fourdmem_store", {"text": HILBERT})
    dispatch(st, "fourdmem_store", {"text": CATS})
    r = handle(
        st,
        {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "resources/read",
            "params": {"uri": "fourdmem://plan"},
        },
    )
    text = r["result"]["contents"][0]["text"]
    assert "Hilbert" in text
    assert "cats" not in text.lower()


def test_live_zone_refuses_prefix_rewrite() -> None:
    original = [{"role": "system", "content": "stay"}, {"role": "user", "content": "hi"}]
    assert_prefix_frozen(original, original + [{"role": "assistant", "content": "ok"}])
    with pytest.raises(LiveZoneError):
        assert_prefix_frozen(original, [{"role": "system", "content": "rewritten"}])
    with pytest.raises(LiveZoneError):
        assert_prefix_frozen(original, [original[0]])


def test_content_length_initialize_roundtrip() -> None:
    import os
    import subprocess
    import sys
    from pathlib import Path

    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path(__file__).resolve().parents[1] / "src")
    env["PYTHONUNBUFFERED"] = "1"
    init = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test", "version": "0"},
        },
    }
    blob = json.dumps(init).encode()
    framed = f"Content-Length: {len(blob)}\r\n\r\n".encode() + blob
    proc = subprocess.run(
        [sys.executable, "-u", "-m", "fourdmem.agent.mcp"],
        input=framed,
        capture_output=True,
        timeout=10,
        env=env,
        cwd=str(Path(__file__).resolve().parents[1]),
    )
    assert b'"name":"fourdmem"' in proc.stdout or b'"name": "fourdmem"' in proc.stdout, proc.stderr


def test_append_tool_result_keeps_prefix() -> None:
    original = [{"role": "user", "content": "prove it"}]
    out = append_tool_result(original, {"role": "tool", "content": "Hilbert oid"})
    assert out[0] == original[0]
    assert len(out) == 2
