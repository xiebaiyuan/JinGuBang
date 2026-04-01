#!/usr/bin/env bash

set -euo pipefail

usage() {
  cat <<'EOF'
Usage: git_branch_health.sh [--base <branch>] [--days <n>]

Checks:
  - merged local branches
  - stale local branches by last commit age
  - behind/ahead against base branch
EOF
}

base=""
days=30

while [[ $# -gt 0 ]]; do
  case "$1" in
    --base)
      shift
      base="${1:-}"
      ;;
    --days)
      shift
      days="${1:-30}"
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "error: unknown arg: $1" >&2
      usage
      exit 2
      ;;
  esac
  shift
done

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "error: not inside a git repository" >&2
  exit 2
fi

if [[ -z "$base" ]]; then
  base="$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | awk -F'/' '{print $NF}')"
  if [[ -z "$base" ]]; then
    if git show-ref --verify --quiet refs/heads/main; then
      base="main"
    elif git show-ref --verify --quiet refs/heads/master; then
      base="master"
    else
      base="$(git branch --show-current)"
    fi
  fi
fi

echo "base_branch=$base"
echo "stale_days=$days"
echo

echo "[MERGED BRANCHES]"
current="$(git branch --show-current)"
git branch --merged "$base" | sed 's/^..//' | while read -r b; do
  [[ -z "$b" || "$b" == "$base" || "$b" == "$current" ]] && continue
  echo "$b"
done

echo
echo "[STALE BRANCHES]"
now_ts="$(date +%s)"
git for-each-ref --format='%(refname:short) %(committerdate:unix)' refs/heads | while read -r b ts; do
  [[ -z "$b" || "$b" == "$current" ]] && continue
  age_days=$(( (now_ts - ts) / 86400 ))
  if (( age_days >= days )); then
    echo "$b age_days=$age_days"
  fi
done

echo
echo "[BASE DIFF STATUS]"
if git rev-parse --verify "$base" >/dev/null 2>&1; then
  ahead_behind="$(git rev-list --left-right --count "$base...HEAD")"
  behind="${ahead_behind%% *}"
  ahead="${ahead_behind##* }"
  echo "behind_base=$behind"
  echo "ahead_base=$ahead"
else
  echo "warning: base branch not found locally: $base"
fi
