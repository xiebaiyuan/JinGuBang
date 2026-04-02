#!/usr/bin/env python3
"""Collect TODO/FIXME/HACK/XXX comments from a codebase."""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

DEFAULT_TAGS = ["TODO", "FIXME", "HACK", "XXX", "BUG", "OPTIMIZE"]

SKIP_DIRS = {
    ".git", ".svn", ".hg", "node_modules", "__pycache__", ".tox",
    ".mypy_cache", ".ruff_cache", "venv", ".venv", "env", "dist",
    "build", ".build", ".gradle", "target", "Pods",
}

BINARY_EXTS = {
    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".ico", ".svg",
    ".zip", ".tar", ".gz", ".bz2", ".xz", ".7z", ".rar",
    ".exe", ".dll", ".so", ".dylib", ".o", ".a", ".class", ".jar",
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt",
    ".mp3", ".mp4", ".avi", ".mkv", ".wav", ".flac",
    ".woff", ".woff2", ".ttf", ".eot",
    ".pyc", ".pyo", ".DS_Store",
}


def should_skip_dir(name: str) -> bool:
    return name in SKIP_DIRS or name.startswith(".")


def is_binary(path: Path) -> bool:
    return path.suffix.lower() in BINARY_EXTS


def build_pattern(tags: list[str]) -> re.Pattern:
    escaped = "|".join(re.escape(t) for t in tags)
    return re.compile(rf"\b({escaped})\b[\s:：]*(.{{0,120}})", re.IGNORECASE)


def scan_file(path: Path, pattern: re.Pattern, max_size: int) -> list[dict]:
    if is_binary(path):
        return []
    if path.stat().st_size > max_size:
        return []

    hits = []
    try:
        with path.open("r", errors="ignore") as f:
            for lineno, line in enumerate(f, 1):
                m = pattern.search(line)
                if m:
                    hits.append({
                        "file": str(path),
                        "line": lineno,
                        "tag": m.group(1).upper(),
                        "text": m.group(2).strip().rstrip("*/").strip(),
                    })
    except OSError:
        pass
    return hits


def scan_dir(base: Path, pattern: re.Pattern, max_size: int) -> list[dict]:
    results = []
    for root, dirs, files in os.walk(base):
        dirs[:] = [d for d in dirs if not should_skip_dir(d)]
        for fname in files:
            fpath = Path(root) / fname
            results.extend(scan_file(fpath, pattern, max_size))
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect TODO/FIXME/HACK comments")
    parser.add_argument("path", nargs="?", default=".", help="Directory to scan")
    parser.add_argument(
        "-t", "--tags", default=",".join(DEFAULT_TAGS),
        help=f"Comma-separated tags (default: {','.join(DEFAULT_TAGS)})",
    )
    parser.add_argument("-g", "--group", choices=["file", "tag"], default="file",
                        help="Group by file or tag (default: file)")
    parser.add_argument("--csv", action="store_true", help="Output as CSV")
    parser.add_argument("--max-size", type=int, default=2,
                        help="Skip files larger than N MB (default: 2)")
    args = parser.parse_args()

    base = Path(args.path).resolve()
    if not base.is_dir():
        print(f"error: not a directory: {base}", file=sys.stderr)
        return 2

    tags = [t.strip() for t in args.tags.split(",") if t.strip()]
    pattern = build_pattern(tags)
    max_bytes = args.max_size * 1024 * 1024
    results = scan_dir(base, pattern, max_bytes)

    if args.csv:
        print("file,line,tag,text")
        for r in results:
            text = r["text"].replace('"', '""')
            print(f'"{r["file"]}",{r["line"]},{r["tag"]},"{text}"')
        return 0

    if not results:
        print(f"No {'/'.join(tags)} comments found in {base}")
        return 0

    if args.group == "tag":
        from collections import defaultdict
        by_tag: dict[str, list] = defaultdict(list)
        for r in results:
            by_tag[r["tag"]].append(r)
        for tag in sorted(by_tag):
            print(f"\n--- {tag} ({len(by_tag[tag])}) ---")
            for r in by_tag[tag]:
                rel = os.path.relpath(r["file"], base)
                print(f"  {rel}:{r['line']}  {r['text']}")
    else:
        from collections import defaultdict
        by_file: dict[str, list] = defaultdict(list)
        for r in results:
            by_file[r["file"]].append(r)
        for fpath in sorted(by_file):
            rel = os.path.relpath(fpath, base)
            print(f"\n{rel} ({len(by_file[fpath])})")
            for r in by_file[fpath]:
                print(f"  L{r['line']:>5} [{r['tag']}] {r['text']}")

    tag_counts = {}
    for r in results:
        tag_counts[r["tag"]] = tag_counts.get(r["tag"], 0) + 1
    print(f"\nTotal: {len(results)}  ", end="")
    print("  ".join(f"{t}: {c}" for t, c in sorted(tag_counts.items())))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
