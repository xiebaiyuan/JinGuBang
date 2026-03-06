# WUKONG_TOOLS

一个按场景分类的实用脚本仓库，覆盖文件管理、Git 操作、媒体处理、网络检测、系统维护和 Android SO 分析等常见开发任务。

## 特性

- 按目录分组，结构清晰
- 每个子目录有入口文档（`README.md`）
- 以脚本为主，依赖少，便于本地快速使用
- 面向“日常可复用”场景，而非单次实验脚本

## 快速开始

```bash
# 1) 克隆仓库
git clone <your-repo-url> wukong_tools
cd wukong_tools

# 2) 给 shell 脚本执行权限（可选）
chmod +x system_utilities/*.sh file_management/*.sh git_tools/*.sh media_tools/*.sh other_tools/*.sh

# 3) 查看各目录说明
open README.md
```

## 目录导航

### 1) Android Tools

- 目录: `android_tools/`
- 入口: `android_tools/README.md`
- 适用场景: Android native 库（SO/ELF）结构分析、链接优化检查

### 2) File Management

- 目录: `file_management/`
- 入口: `file_management/README.md`
- 适用场景: 重复文件分析、文件整理、构建目录清理

### 3) Git Tools

- 目录: `git_tools/`
- 入口: `git_tools/README.md`
- 适用场景: patch 导出、仓库维护、fork 同步

### 4) Media Tools

- 目录: `media_tools/`
- 入口: `media_tools/README.md`
- 适用场景: 图片格式转换、Markdown 资源收集、EXIF 处理

### 5) Net Tools

- 目录: `net_tools/`
- 入口: `net_tools/README.md`
- 适用场景: 端口连通性基础检测

### 6) System Utilities

- 目录: `system_utilities/`
- 入口: `system_utilities/README.md`
- 适用场景: 本机环境维护、批量文件哈希计算

### 7) Other Tools

- 目录: `other_tools/`
- 入口: `other_tools/README.md`
- 适用场景: 其他不易归类但常用的小工具

### 8) Kindle Wallpaper Tool

- 目录: `kindle-wallpaper-tool/`
- 入口: `kindle-wallpaper-tool/README.md`
- 说明: 相对独立的子项目，保留其独立文档结构

## 常用工具推荐

### 批量计算目录文件 MD5（新增）

- 脚本: `system_utilities/batch_file_md5.sh`
- 文档: `system_utilities/batch_file_md5.md`

```bash
# 递归计算当前目录全部文件 MD5
./system_utilities/batch_file_md5.sh

# 计算 build 目录下所有 .so 文件并显示文件数
./system_utilities/batch_file_md5.sh -d ./build -i "*.so" --count

# 导出为 CSV
./system_utilities/batch_file_md5.sh -d . -c -o md5_report.csv
```

### Android SO 分析

```bash
python3 android_tools/android_so_analyzer.py android_tools/test_hash_both.so
```

## 维护约定

- 新增工具请放入最匹配的分类目录
- 为新工具补充对应文档（建议 `xxx.md` 或目录 `README.md`）
- 根目录 `README.md` 保留“导航 + 使用入口”定位，不堆叠过细实现细节

## 兼容性说明

- 多数脚本在 macOS / Linux 可用
- 个别脚本依赖系统命令（如 `find`、`md5sum/md5`、`git`）
- 若脚本依赖特定运行环境，请在对应目录文档中说明

## Disclaimer

These scripts are provided "as is" without any warranties or guarantees. Use them at your own risk. Test in a safe environment before production usage.
