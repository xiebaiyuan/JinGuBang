
## 完整使用示例

	1.	查看帮助：

./move_build_dirs_trash.sh
用法：./move_build_dirs_trash.sh 目标目录 [--dry-run] [额外的目录模式...]


	2.	干运行模式，删除默认模式的目录：

./move_build_dirs_trash.sh /path/to/dir --dry-run


	3.	干运行模式，删除默认模式和 .cxx 目录：

./move_build_dirs_trash.sh /path/to/dir --dry-run .cxx


	4.	实际删除模式，删除默认模式和多个额外目录：

./move_build_dirs_trash.sh /path/to/dir .cxx .vs .idea

	•	注意：实际删除操作会提示确认，输入 yes 才会执行删除。


---


# 构建目录清理脚本 (v2)

这个 Bash 脚本用于清理项目中的构建目录和临时文件。它可以帮助你快速删除常见的构建输出、依赖缓存和临时文件，从而释放磁盘空间。

## 功能

- 自动查找并删除指定模式的目录和文件
- 支持自定义额外的目录和文件模式
- 可以排除特定目录或文件
- 支持白名单目录（如 .git 和 .mgit）
- 提供干运行模式以预览将要删除的内容
- 可选的无确认模式用于自动化场景
- 详细的日志记录
- 彩色输出以提高可读性
- 按父目录分组显示要删除的项目

## 使用方法
bash
./move_build_dirs_trash_v2.sh 目标目录 [选项] [额外的模式...]


### 选项

- `--dry-run`: 模拟运行，显示将要删除的目录但不实际删除
- `--no-confirm`: 跳过确认步骤，直接执行删除操作
- `--help`: 显示帮助信息
- `--exclude <pattern>`: 排除匹配指定模式的目录或文件
- `--file <pattern>`: 添加文件匹配模式
- `--whitelist-dir <dir>`: 添加白名单目录（默认包括 .git 和 .mgit）

### 示例

1. 基本用法：
   ```bash
   ./move_build_dirs_trash_v2.sh /path/to/project
   ```

2. 使用干运行模式：
   ```bash
   ./move_build_dirs_trash_v2.sh /path/to/project --dry-run
   ```

3. 添加额外的目录模式：
   ```bash
   ./move_build_dirs_trash_v2.sh /path/to/project "temp_*" "old_build"
   ```

4. 排除特定目录：
   ```bash
   ./move_build_dirs_trash_v2.sh /path/to/project --exclude important_build --exclude config
   ```

5. 添加文件模式：
   ```bash
   ./move_build_dirs_trash_v2.sh /path/to/project --file "*.tmp"
   ```

6. 添加白名单目录：
   ```bash
   ./move_build_dirs_trash_v2.sh /path/to/project --whitelist-dir .svn
   ```

7. 无确认模式：
   ```bash
   ./move_build_dirs_trash_v2.sh /path/to/project --no-confirm
   ```

## 默认清理模式

脚本默认会查找并删除以下模式的目录和文件：

### 目录
- `build`, `cmake-build-*`, `build.lite.*`, `build.macos.*`, `build.opt`, `tmp`, `CMakeFiles`
- `node_modules`, `dist`, `.cache`, `.tmp`, `.sass-cache`, `coverage`
- `target`, `obj`, `out`, `Debug`, `Release`

### 文件
- `*.log`

## 注意事项

- 使用此脚本前，请确保您了解将要删除的内容。
- 强烈建议首先使用 `--dry-run` 选项来预览将要删除的目录和文件。
- 脚本使用 `trash` 命令而不是 `rm`，以提供额外的安全性。请确保已安装 `trash` 命令。
- 删除操作的日志会保存在 `/Users/<username>/Downloads/` 目录下。

## 要求

- Bash shell
- `trash` 命令（可通过 `brew install trash` 安装）

## 安全性

虽然脚本设计时考虑了安全性，但在使用时仍需谨慎。请确保：

1. 在执行实际删除操作前，先使用 `--dry-run` 选项。
2. 定期备份重要数据。
3. 仔细检查将要删除的目录和文件列表，确保不会意外删除重要文件。

## 贡献

欢迎提交 Issues 和 Pull Requests 来改进这个脚本。

## 许可

[MIT License](LICENSE)