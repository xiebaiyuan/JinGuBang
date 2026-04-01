#!/usr/bin/env python3
"""Export basic metadata for images as CSV or JSON."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate image metadata report")
    parser.add_argument("-i", "--input", required=True, help="Input file or directory")
    parser.add_argument("-o", "--output", help="Output file path")
    parser.add_argument("--format", choices=("csv", "json"), default="csv")
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
    if not src.exists():
        print(f"error: input not found: {src}", file=sys.stderr)
        return 2

    files = [src] if src.is_file() else [p for p in src.rglob("*") if p.is_file()]
    rows: list[dict[str, object]] = []
    for p in files:
        try:
            with Image.open(p) as img:
                rows.append(
                    {
                        "path": str(p),
                        "format": img.format,
                        "width": img.width,
                        "height": img.height,
                        "file_size": p.stat().st_size,
                        "has_exif": bool(getattr(img, "getexif", lambda: {})()),
                    }
                )
        except Exception:
            continue

    if args.format == "json":
        output_text = json.dumps(rows, indent=2, ensure_ascii=False) + "\n"
    else:
        from io import StringIO

        buf = StringIO()
        writer = csv.DictWriter(
            buf,
            fieldnames=["path", "format", "width", "height", "file_size", "has_exif"],
        )
        writer.writeheader()
        writer.writerows(rows)
        output_text = buf.getvalue()

    if args.output:
        Path(args.output).write_text(output_text, encoding="utf-8")
    else:
        print(output_text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
