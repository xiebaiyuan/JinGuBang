#!/usr/bin/env python3
"""Show top N largest files in a directory."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def parse_size(size_text: str) -> int:
    size_text = size_text.strip().upper()
    suffixes = {"K": 1024, "M": 1024**2, "G": 1024**3}
    if size_text[-1:] in suffixes:
        return int(float(size_text[:-1]) * suffixes[size_text[-1]])
    return int(size_text)


def human_size(size: int) -> str:
    units = ["B", "KB", "MB", "GB", "TB"]
    value = float(size)
    for unit in units:
        if value < 1024 or unit == units[-1]:
            return f"{value:.2f}{unit}" if unit != "B" else f"{int(value)}B"
        value /= 1024
    return f"{size}B"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="List largest files")
    parser.add_argument("-i", "--input", required=True, help="Directory path")
    parser.add_argument("-n", type=int, default=20, help="Top N files")
    parser.add_argument("--min-size", default="0", help="Minimum size, e.g. 10M")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    base = Path(args.input)
    if not base.is_dir():
        print(f"error: input is not a directory: {base}", file=sys.stderr)
        return 2

    min_size = parse_size(args.min_size)
    rows: list[tuple[int, Path]] = []
    for p in base.rglob("*"):
        if p.is_file():
            sz = p.stat().st_size
            if sz >= min_size:
                rows.append((sz, p))

    rows.sort(reverse=True, key=lambda x: x[0])
    print(f"input: {base}")
    print(f"total_candidates: {len(rows)}")
    print("\nTOP FILES")
    for idx, (sz, p) in enumerate(rows[: args.n], start=1):
        print(f"{idx:>3}. {human_size(sz):>10}  {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
