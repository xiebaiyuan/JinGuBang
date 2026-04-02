#!/usr/bin/env python3
"""Count lines of code by language, with blank/comment line breakdown."""

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path

SKIP_DIRS = {
    ".git", ".svn", ".hg", "node_modules", "__pycache__", ".tox",
    ".mypy_cache", ".ruff_cache", "venv", ".venv", "env", "dist",
    "build", ".build", ".gradle", "target", "Pods", ".worktrees",
}

LANG_MAP: dict[str, dict] = {
    ".py":    {"name": "Python",     "line_comment": "#"},
    ".js":    {"name": "JavaScript", "line_comment": "//", "block": ("/*", "*/")},
    ".ts":    {"name": "TypeScript", "line_comment": "//", "block": ("/*", "*/")},
    ".tsx":   {"name": "TSX",        "line_comment": "//", "block": ("/*", "*/")},
    ".jsx":   {"name": "JSX",        "line_comment": "//", "block": ("/*", "*/")},
    ".java":  {"name": "Java",       "line_comment": "//", "block": ("/*", "*/")},
    ".kt":    {"name": "Kotlin",     "line_comment": "//", "block": ("/*", "*/")},
    ".swift": {"name": "Swift",      "line_comment": "//", "block": ("/*", "*/")},
    ".go":    {"name": "Go",         "line_comment": "//", "block": ("/*", "*/")},
    ".rs":    {"name": "Rust",       "line_comment": "//", "block": ("/*", "*/")},
    ".c":     {"name": "C",          "line_comment": "//", "block": ("/*", "*/")},
    ".h":     {"name": "C Header",   "line_comment": "//", "block": ("/*", "*/")},
    ".cpp":   {"name": "C++",        "line_comment": "//", "block": ("/*", "*/")},
    ".cc":    {"name": "C++",        "line_comment": "//", "block": ("/*", "*/")},
    ".hpp":   {"name": "C++ Header", "line_comment": "//", "block": ("/*", "*/")},
    ".cs":    {"name": "C#",         "line_comment": "//", "block": ("/*", "*/")},
    ".rb":    {"name": "Ruby",       "line_comment": "#",  "block": ("=begin", "=end")},
    ".php":   {"name": "PHP",        "line_comment": "//", "block": ("/*", "*/")},
    ".sh":    {"name": "Shell",      "line_comment": "#"},
    ".bash":  {"name": "Bash",       "line_comment": "#"},
    ".zsh":   {"name": "Zsh",        "line_comment": "#"},
    ".lua":   {"name": "Lua",        "line_comment": "--", "block": ("--[[", "]]")},
    ".r":     {"name": "R",          "line_comment": "#"},
    ".sql":   {"name": "SQL",        "line_comment": "--", "block": ("/*", "*/")},
    ".dart":  {"name": "Dart",       "line_comment": "//", "block": ("/*", "*/")},
    ".yml":   {"name": "YAML",       "line_comment": "#"},
    ".yaml":  {"name": "YAML",       "line_comment": "#"},
    ".toml":  {"name": "TOML",       "line_comment": "#"},
    ".html":  {"name": "HTML",       "block": ("<!--", "-->")},
    ".xml":   {"name": "XML",        "block": ("<!--", "-->")},
    ".css":   {"name": "CSS",        "block": ("/*", "*/")},
    ".scss":  {"name": "SCSS",       "line_comment": "//", "block": ("/*", "*/")},
    ".md":    {"name": "Markdown"},
    ".json":  {"name": "JSON"},
    ".vue":   {"name": "Vue",        "line_comment": "//", "block": ("/*", "*/")},
    ".svelte": {"name": "Svelte",    "line_comment": "//", "block": ("/*", "*/")},
}


@dataclass
class LangStats:
    name: str = ""
    files: int = 0
    code: int = 0
    comment: int = 0
    blank: int = 0

    @property
    def total(self) -> int:
        return self.code + self.comment + self.blank


def count_file(path: Path, lang: dict) -> tuple[int, int, int]:
    code = comment = blank = 0
    in_block = False
    block_start = lang.get("block", (None, None))[0]
    block_end = lang.get("block", (None, None))[1]
    line_comment = lang.get("line_comment")

    try:
        with path.open("r", errors="ignore") as f:
            for line in f:
                stripped = line.strip()
                if not stripped:
                    blank += 1
                    continue
                if in_block:
                    comment += 1
                    if block_end and block_end in stripped:
                        in_block = False
                    continue
                if block_start and stripped.startswith(block_start):
                    comment += 1
                    if block_end and block_end not in stripped[len(block_start):]:
                        in_block = True
                    continue
                if line_comment and stripped.startswith(line_comment):
                    comment += 1
                    continue
                code += 1
    except OSError:
        pass
    return code, comment, blank


def main() -> int:
    parser = argparse.ArgumentParser(description="Count lines of code by language")
    parser.add_argument("path", nargs="?", default=".", help="Directory to scan")
    parser.add_argument("--top", type=int, default=0, help="Show only top N languages")
    parser.add_argument("--sort", choices=["code", "files", "total", "name"],
                        default="code", help="Sort by (default: code)")
    parser.add_argument("--max-size", type=int, default=5,
                        help="Skip files larger than N MB (default: 5)")
    args = parser.parse_args()

    base = Path(args.path).resolve()
    if not base.is_dir():
        print(f"error: not a directory: {base}", file=sys.stderr)
        return 2

    stats: dict[str, LangStats] = {}
    max_bytes = args.max_size * 1024 * 1024
    file_count = 0

    for root, dirs, files in os.walk(base):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]
        for fname in files:
            fpath = Path(root) / fname
            ext = fpath.suffix.lower()
            lang = LANG_MAP.get(ext)
            if not lang:
                continue
            if fpath.stat().st_size > max_bytes:
                continue
            file_count += 1
            name = lang["name"]
            if name not in stats:
                stats[name] = LangStats(name=name)
            s = stats[name]
            s.files += 1
            c, cm, b = count_file(fpath, lang)
            s.code += c
            s.comment += cm
            s.blank += b

    if not stats:
        print(f"No recognized source files found in {base}")
        return 0

    sort_key = {
        "code": lambda s: s.code,
        "files": lambda s: s.files,
        "total": lambda s: s.total,
        "name": lambda s: s.name.lower(),
    }[args.sort]
    reverse = args.sort != "name"
    rows = sorted(stats.values(), key=sort_key, reverse=reverse)
    if args.top > 0:
        rows = rows[: args.top]

    header = f"{'Language':<16} {'Files':>6} {'Code':>10} {'Comment':>10} {'Blank':>8} {'Total':>10}"
    sep = "-" * len(header)
    print(header)
    print(sep)
    for s in rows:
        print(f"{s.name:<16} {s.files:>6} {s.code:>10} {s.comment:>10} {s.blank:>8} {s.total:>10}")
    print(sep)
    t_files = sum(s.files for s in rows)
    t_code = sum(s.code for s in rows)
    t_comment = sum(s.comment for s in rows)
    t_blank = sum(s.blank for s in rows)
    t_total = t_code + t_comment + t_blank
    print(f"{'TOTAL':<16} {t_files:>6} {t_code:>10} {t_comment:>10} {t_blank:>8} {t_total:>10}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
