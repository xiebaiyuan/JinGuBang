#!/usr/bin/env bash

set -euo pipefail

usage() {
  cat <<'EOF'
Usage: empty_dirs_cleaner.sh <dir> [--dry-run] [--max-depth N]

Defaults:
  --dry-run enabled unless --apply is provided

Examples:
  bash file_management/empty_dirs_cleaner.sh ./build --dry-run
  bash file_management/empty_dirs_cleaner.sh ./build --max-depth 4 --apply
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

dry_run=1
max_depth=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)
      dry_run=1
      ;;
    --apply)
      dry_run=0
      ;;
    --max-depth)
      shift
      max_depth="${1:-}"
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

args=("$target")
if [[ -n "$max_depth" ]]; then
  args+=("-mindepth" 1 "-maxdepth" "$max_depth")
else
  args+=("-mindepth" 1)
fi

echo "target=$target"
echo "mode=$([[ $dry_run -eq 1 ]] && echo dry-run || echo apply)"

mapfile -t dirs < <(find "${args[@]}" -type d -empty | sort -r)
for d in "${dirs[@]}"; do
  echo "$d"
  if [[ $dry_run -eq 0 ]]; then
    rmdir "$d" || true
  fi
done

echo "total_empty_dirs=${#dirs[@]}"
