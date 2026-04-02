# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**WUKONG_TOOLS** — 一个按场景分类的实用脚本仓库（Python 3 + Bash），覆盖 Android 分析、文件管理、Git 操作、媒体处理、网络检测和系统维护等常见开发任务。每个子目录自成一体，有独立 README。项目优先最小化依赖，面向"日常可复用"场景。

## Repository Structure

| Directory | Purpose |
|---|---|
| `android_tools/` | Android SO/ELF 二进制分析（文件头、符号、依赖、NDK 检测、16KB 页对齐） |
| `dev_tools/` | 开发辅助：TODO/FIXME 收集、代码行数统计 |
| `file_management/` | 重复文件检测、构建目录清理、macOS 缓存清理、Docker 清理、目录树可视化 |
| `git_tools/` | Patch 导出、commit 批量修改、Fork 同步、GitHub token 清理 |
| `media_tools/` | AVIF→PNG 转换、EXIF 编辑、Markdown 资源收集、Kindle 图像适配 |
| `net_tools/` | 端口扫描、DNS 报告、SSL 证书检查、HTTP 健康检测 |
| `system_utilities/` | 批量文件 MD5 计算、IP 信息收集、Zsh 插件更新、监听端口查看、Crontab 备份 |
| `other_tools/` | Minecraft 崩溃日志解析、JSON/YAML 转换、文本编解码、CSV 统计 |
| `kindle-wallpaper-tool/` | 独立子项目，含自己的 `requirements.txt`（Pillow），支持 20+ Kindle 型号 |

根目录额外包含：
- `fix_any.sh` / `fix_any2.sh` — 将 Claude CLI 中的 `api.anthropic.com` 替换为自定义 API 主机（`fix_any2.sh` 为增强版，正确解析 pnpm 包装脚本和软链接）

## Key Tools Quick Reference

```bash
# 给 Shell 脚本授权（首次使用）
chmod +x system_utilities/*.sh file_management/*.sh git_tools/*.sh media_tools/*.sh

# 批量 MD5 计算
./system_utilities/batch_file_md5.sh -d ./build -i "*.so" --count
./system_utilities/batch_file_md5.sh -d . -c -o md5_report.csv

# Android SO/ELF 分析
python3 android_tools/android_so_analyzer.py <path-to-so-file>
python3 android_tools/check_android_so.py <path-to-so-file>

# 重复文件查找
python3 file_management/duplicate_finder.py <directory>
python3 file_management/duplicate_finder.py <directory> --global --confirm

# macOS 缓存/临时文件清理
./file_management/mac_cleaner.sh --dry-run

# Git Patch 导出
./git_tools/export_commits_to_patches.sh -n 10 -d patches -a "author_name"

# Git Commit 批量修改（会重写历史，谨慎使用）
./git_tools/batch_modify_git_commits.sh ./myrepo "Old Name" "New Name" "new@example.com"

# AVIF 批量转 PNG
python3 media_tools/avif_to_png_converter.py /path/to/avif -o /path/to/output -r

# Kindle 图像转换
./kindle-wallpaper-tool/run_kindle_converter.sh /path/to/images -m scribe -o /output
./kindle-wallpaper-tool/run_kindle_converter.sh --list   # 列出支持的设备型号

# Claude CLI API 主机替换（用于代理）
API_HOST=your-proxy-host ./fix_any2.sh

# SSL 证书检查
python3 net_tools/ssl_cert_check.py example.com github.com

# HTTP 健康检测
python3 net_tools/http_health_check.py https://example.com https://api.example.com

# TODO/FIXME 收集
python3 dev_tools/todo_collector.py <directory> -g tag

# 代码行数统计
python3 dev_tools/loc_counter.py <directory> --top 10

# 文本编解码
python3 other_tools/text_convert.py b64enc "hello"
python3 other_tools/text_convert.py ts2date 1700000000
echo "encoded" | python3 other_tools/text_convert.py b64dec

# CSV 快速统计
python3 other_tools/csv_quick_stats.py data.csv

# 目录树可视化
python3 file_management/tree_view.py <directory> -d 3 -s

# 查看监听端口
python3 system_utilities/listening_ports.py -p 8080

# Crontab 备份与恢复
./system_utilities/crontab_backup.sh backup
./system_utilities/crontab_backup.sh list
```

