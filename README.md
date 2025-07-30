# WUKONG_TOOLS

## Tools for my daily work. Powerful as Wukong.

This repository contains a collection of utility scripts designed to help with various tasks. Below is a categorized list of tools with links to their detailed documentation.

## Table of Contents

### File Management
- [Duplicate Finder](docs/duplicate_finder_readme.md) - Find and remove duplicate files
- [Duplicate File Analyzer](#duplicate-file-analyzer) - Analyze duplicate files without removing them
- [Organize Files](docs/organize_files_readme.md) - Organize files by type or other criteria

### Git Tools
- [Export Git Commits to Patches](docs/export_commits_to_patches_readme.md) - Export git commits as patch files
- [Batch Modify Git Commits](docs/batch_modify_git_commits.md) - Modify author information in git history

### System Utilities
- [Mac Cleaner](docs/mac_cleaner.md) - Clean up temporary and cache files on macOS
- [Clean Build Directories](docs/clean_build_readme.md) - Move build directories to trash
- [Clean Build Directories (Python)](docs/clean_build_py_readme.md) - Python version of build directory cleaner
- [AVIF to PNG Converter](docs/avif_to_png_converter.md) - Convert AVIF images to PNG format
- [Update Zsh Plugin](docs/update_zsh_plugin.md) - Update Zsh plugins

### Media Tools
- [Collect Markdown Images](#collect-markdown-images) - Extract images from markdown files
- [Apple Music Player](#apple-music-player) - Play music from Apple Music library

---

## File Management Tools

### Duplicate Finder

Find and remove duplicate files to save storage space.

[Detailed documentation](docs/duplicate_finder_readme.md)

### Duplicate File Analyzer

Analyze duplicate files without removing them.

```bash
python duplicate_file_analyzer.py <directory_path> [--size]
```

Example:
```bash
# Analyze duplicate files in a directory
python duplicate_file_analyzer.py /path/to/directory

# Show file size information
python duplicate_file_analyzer.py /path/to/directory --size
```

Features:
- Only analyzes and displays duplicate file information, no deletion
- Shows duplicate file groups and their hash values
- Optionally shows file sizes and potential storage savings
- Safe to use for initial directory scanning

---

## Git Tools

### Export Git Commits to Patches

Export git commits as patch files for easy sharing or backup.

[Detailed documentation](docs/export_commits_to_patches_readme.md)

### Batch Modify Git Commits

Modify author information in git history.

[Detailed documentation](docs/batch_modify_git_commits.md)

---

## System Utilities

### Mac Cleaner

Clean up temporary and cache files on macOS.

[Detailed documentation](docs/mac_cleaner.md)

### Clean Build Directories

Move build directories to trash.

[Detailed documentation](docs/clean_build_readme.md)

### AVIF to PNG Converter

Convert AVIF images to PNG format.

[Detailed documentation](docs/avif_to_png_converter.md)

---

## Media Tools

### Collect Markdown Images

Extract images from markdown files.

```bash
python collect_md.py demo.md -o md_images -d /Users/xiebaiyuan/Documents/md_collects/
```

### Apple Music Player

Play music from Apple Music library.

```bash
python apple_music_player.py
```

## Other Utilities

### Parse Me Crash

Parse crash logs from Minecraft.

[Detailed documentation](docs/parse_me_crash.md)

### Organize Files

Organize files by type or other criteria.

[Detailed documentation](docs/organize_files_readme.md)

---

## Disclaimer

These scripts are untested and provided "as is" without any warranties or guarantees of any kind. Use them at your own risk. The author assumes no responsibility for any errors, omissions, or damages resulting from the use of these scripts. Please exercise caution and thoroughly test the scripts in a safe environment before deploying them in a production setting.