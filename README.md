# WUKONG_TOOLS

## Tools for my daily work. Powerful as Wukong.

### 1. Collect markdown images
python collect_md.py demo.md -o md_images -d /Users/xiebaiyuan/Documents/md_collects/

### 2. Move build directories to trash
see [clean_build_readme.md](docs/clean_build_readme.md)

### 3. Export Git commits to patches
see [export_commits_to_patches_readme.md](docs/export_commits_to_patches_readme.md)

### 3. Export Git commits to patches
see [export_commits_to_patches_readme.md](docs/export_commits_to_patches_readme.md)

### 3. 重复文件查找器 (Duplicate Finder)

这是一个用于查找和移除文件系统中重复文件的命令行工具，它能够帮助您节省存储空间，保持文件系统整洁。

#### 特点

- 默认在同一目录内查找重复文件，避免误删不同文件夹中的内容相同但用途不同的文件
- 可选择全局查找模式，在整个目录树中检测重复
- 通过文件大小和MD5哈希检测完全相同的文件
- 智能识别常见的副本文件命名模式
- 选项可以仅使用文件大小检测重复（不计算MD5哈希，速度更快）
- 将重复文件移动到系统回收站而非永久删除
- 彩色输出结果，便于查看
- 支持排除特定目录

#### 安装依赖

```bash
pip install tqdm colorama
# 在非macOS系统上还需要安装:
pip install send2trash
```

#### 使用方法

```bash
python duplicate_finder.py <目录路径> [选项]
```

##### 基本用法示例

```bash
# 扫描指定目录中的重复文件（默认只在同一目录内查找）
python duplicate_finder.py /path/to/directory

# 全局模式：在整个目录树中查找重复文件
python duplicate_finder.py /path/to/directory --global

# 扫描指定目录，排除特定子目录
python duplicate_finder.py /path/to/directory --exclude /path/to/exclude1 /path/to/exclude2

# 快速模式：只使用文件大小判断重复（不计算MD5）
python duplicate_finder.py /path/to/directory --size-only

# 自动确认删除而不提示
python duplicate_finder.py /path/to/directory --confirm

# 启用调试日志
python duplicate_finder.py /path/to/directory --debug
```

##### 命令行选项

| 选项 | 描述 |
|------|------|
| `--global` | 全局查找重复文件（默认只在同一目录内查找） |
| `--exclude [目录 ...]` | 排除指定的目录，不在其中查找重复文件 |
| `--confirm` | 自动确认删除而不提示 |
| `--debug` | 启用调试日志，显示更多程序运行信息 |
| `--size-only` | 仅基于文件大小判断重复（不计算MD5哈希值） |

#### 工作原理

1. **收集文件信息**：工具会递归扫描指定目录中的所有文件（排除隐藏文件和指定排除的目录）
2. **按大小分组**：将文件按照大小分组，只有大小相同的文件才可能是重复文件
   - 在默认模式下，仅在同一目录内的文件之间进行比较
   - 在全局模式下，整个目录树中的所有文件都会被比较
3. **计算MD5**：对于大小相同的文件，计算MD5哈希值以确认它们的内容是否完全相同
4. **智能选择原始文件**：通过文件命名特征判断哪个文件是原始文件，哪些是副本
5. **移动到回收站**：将确认的副本文件移动到系统回收站，原始文件保留不动

#### 查找策略

- **默认模式（同目录查找）**：只查找同一目录中的重复文件。这种模式更安全，避免误删不同目录中内容相同但用途不同的文件。
- **全局模式**：在整个目录树中查找所有重复文件，可能会发现更多重复但也可能误删有特定用途的文件。

#### 检测副本文件的命名模式

工具能识别以下常见的副本文件命名模式：

- `文件名 (1).扩展名`, `文件名(2).扩展名` 等
- `文件名 副本.扩展名`, `文件名副本2.扩展名` 等
- `文件名 copy.扩展名`, `文件名copy2.扩展名` 等
- `文件名 复制.扩展名`, `文件名复制2.扩展名` 等
- `文件名 1.扩展名`, `文件名 2.扩展名` 等

#### 提示与技巧

- 首次使用时建议使用默认模式（同目录查找），这样更安全
- 对于大型目录，可以使用 `--size-only` 选项以获得更快的结果
- 使用 `--debug` 选项可以看到更详细的处理过程
- 文件被移动到回收站后，您仍然可以从系统回收站恢复它们
- 处理大量文件时，请确保有足够的系统内存用于计算和存储文件哈希值

### 4. Duplicate File Analyzer

这是一个简单的重复文件分析工具，用于扫描目录并显示重复文件的信息，不进行任何删除操作。

#### 使用方法

```bash
python duplicate_file_analyzer.py <目录路径> [--size]
```

#### 基本用法示例

```bash
# 分析指定目录中的重复文件
python duplicate_file_analyzer.py /path/to/directory

# 显示文件大小信息
python duplicate_file_analyzer.py /path/to/directory --size
```

#### 特点

- 仅分析和显示重复文件信息，不执行任何删除操作
- 显示重复文件组及其哈希值
- 可选显示文件大小和潜在的存储节省空间
- 安全无害，适合首次扫描目录时使用

## Disclaimer: 
These scripts is untested and provided “as is” without any warranties or guarantees of any kind. Use it at your own risk. The author assumes no responsibility for any errors, omissions, or damages resulting from the use of this script. Please exercise caution and thoroughly test the script in a safe environment before deploying it in a production setting.