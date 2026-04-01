#!/usr/bin/env python3
"""Batch resize images while preserving directory structure."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Batch resize images")
    parser.add_argument("-i", "--input", required=True, help="Input file or directory")
    parser.add_argument("-o", "--output", required=True, help="Output directory")
    parser.add_argument("--width", type=int, help="Target width")
    parser.add_argument("--height", type=int, help="Target height")
    parser.add_argument(
        "--keep-ratio", action="store_true", help="Keep original aspect ratio"
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        from PIL import Image
    except ImportError:
        print(
            "error: Pillow is required. Install with: pip3 install Pillow",
            file=sys.stderr,
        )
        return 2
    src = Path(args.input)
    out_root = Path(args.output)
    if not src.exists():
        print(f"error: input not found: {src}", file=sys.stderr)
        return 2
    if not args.width and not args.height:
        print("error: at least one of --width/--height is required", file=sys.stderr)
        return 2

    files = [src] if src.is_file() else [p for p in src.rglob("*") if p.is_file()]
    count = 0
    for file_path in files:
        rel = file_path.name if src.is_file() else str(file_path.relative_to(src))
        dst = out_root / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        try:
            with Image.open(file_path) as img:
                if args.keep_ratio:
                    width = args.width or img.width
                    height = args.height or img.height
                    img.thumbnail((width, height))
                    resized = img
                else:
                    width = args.width or img.width
                    height = args.height or img.height
                    resized = img.resize((width, height))
                resized.save(dst)
                count += 1
        except Exception:
            continue

    print(f"output_dir: {out_root}")
    print(f"resized_files: {count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
