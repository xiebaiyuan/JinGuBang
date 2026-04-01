#!/usr/bin/env python3
"""Convert between JSON and YAML with optional PyYAML support."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convert JSON <-> YAML")
    parser.add_argument("-i", "--input", required=True, help="Input file")
    parser.add_argument("-o", "--output", help="Output file")
    parser.add_argument(
        "--to", choices=("json", "yaml"), required=True, help="Output format"
    )
    parser.add_argument("--pretty", action="store_true", help="Pretty-print output")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    src = Path(args.input)
    if not src.exists():
        print(f"error: input file not found: {src}", file=sys.stderr)
        return 2

    text = src.read_text(encoding="utf-8")
    source_ext = src.suffix.lower()

    if source_ext == ".json":
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            print(f"error: invalid json: {exc}", file=sys.stderr)
            return 2
    else:
        try:
            import yaml  # type: ignore
        except ImportError:
            print(
                "error: YAML input requires PyYAML. Install: pip3 install pyyaml",
                file=sys.stderr,
            )
            return 2
        try:
            data = yaml.safe_load(text)
        except Exception as exc:  # pylint: disable=broad-except
            print(f"error: invalid yaml: {exc}", file=sys.stderr)
            return 2

    if args.to == "json":
        out = json.dumps(data, ensure_ascii=False, indent=2 if args.pretty else None)
        if not args.pretty:
            out += "\n"
    else:
        try:
            import yaml  # type: ignore
        except ImportError:
            print(
                "error: YAML output requires PyYAML. Install: pip3 install pyyaml",
                file=sys.stderr,
            )
            return 2
        out = yaml.safe_dump(
            data,
            allow_unicode=True,
            sort_keys=False,
            default_flow_style=False,
            indent=2 if args.pretty else 2,
        )

    if args.output:
        Path(args.output).write_text(out, encoding="utf-8")
    else:
        print(out, end="" if out.endswith("\n") else "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
