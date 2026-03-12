#!/usr/bin/env python3
# filepath: log_summary.py

import argparse
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path

DEFAULT_EXTS = ["log", "txt", "out", "err"]
DEFAULT_KEYWORDS = [
    "error",
    "exception",
    "fail",
    "failed",
    "fatal",
    "panic",
    "traceback",
    "segfault",
]

TIMESTAMP_PATTERNS = [
    (re.compile(r"(\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2})"), "%Y-%m-%d %H:%M:%S"),
    (re.compile(r"(\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2})"), "%Y/%m/%d %H:%M:%S"),
    (re.compile(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2})"), "%Y-%m-%d %H:%M"),
    (re.compile(r"(\d{4}/\d{2}/\d{2} \d{2}:\d{2})"), "%Y/%m/%d %H:%M"),
    (re.compile(r"(\d{4}-\d{2}-\d{2})"), "%Y-%m-%d"),
    (re.compile(r"(\d{4}/\d{2}/\d{2})"), "%Y/%m/%d"),
]


def parse_user_time(value, is_until=False):
    if not value:
        return None

    value = value.strip()
    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y/%m/%d %H:%M:%S",
        "%Y/%m/%d %H:%M",
        "%Y-%m-%d",
        "%Y/%m/%d",
    ]
    for fmt in formats:
        try:
            parsed = datetime.strptime(value, fmt)
            if fmt in ("%Y-%m-%d", "%Y/%m/%d"):
                if is_until:
                    return parsed + timedelta(hours=23, minutes=59, seconds=59)
            return parsed
        except ValueError:
            continue
    raise ValueError(f"Unsupported time format: {value}")


def parse_timestamp(line):
    for pattern, fmt in TIMESTAMP_PATTERNS:
        match = pattern.search(line)
        if not match:
            continue
        value = match.group(1)
        if fmt == "%Y-%m-%d %H:%M:%S" and "T" in value:
            value = value.replace("T", " ")
        try:
            parsed = datetime.strptime(value, fmt)
        except ValueError:
            continue
        return parsed, match.span(1)
    return None, None


def normalize_line(line, timestamp_span=None, max_length=200):
    text = line.rstrip("\n")
    if timestamp_span:
        start, end = timestamp_span
        text = (text[:start] + text[end:]).strip()
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > max_length:
        return text[: max_length - 3] + "..."
    return text


def is_hidden_path(path):
    return any(part.startswith(".") for part in path.parts)


def iter_log_files(base_dir, exts, include_hidden):
    for file_path in base_dir.rglob("*"):
        if not file_path.is_file():
            continue
        if not include_hidden and is_hidden_path(file_path.relative_to(base_dir)):
            continue
        if exts is None:
            yield file_path
            continue
        suffix = file_path.suffix.lower().lstrip(".")
        if suffix in exts:
            yield file_path


def format_time(value):
    return value.strftime("%Y-%m-%d %H:%M:%S") if value else "n/a"


