# Mac Cleanup Tool

A comprehensive tool for safely cleaning up unnecessary files on macOS while preserving important data.

## Features

- Safe removal of unnecessary files without affecting important system or user data
- Multiple cleanup categories including:
  - Xcode derived data and archives
  - iOS simulator data
  - Docker cache and volumes
  - Homebrew cache
  - Application caches
  - Temporary files
  - Downloads folder cleanup
  - Trash emptying
- Dry run mode to preview what will be cleaned
- Detailed logging with timestamps
- Progress bar for visual feedback
- Customizable exclusion options
- Color-coded output for better readability
- Support for custom paths

## Requirements

- macOS system
- [`trash`](https://github.com/sindresorhus/trash) command-line tool
- Docker (optional, for Docker cleanup)
- Homebrew (optional, for Homebrew cache cleanup)

To install the required `trash` utility:

```bash
brew install trash
```

## Installation

1. Save the `mac_cleaner.sh` script to a location in your PATH
2. Make it executable:

```bash
chmod +x mac_cleaner.sh
```

## Usage

```bash
./mac_cleaner.sh [options]
```

### Options

| Option | Description |
|--------|-------------|
| `--help` | Show help message |
| `--dry-run` | Simulate cleanup without actually deleting files |
| `--no-confirm` | Skip confirmation prompts |
| `--quiet` | Quiet mode, only show errors and final results |
| `--verbose` | Verbose mode, show more information |
| `--debug` | Debug mode, show all information |
| `--exclude-system` | Exclude system caches (`~/Library/Caches`) |
| `--exclude-downloads` | Exclude `~/Downloads` folder |
| `--exclude-documents` | Exclude `~/Documents` folder |
| `--exclude-desktop` | Exclude `~/Desktop` folder |
| `--custom-path PATH` | Add custom path to clean |

### Examples

```bash
# Run with default settings
./mac_cleaner.sh

# Preview what would be cleaned without deleting
./mac_cleaner.sh --dry-run

# Exclude system caches from cleanup
./mac_cleaner.sh --exclude-system

# Run without confirmation prompts
./mac_cleaner.sh --no-confirm

# Clean with custom path
./mac_cleaner.sh --custom-path "/path/to/custom/folder"

# Run in debug mode for detailed output
./mac_cleaner.sh --debug
```

## What This Tool Cleans

By default, the tool cleans the following:

1. **Xcode Derived Data**: `~/Library/Developer/Xcode/DerivedData`
2. **Xcode Archives**: `~/Library/Developer/Xcode/Archives`
3. **iOS Simulator Data**: `~/Library/Developer/CoreSimulator`
4. **Docker Cache**: Uses `docker system prune` and `docker builder prune`
5. **Homebrew Cache**: Uses `brew cleanup`
6. **Application Caches**: Contents of `~/Library/Caches`
7. **Temporary Files**: Files in `/tmp`
8. **Downloads Folder**: Temporary and installer files (`.tmp`, `.dmg`, etc.)
9. **Trash**: Empties the system trash

## Safety Features

1. **Uses Trash Command**: Files are moved to the system trash rather than permanently deleted
2. **Dry Run Mode**: Preview what will be cleaned without making any changes
3. **Confirmation Prompts**: Requires explicit confirmation before cleaning (unless `--no-confirm` is used)
4. **Exclusion Options**: Customize what gets cleaned with exclusion flags
5. **Logging**: Detailed logs are saved to `~/Downloads/mac_cleaner_YYYYMMDD_HHMMSS.log`

## Customization

You can customize the cleanup paths by editing the `cleanup_paths` associative array in the script:

```bash
# Add new paths like this:
cleanup_paths["/path/to/custom/location"]="*.tmp"
```

Each entry consists of a path as the key and a file pattern as the value.

## Recovery

Since this tool uses the `trash` command, all deleted files are moved to the system trash and can be recovered through the standard macOS trash recovery process.

## Contributing

Feel free to submit issues or pull requests to improve this tool.

## License

This project is licensed under the MIT License - see the LICENSE file for details.