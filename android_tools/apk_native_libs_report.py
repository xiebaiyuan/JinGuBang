#!/usr/bin/env python3
"""Generate ABI and size report for native libs in APK/AAB."""

from __future__ import annotations

import argparse
import csv
import json
import sys
import zipfile
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scan APK/AAB and report native libraries by ABI."
    )
    parser.add_argument("-i", "--input", required=True, help="Path to APK/AAB file")
    parser.add_argument("-o", "--output", help="Output file path")
    parser.add_argument(
        "--format",
        choices=("text", "json", "csv"),
        default="text",
        help="Output format",
    )
    parser.add_argument(
        "--target-abis",
        default="armeabi-v7a,arm64-v8a,x86,x86_64",
        help="Comma-separated ABI list to compare against",
    )
    return parser.parse_args()


def collect_libs(input_file: Path) -> dict[str, object]:
    with zipfile.ZipFile(input_file, "r") as zf:
        abis: dict[str, dict[str, int]] = {}
        for info in zf.infolist():
            parts = info.filename.split("/")
            if len(parts) >= 3 and parts[0] == "lib" and parts[-1].endswith(".so"):
                abi = parts[1]
                stats = abis.setdefault(abi, {"count": 0, "size": 0})
                stats["count"] += 1
                stats["size"] += info.file_size

    total_so = sum(v["count"] for v in abis.values())
    total_size = sum(v["size"] for v in abis.values())
    return {
        "input": str(input_file),
        "abi_stats": abis,
        "total_so_files": total_so,
        "total_size_bytes": total_size,
    }


def to_text(report: dict[str, object], target_abis: list[str]) -> str:
    lines = [
        f"input: {report['input']}",
        f"total_so_files: {report['total_so_files']}",
        f"total_size_bytes: {report['total_size_bytes']}",
        "",
        "abi stats:",
    ]
    abi_stats = report["abi_stats"]
    assert isinstance(abi_stats, dict)
    for abi in sorted(abi_stats):
        stats = abi_stats[abi]
        lines.append(f"- {abi}: count={stats['count']} size={stats['size']}")
    missing = [abi for abi in target_abis if abi not in abi_stats]
    lines.append("")
    lines.append(f"missing_abis: {', '.join(missing) if missing else 'none'}")
    return "\n".join(lines) + "\n"


def to_csv(report: dict[str, object], target_abis: list[str]) -> str:
    from io import StringIO

    buf = StringIO()
    writer = csv.writer(buf)
    writer.writerow(["abi", "so_count", "size_bytes", "missing"])
    abi_stats = report["abi_stats"]
    assert isinstance(abi_stats, dict)
    for abi in sorted(set(target_abis) | set(abi_stats.keys())):
        stats = abi_stats.get(abi, {"count": 0, "size": 0})
        writer.writerow([abi, stats["count"], stats["size"], abi not in abi_stats])
    return buf.getvalue()


def main() -> int:
    args = parse_args()
    input_file = Path(args.input)
    if not input_file.exists():
        print(f"error: input file not found: {input_file}", file=sys.stderr)
        return 2
    if input_file.suffix.lower() not in {".apk", ".aab"}:
        print("error: input must be .apk or .aab", file=sys.stderr)
        return 2
    if not zipfile.is_zipfile(input_file):
        print("error: input is not a valid zip-based APK/AAB", file=sys.stderr)
        return 2

    target_abis = [x.strip() for x in args.target_abis.split(",") if x.strip()]
    report = collect_libs(input_file)
    abi_stats = report["abi_stats"]
    assert isinstance(abi_stats, dict)
    report["missing_abis"] = [abi for abi in target_abis if abi not in abi_stats]

    if args.format == "json":
        output = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    elif args.format == "csv":
        output = to_csv(report, target_abis)
    else:
        output = to_text(report, target_abis)

    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
    else:
        print(output, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