def main():
    parser = argparse.ArgumentParser(
        description="Summarize logs under a directory with time and keyword aggregation."
    )
    parser.add_argument(
        "-d", "--dir", default=".", help="Target directory (default: .)"
    )
    parser.add_argument(
        "--ext",
        default=",".join(DEFAULT_EXTS),
        help="Comma-separated extensions (default: log,txt,out,err). Use '*' for all files.",
    )
    parser.add_argument(
        "-p",
        "--pattern",
        action="append",
        default=[],
        help="Keyword pattern (can be used multiple times).",
    )
    parser.add_argument(
        "--no-default-keywords",
        action="store_true",
        help="Disable built-in keywords when no -p is provided.",
    )
    parser.add_argument(
        "--since", help="Start time filter (YYYY-MM-DD or YYYY-MM-DD HH:MM:SS)."
    )
    parser.add_argument(
        "--until", help="End time filter (YYYY-MM-DD or YYYY-MM-DD HH:MM:SS)."
    )
    parser.add_argument(
        "--top", type=int, default=20, help="Top items to show (default: 20)."
    )
    parser.add_argument(
        "--max-size-mb",
        type=int,
        default=50,
        help="Skip files larger than this size in MB (default: 50).",
    )
    parser.add_argument(
        "--include-hidden",
        action="store_true",
        help="Include hidden files and directories.",
    )

    args = parser.parse_args()

    base_dir = Path(args.dir).expanduser().resolve()
    if not base_dir.exists() or not base_dir.is_dir():
        print(f"Directory not found: {base_dir}", file=sys.stderr)
        sys.exit(1)

    try:
        since = parse_user_time(args.since, is_until=False) if args.since else None
        until = parse_user_time(args.until, is_until=True) if args.until else None
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)

    exts = None
    if args.ext.strip() != "*":
        exts = {
            ext.strip().lstrip(".").lower()
            for ext in args.ext.split(",")
            if ext.strip()
        }

    keywords = list(args.pattern)
    if not keywords and not args.no_default_keywords:
        keywords = DEFAULT_KEYWORDS

    keyword_patterns = [re.compile(re.escape(k), re.IGNORECASE) for k in keywords]

    total_files = 0
    skipped_large = 0
    total_lines = 0
    eligible_lines = 0
    matched_lines = 0
    skipped_no_timestamp = 0
    keyword_counts = Counter()
    file_counts = defaultdict(int)
    frequent_lines = Counter()
    earliest_time = None
    latest_time = None

    for file_path in iter_log_files(base_dir, exts, args.include_hidden):
        total_files += 1
        if args.max_size_mb > 0:
            size_mb = file_path.stat().st_size / (1024 * 1024)
            if size_mb > args.max_size_mb:
                skipped_large += 1
                continue

        try:
            with file_path.open("r", errors="ignore") as handle:
                for line in handle:
                    total_lines += 1
                    timestamp, span = parse_timestamp(line)
                    if since or until:
                        if not timestamp:
                            skipped_no_timestamp += 1
                            continue
                        if since and timestamp < since:
                            continue
                        if until and timestamp > until:
                            continue
                    eligible_lines += 1

                    if timestamp:
                        if earliest_time is None or timestamp < earliest_time:
                            earliest_time = timestamp
                        if latest_time is None or timestamp > latest_time:
                            latest_time = timestamp

                    if keyword_patterns:
                        if not any(p.search(line) for p in keyword_patterns):
                            continue
                    matched_lines += 1
                    file_counts[str(file_path)] += 1

                    for pattern, raw_keyword in zip(keyword_patterns, keywords):
                        if pattern.search(line):
                            keyword_counts[raw_keyword] += 1

                    if keyword_patterns:
                        normalized = normalize_line(line, span)
                        if normalized:
                            frequent_lines[normalized] += 1
        except (OSError, UnicodeError):
            continue

    print("Log Summary")
    print(f"Directory: {base_dir}")
    print(f"Files scanned: {total_files} (skipped large: {skipped_large})")
    if since or until:
        print(f"Time filter: since={format_time(since)} until={format_time(until)}")
    print(
        f"Time range (detected): {format_time(earliest_time)} -> {format_time(latest_time)}"
    )
    print(f"Lines scanned: {total_lines}")
    print(f"Eligible lines: {eligible_lines}")
    if since or until:
        print(f"Skipped (no timestamp): {skipped_no_timestamp}")
    print(f"Matched lines: {matched_lines}")

    if keywords:
        print("\nTop keywords:")
        for keyword, count in keyword_counts.most_common(args.top):
            print(f"- {keyword}: {count}")
        if not keyword_counts:
            print("- none")
    else:
        print("\nKeywords: none (all eligible lines are treated as matched)")

    print("\nTop files by matched lines:")
    for path, count in sorted(file_counts.items(), key=lambda x: x[1], reverse=True)[
        : args.top
    ]:
        print(f"- {path}: {count}")
    if not file_counts:
        print("- none")

    if keyword_patterns:
        print("\nTop lines:")
        for line, count in frequent_lines.most_common(args.top):
            print(f"- [{count}] {line}")
        if not frequent_lines:
            print("- none")


if __name__ == "__main__":
    main()
