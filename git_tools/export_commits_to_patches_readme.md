# Git Commit 导出工具

这个脚本用于从 Git 仓库中逐个导出指定数量的 commit 为独立的 patch 文件，支持按作者过滤。

## 功能特点

- 将多个 commit 分别导出为单独的 patch 文件
- 支持按作者过滤 commit
- 支持设置输出目录
- 支持跳过最近的 N 个 commit
- 自动生成有序且包含提交信息的文件名

## 使用方法

```bash
./export_commits_to_patches.sh [选项]
```

### 选项说明

| 选项 | 说明 |
|------|------|
| `-n, --number NUM` | 导出最近 NUM 个 commit (默认: 5) |
| `-d, --directory DIR` | 存储 patch 文件的目录 (默认: patches) |
| `-s, --skip NUM` | 跳过最新的 NUM 个 commit (默认: 0) |
| `-a, --author NAME` | 只导出指定作者的 commit (默认: xiebaiyuan) |
| `-A, --all-authors` | 导出所有作者的 commit (覆盖 -a 选项) |
| `-h, --help` | 显示帮助信息 |

## 使用示例

### 基本使用

默认导出指定作者（xiebaiyuan）的最近 5 个 commit：

```bash
./export_commits_to_patches.sh
```

### 指定数量

导出最近 10 个 commit：

```bash
./export_commits_to_patches.sh -n 10
```

### 指定输出目录

将 patch 文件保存到自定义目录：

```bash
./export_commits_to_patches.sh -d my_patches
```

### 跳过最新 commit

跳过最新的 2 个 commit，导出之后的 5 个：

```bash
./export_commits_to_patches.sh -s 2
```

### 指定作者

导出特定作者的 commit：

```bash
./export_commits_to_patches.sh -a "other_username"
```

### 导出所有作者的 commit

```bash
./export_commits_to_patches.sh --all-authors
```

### 组合使用

```bash
./export_commits_to_patches.sh -n 8 -d feature_patches -s 1 -a "developer_name"
```

## 输出格式

生成的 patch 文件名格式为：`[序号]_[提交信息]_[commit哈希前7位].patch`

例如：

- `001_fix_memory_leak_abcd123.patch`
- `002_update_documentation_efgh456.patch`

## 注意事项

- 确保在 Git 仓库目录中运行脚本
- 脚本执行前会清空输出目录中的现有 .patch 文件
- 提交信息中的特殊字符会被下划线替换，以确保文件名有效
