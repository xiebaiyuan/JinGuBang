# Duplicate File Analyzer

This is a simple tool to analyze directories and identify duplicate files based on their MD5 hash values. Unlike the existing `duplicate_finder.py` which can move files to trash, this tool only analyzes and displays information about duplicates without performing any deletions.

## Features

- Scans directories recursively to find all files
- Calculates MD5 hash for each file to identify duplicates
- Groups files by their hash values
- Displays duplicate file groups with their paths
- Optionally shows file sizes and potential space savings
- Safe to use as it doesn't perform any deletions

## Usage

```bash
python duplicate_file_analyzer.py <directory_path> [--size]
```

### Basic Usage Examples

```bash
# Analyze duplicate files in a directory
python duplicate_file_analyzer.py /path/to/directory

# Show file sizes in the output
python duplicate_file_analyzer.py /path/to/directory --size
```

### Command Line Options

| Option | Description |
|--------|-------------|
| `--size` | Show file sizes and potential space savings |

## How It Works

1. The tool recursively scans the specified directory for all files
2. For each file, it calculates an MD5 hash of its contents
3. Files with identical hashes are grouped together as duplicates
4. The tool displays these groups along with their file paths
5. When using the `--size` option, it also shows file sizes and potential space savings

## Differences from duplicate_finder.py

- Only analyzes and displays information, doesn't perform deletions
- Simpler implementation focused solely on identification
- No complex logic for determining "original" vs "duplicate" files
- No support for excluding directories or other advanced options
- Useful for initial analysis before taking action on duplicates