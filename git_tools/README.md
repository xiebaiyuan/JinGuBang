# Git Tools

用于仓库维护、提交流程规范化和发布辅助。

| 工具名 | 用途 | 使用示例 | 依赖 | 平台支持 | 风险级别 |
|---|---|---|---|---|---|
| `export_commits_to_patches.sh` | 导出 commit 为 patch 文件 | `bash git_tools/export_commits_to_patches.sh -n 10 -d patches` | git | macOS/Linux | 低 |
| `git_branch_health.sh` | 检查分支健康（已合并/陈旧/主干差异） | `bash git_tools/git_branch_health.sh --days 30` | git | macOS/Linux | 低 |
| `conventional_commit_lint.py` | 校验 commit message 是否符合约定格式 | `python3 git_tools/conventional_commit_lint.py --last 20 --strict` | git（`--last` 模式） | 跨平台 | 低 |
| `changelog_from_git.py` | 从 git log 生成 changelog | `python3 git_tools/changelog_from_git.py --from v1.0.0 --to HEAD` | git | 跨平台 | 低 |
| `batch_modify_git_commits.sh` | 批量修改 commit 历史信息 | `bash git_tools/batch_modify_git_commits.sh ./repo "A" "B" "b@x.com"` | git | macOS/Linux | 高 |
| `cleanup-gh-token.sh` | 清理 GitHub token 相关残留配置 | `bash git_tools/cleanup-gh-token.sh` | git | macOS/Linux | 中 |
| `git_so_md5.sh` | Git 场景下 so 文件哈希辅助 | `bash git_tools/git_so_md5.sh` | git, md5/md5sum | macOS/Linux | 低 |
| `list_big_repo.sh` | 识别大仓库/大对象 | `bash git_tools/list_big_repo.sh` | git | macOS/Linux | 低 |
| `sync_forks.sh` | 同步 fork 仓库主干 | `bash git_tools/sync_forks.sh` | git | macOS/Linux | 中 |

## 何时使用

- 合并前先跑 `git_branch_health.sh` 检查陈旧分支。
- 团队统一提交规范时跑 `conventional_commit_lint.py`。
- 发布说明草稿可先用 `changelog_from_git.py` 自动生成。

## 相关文档

- `git_tools/export_commits_to_patches_readme.md`
- `git_tools/batch_modify_git_commits.md`
