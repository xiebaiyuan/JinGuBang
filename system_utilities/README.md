# System Utilities

用于系统环境巡检、哈希计算、资源快照等日常维护任务。

| 工具名 | 用途 | 使用示例 | 依赖 | 平台支持 | 风险级别 |
|---|---|---|---|---|---|
| `env_doctor.py` | 检测常见开发依赖与版本 | `python3 system_utilities/env_doctor.py` | Python 标准库 | 跨平台 | 低 |
| `batch_file_md5.sh` | 批量计算目录文件 MD5 | `bash system_utilities/batch_file_md5.sh -d . -i "*.so" --count` | `md5/md5sum/openssl` | macOS/Linux | 低 |
| `disk_usage_snapshot.sh` | 输出目录占用快照 | `bash system_utilities/disk_usage_snapshot.sh . -n 20 --human` | `du` | macOS/Linux | 低 |
| `process_top_watch.py` | 按 CPU/内存输出进程 TopN | `python3 system_utilities/process_top_watch.py --by cpu -n 10` | `ps` | macOS/Linux | 低 |
| `collect_ip.sh` | 收集本机网络 IP 信息 | `bash system_utilities/collect_ip.sh` | 系统网络命令 | macOS/Linux | 低 |
| `update_zsh_plugin.sh` | 更新 zsh 插件 | `bash system_utilities/update_zsh_plugin.sh` | zsh 生态命令 | macOS/Linux | 中 |
| `current_dir_so_md5.sh` | 历史 so 文件哈希辅助脚本 | `bash system_utilities/current_dir_so_md5.sh` | `md5/md5sum` | macOS/Linux | 低 |
| `listening_ports.py` | 查看系统监听端口与对应进程 | `python3 system_utilities/listening_ports.py` | `lsof`(macOS)/`ss`(Linux) | macOS/Linux | 低 |
| `crontab_backup.sh` | 备份/恢复/对比用户 crontab | `bash system_utilities/crontab_backup.sh backup` | Shell | macOS/Linux | 低 |

## 何时使用

- 空间排查用 `disk_usage_snapshot.sh`。
- 排查高占用进程用 `process_top_watch.py`。
- CI/发版前做环境基线用 `env_doctor.py`。
- 查看谁占用了端口用 `listening_ports.py`。
- 定时任务变更前用 `crontab_backup.sh backup` 备份。

## 相关文档

- `system_utilities/update_zsh_plugin.md`
- `system_utilities/batch_file_md5.md`
- `system_utilities/env_doctor.md`