## Testing

最小化测试基础设施：
- `android_tools/test_so_analyzer.py` — SO 分析器基础测试
- `android_tools/test_hash_both.so` — 测试用样本二进制文件
- 运行测试：`python3 android_tools/test_so_analyzer.py`

无全局构建系统、测试框架或 Linter，脚本单独运行。

## Dependencies

**Python 可选依赖：**
- `tqdm` — 进度条（`file_management/`）
- `colorama` — 彩色输出（`file_management/`）
- `send2trash` — 安全删除到回收站（非 macOS 时需要）
- `Pillow>=11.3.0` + `pillow-avif-plugin` — 图像处理（`media_tools/`, `kindle-wallpaper-tool/`）

**系统命令依赖（按目录）：**
- `android_tools/`: `readelf`/`llvm-readelf`, `objdump`/`llvm-objdump`, `strings`, `file`
- `system_utilities/`: `md5sum`（Linux）或 `md5`/`openssl dgst -md5`（macOS），`lsof`（macOS）或 `ss`（Linux）
- `git_tools/`: `git`（含 `filter-branch` 支持）
- `file_management/`: `trash`（可选，macOS）, `docker`（可选）, `brew`（可选）

## Conventions

- **语言**: 文档使用简体中文；代码注释中英混用
- **新工具**: 放入最匹配的分类目录
- **文档**: 每个工具配备 `xxx.md` 或更新该目录的 `README.md`
- **根 README.md**: 仅保留导航和入口，不堆叠实现细节
- **平台**: 脚本面向 macOS/Linux；部分依赖平台特定命令（`md5sum` vs `md5`，GNU `find`）
- **依赖最小化**: Python 脚本优先使用标准库
- **危险操作**: `batch_modify_git_commits.sh` 会重写 Git 历史，使用前自动备份，但仍需谨慎
- **License**: Apache 2.0（`kindle-wallpaper-tool/` 子项目为 MIT）

## Directory-Specific Notes

### android_tools/
- 主分析工具 `android_so_analyzer.py` 输出：文件基本信息、ELF 结构、依赖库、符号表、Android 优化检查（16KB 页对齐、GNU Hash、NDK 版本）
- `check_android_so.py` 为快速版，仅验证关键链接器选项

### file_management/
- `duplicate_finder.py` 按文件大小 + MD5 双重匹配，支持智能识别副本命名模式（`(1)`, `副本`, `copy`, `复制`）
- `move_build_dirs_trash_v4.sh` 为当前推荐版本（带干运行和大小统计）
- 清理操作默认移入回收站，不永久删除

### git_tools/
- `export_commits_to_patches.sh` 支持 `-a` 按作者过滤、`-s` 跳过最新 N 个 commit
- `batch_modify_git_commits.sh` 使用 `git filter-branch` 重写历史，执行前自动创建 `.bak` 备份

### kindle-wallpaper-tool/
- 独立子项目，有自己的 `requirements.txt` 和多语言文档（中/英）
- 支持 Kindle 基础款、Paperwhite（1-6代）、Oasis（1-3代）、Scribe、Colorsoft 共 20+ 型号
- 安装依赖：`./kindle-wallpaper-tool/setup_kindle_converter.sh`

### fix_any.sh / fix_any2.sh（根目录）
- 用于将 Claude CLI（`@anthropic-ai/claude-code`）中硬编码的 `api.anthropic.com` 替换为自定义代理主机
- `fix_any2.sh` 为推荐版，正确处理 pnpm 包装脚本和软链接解析
- 使用：`API_HOST=your-proxy.example.com ./fix_any2.sh`（默认主机为 `anyrouter.top`）
