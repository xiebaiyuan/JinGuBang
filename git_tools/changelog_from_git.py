#!/usr/bin/env python3
"""Generate a lightweight changelog from git history."""

from __future__ import annotations

import argparse
import subprocess
import sys
from collections import defaultdict
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate changelog from git log")
    parser.add_argument("--from", dest="from_ref", required=True, help="Start ref")
    parser.add_argument("--to", dest="to_ref", required=True, help="End ref")
    parser.add_argument("-o", "--output", help="Output file")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    cmd = ["git", "log", "--pretty=%s", f"{args.from_ref}..{args.to_ref}"]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        print(
            f"error: {proc.stderr.strip() or 'failed to read git log'}", file=sys.stderr
        )
        return 2

    lines = [x.strip() for x in proc.stdout.splitlines() if x.strip()]
    groups: dict[str, list[str]] = defaultdict(list)
    for line in lines:
        prefix = line.split(":", maxsplit=1)[0]
        if "(" in prefix and ")" in prefix:
            prefix = prefix.split("(", maxsplit=1)[0]
        if prefix in {"feat", "fix", "docs", "refactor", "test", "chore", "perf"}:
            groups[prefix].append(line)
        else:
            groups["others"].append(line)

    order = ["feat", "fix", "docs", "refactor", "test", "perf", "chore", "others"]
    out_lines = [f"# Changelog ({args.from_ref}..{args.to_ref})", ""]
    for key in order:
        entries = groups.get(key)
        if not entries:
            continue
        out_lines.append(f"## {key}")
        out_lines.extend([f"- {item}" for item in entries])
        out_lines.append("")
    result = "\n".join(out_lines).rstrip() + "\n"

    if args.output:
        Path(args.output).write_text(result, encoding="utf-8")
    else:
        print(result, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
