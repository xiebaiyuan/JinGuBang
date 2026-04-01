# WUKONG_TOOLS

一个按场景分类的实用脚本仓库，覆盖 Android 分析、文件管理、Git 操作、媒体处理、网络检测和系统维护。

## 快速入口

- 全局索引：`TOOLS_INDEX.md`
- 贡献规范：`docs/CONTRIBUTING_TOOLS.md`
- Android：`android_tools/README.md`
- 文件管理：`file_management/README.md`
- Git：`git_tools/README.md`
- 媒体处理：`media_tools/README.md`
- 网络：`net_tools/README.md`
- 系统维护：`system_utilities/README.md`
- 其他：`other_tools/README.md`
- Kindle 子项目：`kindle-wallpaper-tool/README.md`

## 30 秒常用命令

```bash
# 定位大文件
python3 file_management/large_files_top.py -i . -n 20 --min-size 10M

# 检查 Git 分支健康
bash git_tools/git_branch_health.sh --days 30

# 生成 DNS 摘要
python3 net_tools/domain_dns_report.py -d example.com

# 查看系统环境依赖
python3 system_utilities/env_doctor.py
```

## 维护原则

- 新工具放入最匹配目录并同步更新对应 README
- 根 README 只保留导航和入口，不堆实现细节
- 优先低依赖实现，危险操作默认 dry-run 或明确确认

## 免责声明

These scripts are provided "as is" without warranties. Always test in a safe environment before production use.
