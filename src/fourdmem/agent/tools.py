"""MCP tool table. Always the same names — never toggled on/off (K6)."""

from __future__ import annotations

from typing import Any, Callable

from fourdmem.api import Store
from fourdmem.store.kinds import Kind

# Frozen list. Adding a tool is a design change; removing one is forbidden.
TOOL_NAMES: tuple[str, ...] = (
    "fourdmem_goal",
    "fourdmem_store",
    "fourdmem_judge",
    "fourdmem_recall",
    "fourdmem_cas",
    "fourdmem_status",
    "fourdmem_math_verify",
    "fourdmem_lean",
)


def _schema(properties: dict, required: list[str] | None = None) -> dict:
    return {
        "type": "object",
        "properties": properties,
        "required": required or [],
        "additionalProperties": False,
    }


TOOL_DEFS: list[dict] = [
    {
        "name": "fourdmem_goal",
        "description": (
            "Set the creating plan. Kind (good/bad) is judged against THIS "
            "text at store time, not against later prompts."
        ),
        "inputSchema": _schema({"text": {"type": "string"}}, ["text"]),
    },
    {
        "name": "fourdmem_store",
        "description": (
            "Store a note under the current plan. Auto-classifies good vs bad "
            "from the creating goal. Bad is kept but NOT tied to the plan. "
            "Default recall will not show bad."
        ),
        "inputSchema": _schema(
            {
                "text": {"type": "string"},
                "title": {"type": "string"},
                "kind": {"type": "string", "enum": ["good", "bad"]},
                "mnemonic": {"type": "string"},
            },
            ["text"],
        ),
    },
    {
        "name": "fourdmem_judge",
        "description": "Retie a memory: good joins the plan; bad is untied (not deleted).",
        "inputSchema": _schema(
            {
                "oid": {"type": "string"},
                "kind": {"type": "string", "enum": ["good", "bad"]},
            },
            ["oid", "kind"],
        ),
    },
    {
        "name": "fourdmem_recall",
        "description": (
            "Recall the plan. Default kind=good (unclouded). "
            "kind=bad is explicit junk inspection. Never rewrite chat history; "
            "this tool result is the only injection."
        ),
        "inputSchema": _schema(
            {
                "kind": {"type": "string", "enum": ["good", "bad"], "default": "good"},
                "goal": {"type": "string"},
            }
        ),
    },
    {
        "name": "fourdmem_cas",
        "description": "Lossless retrieve by oid. Works for good and bad.",
        "inputSchema": _schema({"oid": {"type": "string"}}, ["oid"]),
    },
    {
        "name": "fourdmem_status",
        "description": "Current goal, good count, bad count, store root.",
        "inputSchema": _schema({}),
    },
    {
        "name": "fourdmem_math_verify",
        "description": "HuggingFace Math-Verify: is answer the same math as gold?",
        "inputSchema": _schema(
            {"gold": {"type": "string"}, "answer": {"type": "string"}},
            ["gold", "answer"],
        ),
    },
    {
        "name": "fourdmem_lean",
        "description": "Lean 4 REPL command (JSON). Example: def f := 2",
        "inputSchema": _schema({"cmd": {"type": "string"}}, ["cmd"]),
    },
]


def _mem_brief(mem) -> dict:
    return {
        "oid": mem.oid,
        "kind": mem.kind,
        "w": mem.w,
        "title": mem.title,
        "coord": mem.coord,
        "goal_at_store": mem.goal_at_store,
        "landmark": mem.landmark,
    }


def dispatch(store: Store, name: str, arguments: dict[str, Any] | None) -> Any:
    args = arguments or {}
    if name == "fourdmem_goal":
        oid = store.set_goal(args["text"])
        return {"oid": oid, "goal": store.goal}
    if name == "fourdmem_store":
        kind = args.get("kind")
        mem = store.store(
            args["text"],
            title=args.get("title"),
            kind=Kind(kind) if kind else None,
            landmark=args.get("mnemonic"),
        )
        return _mem_brief(mem)
    if name == "fourdmem_judge":
        mem = store.judge(args["oid"], Kind(args["kind"]))
        return _mem_brief(mem)
    if name == "fourdmem_recall":
        kind = Kind(args.get("kind") or "good")
        text = store.recall(kind=kind, goal=args.get("goal"))
        return {"kind": kind.value, "text": text}
    if name == "fourdmem_cas":
        body = store.cas_get(args["oid"])
        return {"oid": args["oid"], "text": body.decode("utf-8")}
    if name == "fourdmem_status":
        return store.status()
    if name == "fourdmem_math_verify":
        from fourdmem.harness.math_verify import verify_pair

        ok = verify_pair(args["gold"], args["answer"])
        return {"ok": ok}
    if name == "fourdmem_lean":
        from fourdmem.harness.lean_repl import run_cmd

        return run_cmd(args["cmd"])
    raise KeyError(f"unknown tool: {name}")


HANDLERS: dict[str, Callable] = {n: dispatch for n in TOOL_NAMES}
