#!/usr/bin/env python3
"""Validate commit messages against conventional commit style."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

PATTERN = re.compile(
    r"^(feat|fix|docs|style|refactor|perf|test|build|ci|chore)(\([a-z0-9_\-/]+\))?: .+"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Lint conventional commit messages")
    parser.add_argument("-i", "--input", help="Input file with commit subject per line")
    parser.add_argument(
        "--last", type=int, help="Check last N commit subjects from git log"
    )
    parser.add_argument(
        "--strict", action="store_true", help="Disallow uppercase type/scope"
    )
    return parser.parse_args()


def read_messages(args: argparse.Namespace) -> list[str]:
    if args.input:
        path = Path(args.input)
        if not path.exists():
            raise ValueError(f"input file not found: {path}")
        return [
            line.strip()
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
    if args.last:
        proc = subprocess.run(
            ["git", "log", f"-n{args.last}", "--pretty=%s"],
            capture_output=True,
            text=True,
        )
        if proc.returncode != 0:
            raise ValueError(proc.stderr.strip() or "failed to read git log")
        return [line.strip() for line in proc.stdout.splitlines() if line.strip()]
    raise ValueError("must provide -i/--input or --last")


def validate(msg: str, strict: bool) -> bool:
    if strict and any(ch.isupper() for ch in msg.split(":", maxsplit=1)[0]):
        return False
    return bool(PATTERN.match(msg))


def main() -> int:
    args = parse_args()
    try:
        messages = read_messages(args)
    except Exception as exc:  # pylint: disable=broad-except
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if not messages:
        print("error: no commit messages to lint", file=sys.stderr)
        return 2

    failed: list[str] = [m for m in messages if not validate(m, args.strict)]
    print(f"checked: {len(messages)}")
    print(f"failed: {len(failed)}")
    if failed:
        print("\ninvalid messages:")
        for msg in failed:
            print(f"- {msg}")
        return 1
    print("all commit messages are valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
