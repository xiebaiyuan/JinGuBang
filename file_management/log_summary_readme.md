# Log Summary

Summarize logs or text files under a directory with time/keyword aggregation and quick hotspots.

## Features

- Scan common log extensions (`log`, `txt`, `out`, `err`) or all files
- Time filter with `--since` and `--until`
- Keyword aggregation with top counts and frequent lines
- File-level summary of matched lines
- Skip large files by size limit

## Usage

```bash
python3 file_management/log_summary.py -d ./logs
```

### Options

- `-d, --dir` target directory (default: `.`)
- `--ext` comma-separated extensions, or `*` for all
- `-p, --pattern` keyword pattern (can be used multiple times)
- `--no-default-keywords` disable built-in keywords
- `--since` start time filter (e.g. `2024-01-01` or `2024-01-01 12:00:00`)
- `--until` end time filter
- `--top` top items to show (default: 20)
- `--max-size-mb` skip files larger than this size (default: 50)
- `--include-hidden` include hidden files and directories

## Examples

```bash
# Scan ./logs with default keywords
python3 file_management/log_summary.py -d ./logs

# Filter by time range
python3 file_management/log_summary.py -d ./logs --since "2024-01-01" --until "2024-01-02"

# Use custom keywords only
python3 file_management/log_summary.py -d ./logs -p timeout -p refused --no-default-keywords

# Scan all files, not just log/txt/out/err
python3 file_management/log_summary.py -d ./logs --ext "*"
```
