#!/usr/bin/env python3
"""Pretty directory tree with file sizes and statistics."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

SKIP_DIRS = {
    ".git", ".svn", ".hg", "node_modules", "__pycache__", ".tox",
    ".mypy_cache", ".ruff_cache", ".DS_Store",
}


def format_size(size: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024:
            if unit == "B":
                return f"{size}{unit}"
            return f"{size:.1f}{unit}"
        size /= 1024
    return f"{size:.1f}TB"


def dir_size(path: Path) -> int:
    total = 0
    try:
        for entry in os.scandir(path):
            if entry.is_file(follow_symlinks=False):
                total += entry.stat(follow_symlinks=False).st_size
            elif entry.is_dir(follow_symlinks=False):
                total += dir_size(Path(entry.path))
    except PermissionError:
        pass
    return total


def print_tree(path: Path, prefix: str, depth: int, max_depth: int,
               show_hidden: bool, show_size: bool, dirs_only: bool,
               stats: dict) -> None:
    if max_depth > 0 and depth > max_depth:
        return

    try:
        entries = sorted(os.scandir(path), key=lambda e: (not e.is_dir(), e.name.lower()))
    except PermissionError:
        return

    filtered = []
    for entry in entries:
        name = entry.name
        if not show_hidden and (name.startswith(".") or name in SKIP_DIRS):
            continue
        if dirs_only and not entry.is_dir(follow_symlinks=False):
            continue
        filtered.append(entry)

    for i, entry in enumerate(filtered):
        is_last = (i == len(filtered) - 1)
        connector = "└── " if is_last else "├── "
        extension = "    " if is_last else "│   "

        if entry.is_dir(follow_symlinks=False):
            stats["dirs"] += 1
            size_str = ""
            if show_size:
                sz = dir_size(Path(entry.path))
                size_str = f"  [{format_size(sz)}]"
            print(f"{prefix}{connector}{entry.name}/{size_str}")
            print_tree(Path(entry.path), prefix + extension, depth + 1,
                       max_depth, show_hidden, show_size, dirs_only, stats)
        else:
            stats["files"] += 1
            sz = entry.stat(follow_symlinks=False).st_size
            stats["total_size"] += sz
            size_str = ""
            if show_size:
                size_str = f"  [{format_size(sz)}]"
            print(f"{prefix}{connector}{entry.name}{size_str}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Pretty directory tree with sizes")
    parser.add_argument("path", nargs="?", default=".", help="Directory to display")
    parser.add_argument("-d", "--depth", type=int, default=0,
                        help="Max depth (0 = unlimited)")
    parser.add_argument("-s", "--size", action="store_true", help="Show file/dir sizes")
    parser.add_argument("-a", "--all", action="store_true", help="Show hidden files")
    parser.add_argument("--dirs-only", action="store_true", help="Only show directories")
    args = parser.parse_args()

    base = Path(args.path).resolve()
    if not base.is_dir():
        print(f"error: not a directory: {base}", file=sys.stderr)
        return 2

    size_str = ""
    if args.size:
        sz = dir_size(base)
        size_str = f"  [{format_size(sz)}]"
    print(f"{base.name}/{size_str}")

    stats: dict = {"dirs": 0, "files": 0, "total_size": 0}
    print_tree(base, "", 1, args.depth, args.all, args.size, args.dirs_only, stats)

    print(f"\n{stats['dirs']} directories, {stats['files']} files", end="")
    if args.size:
        print(f", {format_size(stats['total_size'])} total", end="")
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
