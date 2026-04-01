# TOOLS INDEX

统一检索入口，帮助你快速找到合适脚本。

## 按分类

- Android: `android_tools/README.md`
- 文件管理: `file_management/README.md`
- Git: `git_tools/README.md`
- 媒体处理: `media_tools/README.md`
- 网络: `net_tools/README.md`
- 系统维护: `system_utilities/README.md`
- 其他: `other_tools/README.md`
- Kindle 子项目: `kindle-wallpaper-tool/README.md`

## 按关键词

- SO/ELF 分析: `android_tools/android_so_analyzer.py`, `android_tools/check_android_so.py`, `android_tools/so_symbol_diff.py`
- APK/AAB Native 报告: `android_tools/apk_native_libs_report.py`
- 重复文件: `file_management/duplicate_finder.py`, `file_management/duplicate_file_analyzer.py`
- 大文件定位: `file_management/large_files_top.py`
- 自动整理文件: `file_management/smart_organize_by_type.py`
- 空目录清理: `file_management/empty_dirs_cleaner.sh`
- 分支健康检查: `git_tools/git_branch_health.sh`
- Commit 规范检查: `git_tools/conventional_commit_lint.py`
- Changelog 生成: `git_tools/changelog_from_git.py`
- 批量改图尺寸: `media_tools/image_batch_resize.py`
- 图片元数据报告: `media_tools/image_metadata_report.py`
- TCP 扫描: `net_tools/port_scan_tcp.py`
- DNS 报告: `net_tools/domain_dns_report.py`
- 磁盘占用快照: `system_utilities/disk_usage_snapshot.sh`
- 进程排行: `system_utilities/process_top_watch.py`
- JSON/YAML 转换: `other_tools/json_yaml_convert.py`

## 按语言

- Python: `android_tools/*.py`, `file_management/*.py`, `git_tools/*.py`, `media_tools/*.py`, `net_tools/*.py`, `system_utilities/*.py`, `other_tools/*.py`
- Shell: `file_management/*.sh`, `git_tools/*.sh`, `system_utilities/*.sh`, `media_tools/*.sh`
- HTML: `net_tools/port_checker.html`

## 按平台

- 跨平台（macOS/Linux 优先）: 大多数 Python 脚本
- macOS 偏向: `file_management/mac_cleaner.sh`
- 依赖系统命令: `git_tools/`, `system_utilities/disk_usage_snapshot.sh`, `android_tools/so_symbol_diff.py`

## 快速任务示例

```bash
# 查看目录中最大 20 个文件
python3 file_management/large_files_top.py -i . -n 20 --min-size 10M

# 检查当前仓库分支健康
bash git_tools/git_branch_health.sh --days 30

# 生成域名 DNS 摘要
python3 net_tools/domain_dns_report.py -d example.com --types A,AAAA,MX

# 生成 APK native 库报告
python3 android_tools/apk_native_libs_report.py -i app.apk --format text
```

## 验证记录

- 本索引与各目录 README 保持一致维护。
- 新工具加入时，必须同步更新本文件关键词和示例区块。
