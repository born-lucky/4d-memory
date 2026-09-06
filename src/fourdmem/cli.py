"""CLI stub. Palace verbs land with the PR plan in docs/DESIGN.md."""

from __future__ import annotations

import argparse
import sys

from fourdmem import __version__


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="fourdmem",
        description="4D memory harness: a mnemonic palace on a Z^4 lattice.",
    )
    parser.add_argument("--version", action="version", version=f"fourdmem {__version__}")
    sub = parser.add_subparsers(dest="cmd")
    sub.add_parser("status", help="print version and point at the design")
    args = parser.parse_args(argv)

    if args.cmd in (None, "status"):
        print(f"fourdmem {__version__}")
        print("status: design complete; implementation follows docs/DESIGN.md")
        print("math:   docs/MATH.md")
        return 0

    print(f"unknown command: {args.cmd}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
