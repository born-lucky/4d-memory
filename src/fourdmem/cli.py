"""Agent-facing harness. Same idea as Math-Verify: call it, it works."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from fourdmem import __version__
from fourdmem.api import Store
from fourdmem.store.kinds import Kind


def _store(args: argparse.Namespace) -> Store:
    root = Path(args.store) if args.store else Path.cwd() / ".fourdmem"
    return Store(root)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="fourdmem",
        description=(
            "4D memory harness: two kinds (good/bad) judged against the "
            "goal at store time. Default recall is the plan, unclouded."
        ),
    )
    parser.add_argument("--version", action="version", version=f"fourdmem {__version__}")
    parser.add_argument(
        "--store",
        default=None,
        help="store root (default: ./.fourdmem)",
    )
    sub = parser.add_subparsers(dest="cmd", required=False)

    sub.add_parser("status", help="goal, good count, bad count")

    p_goal = sub.add_parser("goal", help="set the creating prompt / plan")
    p_goal.add_argument("text")

    p_store = sub.add_parser("store", help="store a note; auto-kind vs creating goal")
    p_store.add_argument("text")
    p_store.add_argument("--title", default=None)
    p_store.add_argument("--kind", choices=["good", "bad"], default=None)
    p_store.add_argument("--mnemonic", default=None)

    p_judge = sub.add_parser("judge", help="retie: good joins the plan, bad is untied")
    p_judge.add_argument("oid")
    p_judge.add_argument("kind", choices=["good", "bad"])

    p_recall = sub.add_parser("recall", help="default: good of the current plan")
    p_recall.add_argument("--kind", choices=["good", "bad"], default="good")

    p_cas = sub.add_parser("cas", help="lossless retrieve (even bad stays)")
    p_cas.add_argument("oid")

    sub.add_parser("mcp", help="stdio MCP server (Grok / Claude / Cursor)")

    p_mv = sub.add_parser("harness", help="lab tools: math-verify, lean")
    p_mv.add_argument("tool", choices=["math-verify", "lean"])
    p_mv.add_argument("--gold", default=None)
    p_mv.add_argument("--answer", default=None)
    p_mv.add_argument("--lean-cmd", dest="lean_cmd", default=None, help="Lean command, e.g. def f := 2")

    args = parser.parse_args(argv)
    cmd = args.cmd or "status"

    if cmd == "mcp":
        from fourdmem.agent.mcp import serve

        serve(_store(args))
        return 0

    if cmd == "harness":
        if args.tool == "math-verify":
            from fourdmem.harness.math_verify import verify_pair

            if not args.gold or not args.answer:
                print("math-verify needs --gold and --answer", file=sys.stderr)
                return 2
            ok = verify_pair(args.gold, args.answer)
            print("true" if ok else "false")
            return 0 if ok else 1
        if args.tool == "lean":
            from fourdmem.harness.lean_repl import run_cmd as lean_cmd

            if not args.lean_cmd:
                print("lean needs --lean-cmd", file=sys.stderr)
                return 2
            print(json.dumps(lean_cmd(args.lean_cmd)))
            return 0

    st = _store(args)

    if cmd == "status":
        print(json.dumps(st.status(), indent=2))
        return 0

    if cmd == "goal":
        oid = st.set_goal(args.text)
        print(oid)
        return 0

    if cmd == "store":
        mem = st.store(
            args.text,
            title=args.title,
            kind=Kind(args.kind) if args.kind else None,
            landmark=args.mnemonic,
        )
        print(f"{mem.kind} {mem.oid} w={mem.w} {mem.title}")
        return 0

    if cmd == "judge":
        mem = st.judge(args.oid, Kind(args.kind))
        print(f"{mem.kind} {mem.oid} w={mem.w}")
        return 0

    if cmd == "recall":
        sys.stdout.write(st.recall(kind=Kind(args.kind)))
        return 0

    if cmd == "cas":
        sys.stdout.buffer.write(st.cas_get(args.oid))
        return 0

    print(f"unknown command: {cmd}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
