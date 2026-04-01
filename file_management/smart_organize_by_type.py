#!/usr/bin/env python3
"""Organize files by extension or modified date with safe defaults."""

from __future__ import annotations

import argparse
import shutil
import sys
from datetime import datetime
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Organize files in a directory")
    parser.add_argument("-i", "--input", required=True, help="Input directory")
    parser.add_argument(
        "-o", "--output", help="Output directory (default: input/organized)"
    )
    parser.add_argument(
        "--by", choices=("ext", "date"), default="ext", help="Organize strategy"
    )
    parser.add_argument("--dry-run", action="store_true", help="Preview actions only")
    parser.add_argument("--apply", action="store_true", help="Apply file moves")
    return parser.parse_args()


def target_subdir(path: Path, mode: str) -> str:
    if mode == "date":
        return datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m")
    ext = path.suffix.lower().lstrip(".")
    return ext if ext else "no_ext"


def main() -> int:
    args = parse_args()
    src = Path(args.input)
    if not src.is_dir():
        print(f"error: input is not a directory: {src}", file=sys.stderr)
        return 2

    out = Path(args.output) if args.output else src / "organized"
    do_apply = args.apply and not args.dry_run

    moved = 0
    for p in src.rglob("*"):
        if not p.is_file():
            continue
        if out in p.parents:
            continue
        sub = target_subdir(p, args.by)
        dst = out / sub / p.name
        print(f"{p} -> {dst}")
        moved += 1
        if do_apply:
            dst.parent.mkdir(parents=True, exist_ok=True)
            if dst.exists():
                stem = dst.stem
                suffix = dst.suffix
                i = 1
                while True:
                    candidate = dst.with_name(f"{stem}_{i}{suffix}")
                    if not candidate.exists():
                        dst = candidate
                        break
                    i += 1
            shutil.move(str(p), str(dst))

    print(f"total_files: {moved}")
    print("mode: apply" if do_apply else "mode: dry-run")
    if not do_apply:
        print("hint: use --apply to move files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
