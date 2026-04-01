#!/usr/bin/env python3
"""Show top processes by CPU or memory usage."""

from __future__ import annotations

import argparse
import subprocess
import sys
import time


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Display top processes")
    parser.add_argument(
        "--by", choices=("cpu", "mem"), default="cpu", help="Sort by CPU or memory"
    )
    parser.add_argument("-n", type=int, default=10, help="Top N rows")
    parser.add_argument(
        "--interval", type=float, default=0.0, help="Repeat interval seconds (0 = once)"
    )
    return parser.parse_args()


def get_rows(sort_by: str) -> list[str]:
    if sort_by == "cpu":
        sort_flag = "-r"
    else:
        sort_flag = "-m"
    cmd = ["ps", "-axo", "pid,pcpu,pmem,rss,comm", sort_flag]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or "ps failed")
    return [x for x in proc.stdout.splitlines() if x.strip()]


def print_top(rows: list[str], topn: int) -> None:
    if not rows:
        return
    print(rows[0])
    for row in rows[1 : topn + 1]:
        print(row)


def main() -> int:
    args = parse_args()
    try:
        if args.interval <= 0:
            print_top(get_rows(args.by), args.n)
            return 0

        while True:
            print(f"\n=== by={args.by} top={args.n} ===")
            print_top(get_rows(args.by), args.n)
            print("(Ctrl+C to stop)")
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\nstopped")
        return 0
    except Exception as exc:  # pylint: disable=broad-except
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
