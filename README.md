# WUKONG_TOOLS

## Tools for my daily work. Powerful as Wukong.

This repository contains a collection of utility scripts designed to help with various tasks. The tools are organized into categorized directories with links to their detailed documentation.

## Table of Contents

### [File Management](file_management/)
- [Duplicate Finder](file_management/duplicate_finder_readme.md) - Find and remove duplicate files
- [Duplicate File Analyzer](file_management/duplicate_file_analyzer.md) - Analyze duplicate files without removing them
- [Organize Files](file_management/organize_files_readme.md) - Organize files by type or other criteria
- [Clean Build Directories](file_management/clean_build_readme.md) - Move build directories to trash
- [Clean Build Directories (Python)](file_management/clean_build_py_readme.md) - Python version of build directory cleaner
- [Mac Cleaner](file_management/mac_cleaner.md) - Clean up temporary and cache files on macOS

### [Git Tools](git_tools/)
- [Export Git Commits to Patches](git_tools/export_commits_to_patches_readme.md) - Export git commits as patch files
- [Batch Modify Git Commits](git_tools/batch_modify_git_commits.md) - Modify author information in git history

### [Media Tools](media_tools/)
- [AVIF to PNG Converter](media_tools/avif_to_png_converter.md) - Convert AVIF images to PNG format
- [Collect Markdown Images](#collect-markdown-images) - Extract images from markdown files
- [Apple Music Player](#apple-music-player) - Play music from Apple Music library

### [System Utilities](system_utilities/)
- [Update Zsh Plugin](system_utilities/update_zsh_plugin.md) - Update Zsh plugins

### [Other Tools](other_tools/)
- [Parse Me Crash](other_tools/parse_me_crash.md) - Parse crash logs from Minecraft

## File Management Tools

Find and remove duplicate files to save storage space, organize files, and clean build directories.

[Detailed documentation for all file management tools](file_management/)

---

## Git Tools

Tools for working with Git repositories, including exporting commits as patches and modifying commit history.

[Detailed documentation for all Git tools](git_tools/)

---

## System Utilities

Utilities for system maintenance and management.

[Detailed documentation for all system utilities](system_utilities/)

---

## Media Tools

Tools for handling media files and extraction.

[Detailed documentation for all media tools](media_tools/)

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

Specialized tools for specific tasks.

[Detailed documentation for other tools](other_tools/)

---

## Disclaimer

These scripts are untested and provided "as is" without any warranties or guarantees of any kind. Use them at your own risk. The author assumes no responsibility for any errors, omissions, or damages resulting from the use of these scripts. Please exercise caution and thoroughly test the scripts in a safe environment before deploying them in a production setting.