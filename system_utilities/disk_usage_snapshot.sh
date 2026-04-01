#!/usr/bin/env bash

set -euo pipefail

usage() {
  cat <<'EOF'
Usage: disk_usage_snapshot.sh <dir> [-n N] [--human] [-o file]

Examples:
  bash system_utilities/disk_usage_snapshot.sh . -n 20 --human
  bash system_utilities/disk_usage_snapshot.sh /tmp -n 10 -o /tmp/du_report.txt
EOF
}

if [[ $# -lt 1 ]]; then
  usage
  exit 2
fi

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  usage
  exit 0
fi

target="$1"
shift

topn=20
human=0
outfile=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    -n)
      shift
      topn="${1:-20}"
      ;;
    --human)
      human=1
      ;;
    -o)
      shift
      outfile="${1:-}"
      ;;
    *)
      echo "error: unknown arg: $1" >&2
      usage
      exit 2
      ;;
  esac
  shift
done

if [[ ! -d "$target" ]]; then
  echo "error: target directory not found: $target" >&2
  exit 2
fi

if [[ $human -eq 1 ]]; then
  data="$(du -h -d 1 "$target" 2>/dev/null || du -h "$target"/* 2>/dev/null | sort -hr | head -n "$topn")"
else
  data="$(du -k -d 1 "$target" 2>/dev/null || du -k "$target"/* 2>/dev/null | sort -nr | head -n "$topn")"
fi

output="snapshot_target=$target
top_n=$topn
human=$human

$data
"

if [[ -n "$outfile" ]]; then
  printf "%s" "$output" > "$outfile"
  echo "written: $outfile"
else
  printf "%s" "$output"
fi
