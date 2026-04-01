#!/usr/bin/env python3
"""Diff exported symbols between two shared libraries."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare exported symbols of two SO files"
    )
    parser.add_argument("--old", required=True, help="Old .so path")
    parser.add_argument("--new", required=True, help="New .so path")
    parser.add_argument("-o", "--output", help="Write report to file")
    parser.add_argument(
        "--only-added", action="store_true", help="Print only added symbols"
    )
    parser.add_argument(
        "--only-removed", action="store_true", help="Print only removed symbols"
    )
    return parser.parse_args()


def run_cmd(cmd: list[str]) -> str:
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(
            proc.stderr.strip() or proc.stdout.strip() or "command failed"
        )
    return proc.stdout


def extract_symbols(so_file: Path) -> set[str]:
    commands = [
        ["nm", "-D", "--defined-only", str(so_file)],
        ["objdump", "-T", str(so_file)],
    ]
    output = ""
    last_err = ""
    for cmd in commands:
        try:
            output = run_cmd(cmd)
            break
        except Exception as exc:  # pylint: disable=broad-except
            last_err = str(exc)
    if not output:
        raise RuntimeError(f"failed to extract symbols (nm/objdump): {last_err}")

    symbols: set[str] = set()
    for line in output.splitlines():
        line = line.strip()
        if not line:
            continue
        token = line.split()[-1]
        if token.startswith("_") or token[0].isalpha():
            symbols.add(token)
    return symbols


def main() -> int:
    args = parse_args()
    old_file = Path(args.old)
    new_file = Path(args.new)

    if not old_file.exists() or not new_file.exists():
        print("error: old/new file must both exist", file=sys.stderr)
        return 2
    if old_file.suffix != ".so" or new_file.suffix != ".so":
        print("error: both files must be .so", file=sys.stderr)
        return 2

    try:
        old_syms = extract_symbols(old_file)
        new_syms = extract_symbols(new_file)
    except Exception as exc:  # pylint: disable=broad-except
        print(f"error: {exc}", file=sys.stderr)
        return 2

    added = sorted(new_syms - old_syms)
    removed = sorted(old_syms - new_syms)
    common = len(old_syms & new_syms)

    lines: list[str] = []
    lines.append(f"old: {old_file}")
    lines.append(f"new: {new_file}")
    lines.append(f"added: {len(added)}")
    lines.append(f"removed: {len(removed)}")
    lines.append(f"common: {common}")

    if not args.only_removed:
        lines.append("\n[ADDED]")
        lines.extend(added or ["(none)"])
    if not args.only_added:
        lines.append("\n[REMOVED]")
        lines.extend(removed or ["(none)"])

    report = "\n".join(lines) + "\n"
    if args.output:
        Path(args.output).write_text(report, encoding="utf-8")
    else:
        print(report, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
