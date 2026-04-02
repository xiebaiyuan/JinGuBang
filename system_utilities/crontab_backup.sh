#!/usr/bin/env bash
# Backup and restore user crontab.
# Usage:
#   ./crontab_backup.sh backup              # backup to default dir
#   ./crontab_backup.sh backup -d /my/dir   # backup to custom dir
#   ./crontab_backup.sh restore <file>      # restore from file
#   ./crontab_backup.sh list                # list backups
#   ./crontab_backup.sh diff <file>         # diff backup vs current

set -euo pipefail

DEFAULT_DIR="${HOME}/.crontab_backups"

usage() {
    echo "Usage: $0 <command> [options]"
    echo ""
    echo "Commands:"
    echo "  backup  [-d dir]     Backup current crontab"
    echo "  restore <file>       Restore crontab from file"
    echo "  list    [-d dir]     List existing backups"
    echo "  diff    <file>       Diff backup against current crontab"
    echo ""
    echo "Default backup dir: ${DEFAULT_DIR}"
}

cmd_backup() {
    local dir="${DEFAULT_DIR}"
    while [[ $# -gt 0 ]]; do
        case "$1" in
            -d) dir="$2"; shift 2 ;;
            *) echo "Unknown option: $1"; exit 1 ;;
        esac
    done

    mkdir -p "${dir}"
    local ts
    ts=$(date +%Y%m%d_%H%M%S)
    local user
    user=$(whoami)
    local outfile="${dir}/crontab_${user}_${ts}.bak"

    if ! crontab -l > "${outfile}" 2>/dev/null; then
        echo "No crontab found for user ${user}."
        rm -f "${outfile}"
        return 1
    fi

    local lines
    lines=$(wc -l < "${outfile}" | tr -d ' ')
    echo "Backed up ${lines} lines to: ${outfile}"
}

cmd_restore() {
    local file="$1"
    if [[ ! -f "${file}" ]]; then
        echo "error: file not found: ${file}"
        exit 1
    fi

    local lines
    lines=$(wc -l < "${file}" | tr -d ' ')
    echo "About to restore crontab from: ${file} (${lines} lines)"
    echo "Current crontab will be overwritten."
    read -r -p "Continue? [y/N] " answer
    if [[ "${answer}" != "y" && "${answer}" != "Y" ]]; then
        echo "Aborted."
        exit 0
    fi

    crontab "${file}"
    echo "Crontab restored successfully."
}

cmd_list() {
    local dir="${DEFAULT_DIR}"
    while [[ $# -gt 0 ]]; do
        case "$1" in
            -d) dir="$2"; shift 2 ;;
            *) echo "Unknown option: $1"; exit 1 ;;
        esac
    done

    if [[ ! -d "${dir}" ]]; then
        echo "No backup directory found: ${dir}"
        return 0
    fi

    local count
    count=$(find "${dir}" -name "crontab_*.bak" -type f | wc -l | tr -d ' ')
    echo "Backup directory: ${dir}"
    echo "Found ${count} backup(s):"
    echo ""

    find "${dir}" -name "crontab_*.bak" -type f -exec ls -lh {} \; | sort -k9
}

cmd_diff() {
    local file="$1"
    if [[ ! -f "${file}" ]]; then
        echo "error: file not found: ${file}"
        exit 1
    fi

    local tmpfile
    tmpfile=$(mktemp)
    trap 'rm -f "${tmpfile}"' EXIT

    if ! crontab -l > "${tmpfile}" 2>/dev/null; then
        echo "No current crontab to compare."
        return 1
    fi

    echo "Diff: ${file} (backup) vs current crontab"
    echo "---"
    diff "${file}" "${tmpfile}" || true
}

if [[ $# -lt 1 ]]; then
    usage
    exit 1
fi

command="$1"
shift

case "${command}" in
    backup)  cmd_backup "$@" ;;
    restore)
        if [[ $# -lt 1 ]]; then echo "error: restore requires a file argument"; exit 1; fi
        cmd_restore "$1" ;;
    list)    cmd_list "$@" ;;
    diff)
        if [[ $# -lt 1 ]]; then echo "error: diff requires a file argument"; exit 1; fi
        cmd_diff "$1" ;;
    -h|--help) usage ;;
    *) echo "Unknown command: ${command}"; usage; exit 1 ;;
esac
