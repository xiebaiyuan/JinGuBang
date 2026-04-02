#!/usr/bin/env python3
"""Quick statistics for CSV files: row/column counts, types, numeric stats."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path


def detect_type(values: list[str]) -> str:
    """Detect column type from sample values."""
    non_empty = [v for v in values if v.strip()]
    if not non_empty:
        return "empty"

    int_count = float_count = 0
    for v in non_empty:
        try:
            int(v)
            int_count += 1
            continue
        except ValueError:
            pass
        try:
            float(v)
            float_count += 1
        except ValueError:
            pass

    total = len(non_empty)
    if int_count == total:
        return "integer"
    if (int_count + float_count) == total:
        return "float"
    return "string"


def numeric_stats(values: list[str]) -> dict | None:
    nums = []
    for v in values:
        try:
            nums.append(float(v))
        except (ValueError, TypeError):
            continue
    if not nums:
        return None

    nums.sort()
    n = len(nums)
    mean = sum(nums) / n
    median = nums[n // 2] if n % 2 else (nums[n // 2 - 1] + nums[n // 2]) / 2

    return {
        "count": n,
        "min": nums[0],
        "max": nums[-1],
        "mean": round(mean, 4),
        "median": round(median, 4),
    }


def fmt_num(v: float) -> str:
    if v == int(v):
        return str(int(v))
    return f"{v:.4f}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Quick CSV file statistics")
    parser.add_argument("file", help="CSV file to analyze")
    parser.add_argument("-d", "--delimiter", default=",", help="Delimiter (default: comma)")
    parser.add_argument("--head", type=int, default=5, help="Sample rows to show (default: 5)")
    parser.add_argument("--no-header", action="store_true", help="CSV has no header row")
    parser.add_argument("--encoding", default="utf-8", help="File encoding (default: utf-8)")
    args = parser.parse_args()

    path = Path(args.file)
    if not path.exists():
        print(f"error: file not found: {path}", file=sys.stderr)
        return 2

    try:
        with path.open("r", encoding=args.encoding, errors="replace") as f:
            reader = csv.reader(f, delimiter=args.delimiter)
            rows = list(reader)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if not rows:
        print("Empty CSV file.")
        return 0

    if args.no_header:
        headers = [f"col_{i}" for i in range(len(rows[0]))]
        data_rows = rows
    else:
        headers = rows[0]
        data_rows = rows[1:]

    num_cols = len(headers)
    num_rows = len(data_rows)
    file_size = path.stat().st_size

    print(f"File:    {path}")
    print(f"Size:    {file_size:,} bytes")
    print(f"Rows:    {num_rows:,} (data)")
    print(f"Columns: {num_cols}")

    # columns by index
    columns: dict[int, list[str]] = {i: [] for i in range(num_cols)}
    for row in data_rows:
        for i in range(num_cols):
            columns[i].append(row[i] if i < len(row) else "")

    # column info
    print(f"\n{'#':<4} {'Column':<24} {'Type':<10} {'Non-Empty':>10} {'Unique':>8}")
    print("-" * 60)
    for i, h in enumerate(headers):
        col = columns[i]
        col_type = detect_type(col)
        non_empty = sum(1 for v in col if v.strip())
        unique = len(set(col))
        print(f"{i:<4} {h:<24} {col_type:<10} {non_empty:>10} {unique:>8}")

    # numeric stats
    numeric_cols = []
    for i, h in enumerate(headers):
        stats = numeric_stats(columns[i])
        if stats and stats["count"] > 0:
            numeric_cols.append((i, h, stats))

    if numeric_cols:
        print(f"\nNumeric column statistics:")
        print(f"{'Column':<24} {'Count':>8} {'Min':>12} {'Max':>12} {'Mean':>12} {'Median':>12}")
        print("-" * 82)
        for i, h, s in numeric_cols:
            print(f"{h:<24} {s['count']:>8} {fmt_num(s['min']):>12} {fmt_num(s['max']):>12} "
                  f"{fmt_num(s['mean']):>12} {fmt_num(s['median']):>12}")

    # sample rows
    if args.head > 0:
        show = min(args.head, num_rows)
        print(f"\nFirst {show} rows:")
        # compute column widths
        widths = [len(h) for h in headers]
        sample = data_rows[:show]
        for row in sample:
            for i in range(min(len(row), num_cols)):
                widths[i] = min(max(widths[i], len(row[i])), 30)

        fmt = "  ".join(f"{{:<{w}}}" for w in widths)
        print(fmt.format(*[h[:30] for h in headers]))
        print("  ".join("-" * w for w in widths))
        for row in sample:
            vals = [(row[i] if i < len(row) else "")[:30] for i in range(num_cols)]
            print(fmt.format(*vals))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
