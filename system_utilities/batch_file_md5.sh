#!/usr/bin/env bash

set -euo pipefail

TARGET_DIR="."
RECURSIVE=true
INCLUDE_PATTERN=""
EXCLUDE_PATTERN=""
SORT_MODE="path"
CSV_MODE=false
OUTPUT_FILE=""
ABSOLUTE_PATH=false
SHOW_COUNT=false

show_help() {
    cat <<'EOF'
Batch MD5 Calculator

Usage:
  batch_file_md5.sh [options]

Options:
  -d, --dir <path>          Target directory (default: .)
  -n, --non-recursive       Only scan top-level files
  -i, --include <pattern>   Include glob pattern, e.g. "*.so"
  -e, --exclude <pattern>   Exclude glob pattern, e.g. "*.log"
  -s, --sort <mode>         Sort mode: path|md5|none (default: path)
  -c, --csv                 Output CSV format
  -o, --output <file>       Write output to file
  -a, --absolute            Print absolute path
      --count               Show file count summary
  -h, --help                Show this help message

Examples:
  ./batch_file_md5.sh
  ./batch_file_md5.sh -d ./build -i "*.so" --count
  ./batch_file_md5.sh -d ./dist -n -s md5 -o md5_report.txt
  ./batch_file_md5.sh -d . -e "*.log" -c -o md5_report.csv
EOF
}

require_cmd() {
    if ! command -v "$1" >/dev/null 2>&1; then
        echo "Error: command '$1' not found" >&2
        exit 1
    fi
}

calc_md5() {
    local file="$1"
    if command -v md5sum >/dev/null 2>&1; then
        md5sum "$file" | awk '{print $1}'
    elif command -v md5 >/dev/null 2>&1; then
        md5 -q "$file"
    elif command -v openssl >/dev/null 2>&1; then
        openssl dgst -md5 "$file" | awk '{print $NF}'
    else
        echo "Error: no MD5 tool found (md5sum/md5/openssl)" >&2
        exit 1
    fi
}

to_display_path() {
    local file="$1"
    if "$ABSOLUTE_PATH"; then
        local dir_name
        local base_name
        dir_name=$(cd "$(dirname "$file")" && pwd)
        base_name=$(basename "$file")
        printf "%s/%s\n" "$dir_name" "$base_name"
        return
    fi

    local cleaned_dir="${TARGET_DIR%/}"
    if [[ "$cleaned_dir" == "." ]]; then
        printf "%s\n" "${file#./}"
        return
    fi

    if [[ "$file" == "$cleaned_dir"/* ]]; then
        printf "%s\n" "${file#"$cleaned_dir"/}"
    else
        printf "%s\n" "$file"
    fi
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        -d|--dir)
            TARGET_DIR="${2:-}"
            shift 2
            ;;
        -n|--non-recursive)
            RECURSIVE=false
            shift
            ;;
        -i|--include)
            INCLUDE_PATTERN="${2:-}"
            shift 2
            ;;
        -e|--exclude)
            EXCLUDE_PATTERN="${2:-}"
            shift 2
            ;;
        -s|--sort)
            SORT_MODE="${2:-}"
            shift 2
            ;;
        -c|--csv)
            CSV_MODE=true
            shift
            ;;
        -o|--output)
            OUTPUT_FILE="${2:-}"
            shift 2
            ;;
        -a|--absolute)
            ABSOLUTE_PATH=true
            shift
            ;;
        --count)
            SHOW_COUNT=true
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            echo "Error: unknown option '$1'" >&2
            show_help
            exit 1
            ;;
    esac
done

if [[ ! -d "$TARGET_DIR" ]]; then
    echo "Error: directory not found: $TARGET_DIR" >&2
    exit 1
fi

case "$SORT_MODE" in
    path|md5|none)
        ;;
    *)
        echo "Error: invalid sort mode '$SORT_MODE' (use path|md5|none)" >&2
        exit 1
        ;;
esac

require_cmd find
require_cmd awk

find_args=("$TARGET_DIR")
if ! "$RECURSIVE"; then
    find_args+=(-maxdepth 1)
fi
find_args+=(-type f)

if [[ -n "$INCLUDE_PATTERN" ]]; then
    find_args+=(-name "$INCLUDE_PATTERN")
fi

if [[ -n "$EXCLUDE_PATTERN" ]]; then
    find_args+=(! -name "$EXCLUDE_PATTERN")
fi

tmp_raw=$(mktemp)
tmp_sorted=$(mktemp)
trap 'rm -f "$tmp_raw" "$tmp_sorted"' EXIT

file_count=0
while IFS= read -r -d '' file; do
    md5_value=$(calc_md5 "$file")
    display_path=$(to_display_path "$file")
    printf "%s\t%s\n" "$md5_value" "$display_path" >> "$tmp_raw"
    file_count=$((file_count + 1))
done < <(find "${find_args[@]}" -print0)

if [[ "$SORT_MODE" == "path" ]]; then
    sort -k2,2 "$tmp_raw" > "$tmp_sorted"
elif [[ "$SORT_MODE" == "md5" ]]; then
    sort -k1,1 "$tmp_raw" > "$tmp_sorted"
else
    cp "$tmp_raw" "$tmp_sorted"
fi

if "$CSV_MODE"; then
    output_content=$( {
        printf "md5,path\n"
        while IFS=$'\t' read -r md5_value file_path; do
            escaped_path=${file_path//\"/\"\"}
            printf "%s,\"%s\"\n" "$md5_value" "$escaped_path"
        done < "$tmp_sorted"
    } )
else
    output_content=$(while IFS=$'\t' read -r md5_value file_path; do
        printf "%s  %s\n" "$md5_value" "$file_path"
    done < "$tmp_sorted")
fi

if [[ -n "$OUTPUT_FILE" ]]; then
    printf "%s\n" "$output_content" > "$OUTPUT_FILE"
else
    printf "%s\n" "$output_content"
fi

if "$SHOW_COUNT"; then
    printf "\nTotal files: %d\n" "$file_count" >&2
fi
