# File Management

用于文件整理、构建目录清理、重复文件分析和空间排查。

| 工具名 | 用途 | 使用示例 | 依赖 | 平台支持 | 风险级别 |
|---|---|---|---|---|---|
| `duplicate_finder.py` | 查找重复文件并可选择处理 | `python3 file_management/duplicate_finder.py .` | Python 标准库 | 跨平台 | 中 |
| `duplicate_file_analyzer.py` | 仅分析重复文件，不执行删除 | `python3 file_management/duplicate_file_analyzer.py .` | Python 标准库 | 跨平台 | 低 |
| `log_summary.py` | 日志关键字与时间维度汇总 | `python3 file_management/log_summary.py app.log` | Python 标准库 | 跨平台 | 低 |
| `smart_organize_by_type.py` | 按扩展名或日期自动归档文件（默认 dry-run） | `python3 file_management/smart_organize_by_type.py -i ./Downloads --by ext --dry-run` | Python 标准库 | 跨平台 | 中 |
| `large_files_top.py` | 定位目录中最大的文件 TopN | `python3 file_management/large_files_top.py -i . -n 20 --min-size 10M` | Python 标准库 | 跨平台 | 低 |
| `empty_dirs_cleaner.sh` | 清理空目录（默认 dry-run） | `bash file_management/empty_dirs_cleaner.sh . --dry-run` | `find` | macOS/Linux | 中 |
| `organize_files.sh` | 规则化整理文件 | `bash file_management/organize_files.sh` | Shell | macOS/Linux | 中 |
| `move_build_dirs_trash_v4.sh` | 推荐版构建目录清理工具 | `bash file_management/move_build_dirs_trash_v4.sh --dry-run` | `trash` 可选 | macOS/Linux | 中 |
| `move_build_dirs_trash.py` | 构建目录清理（Python 版） | `python3 file_management/move_build_dirs_trash.py --help` | Python 标准库 | 跨平台 | 中 |
| `mac_cleaner.sh` | 清理 macOS 缓存与临时文件 | `bash file_management/mac_cleaner.sh --dry-run` | macOS 命令 | macOS | 中 |
| `clean_docker.sh` | 清理 Docker 资源 | `bash file_management/clean_docker.sh` | Docker | macOS/Linux | 高 |
| `tree_view.py` | 目录树可视化，带文件大小统计 | `python3 file_management/tree_view.py . -d 3 -s` | Python 标准库 | 跨平台 | 低 |

## 旧名与推荐名

- `move_build_dirs_trash.sh` / `v2` / `v3` 仍保留，推荐优先使用 `move_build_dirs_trash_v4.sh`。

## 相关文档

- `file_management/duplicate_finder_readme.md`
- `file_management/duplicate_file_analyzer.md`
- `file_management/log_summary_readme.md`
- `file_management/organize_files_readme.md`
- `file_management/clean_build_readme.md`
- `file_management/clean_build_py_readme.md`
- `file_management/mac_cleaner.md`
