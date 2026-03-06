# Batch File MD5

批量计算目录内文件 MD5 的脚本，支持递归、过滤、排序、CSV 导出等常见需求。

## 脚本位置

- `system_utilities/batch_file_md5.sh`

## 功能

- 递归或非递归扫描目录
- 按文件名模式包含/排除
- 按路径或 MD5 排序
- 支持普通文本输出与 CSV 输出
- 可输出绝对路径
- 可写入文件并显示文件总数

## 用法

```bash
./batch_file_md5.sh [options]
```

## 选项

- `-d, --dir <path>`: 目标目录（默认 `.`）
- `-n, --non-recursive`: 仅扫描当前层，不递归
- `-i, --include <pattern>`: 包含模式（如 `"*.so"`）
- `-e, --exclude <pattern>`: 排除模式（如 `"*.log"`）
- `-s, --sort <mode>`: 排序方式 `path|md5|none`（默认 `path`）
- `-c, --csv`: 输出 CSV
- `-o, --output <file>`: 写入输出文件
- `-a, --absolute`: 输出绝对路径
- `--count`: 在 stderr 输出总文件数
- `-h, --help`: 显示帮助

## 示例

```bash
# 递归计算当前目录全部文件
./batch_file_md5.sh

# 仅计算 so 文件并显示数量
./batch_file_md5.sh -d ./build -i "*.so" --count

# 非递归扫描，按 MD5 排序并输出到文件
./batch_file_md5.sh -d ./dist -n -s md5 -o md5_report.txt

# 排除日志文件并导出 CSV
./batch_file_md5.sh -d . -e "*.log" -c -o md5_report.csv
```

## 兼容性

脚本会优先尝试以下命令计算 MD5：

1. `md5sum`
2. `md5`
3. `openssl dgst -md5`

因此可在常见 Linux/macOS 环境运行。
