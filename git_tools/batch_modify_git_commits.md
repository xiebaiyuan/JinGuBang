# 批量修改 Git 提交信息脚本

这个脚本可以批量修改 Git 仓库中的提交作者信息（包括姓名和邮箱），并可选择在提交信息中添加特定内容以及修改提交日期。

## 功能

1. 修改历史提交中的作者姓名
2. 修改历史提交中的作者邮箱
3. 在所有提交信息中添加特定内容（可选）
4. 修改所有提交的日期（可选）
5. 自动备份原始仓库

## 使用方法

```bash
./batch_modify_git_commits.sh <repo_path> <old_name> <new_name> <new_email> [additional_commit_msg] [new_date]
```

### 参数说明

- `repo_path`: Git 仓库的路径
- `old_name`: 需要修改的原作者姓名
- `new_name`: 新的作者姓名
- `new_email`: 新的作者邮箱
- `additional_commit_msg`: （可选）要在所有提交信息中添加的内容
- `new_date`: （可选）新的提交日期，格式为 "YYYY-MM-DD HH:MM:SS"

### 示例

```bash
# 基本用法：只修改作者姓名和邮箱
./batch_modify_git_commits.sh ./myrepo "Old Name" "New Name" "new@example.com"

# 高级用法：同时修改作者信息并在提交信息中添加内容
./batch_modify_git_commits.sh ./myrepo "Old Name" "New Name" "new@example.com" "[Updated by script]"

# 完整用法：修改作者信息、添加内容并设置新的提交日期
./batch_modify_git_commits.sh ./myrepo "Old Name" "New Name" "new@example.com" "[Updated by script]" "2023-01-01 12:00:00"
```

## 注意事项

1. 脚本会自动创建仓库的完整备份，位于仓库上一级目录中，文件名为 `repo_backup_<timestamp>`
2. 修改完成后，需要手动推送更改到远程仓库：
   ```bash
   git push origin --force --all
   git push origin --force --tags
   ```
3. 此操作会重写 Git 历史，请确保在执行前已通知团队成员，并确认这是你真正想要的操作
4. 对于大型仓库，此操作可能需要较长时间完成
5. 修改提交日期时，请确保使用正确的日期格式：`"YYYY-MM-DD HH:MM:SS"`

## 依赖

- Git（内置的 `git filter-branch` 命令）

## 工作原理

脚本使用 Git 内置的 `git filter-branch` 命令来重写 Git 历史。虽然 `git-filter-repo` 是更现代的工具，但在某些系统配置下可能遇到兼容性问题，因此我们选择使用更广泛的 `git filter-branch`。

### 环境变量过滤

脚本使用 `--env-filter` 选项来修改提交的作者、提交者信息以及提交日期：
```bash
if [ "$GIT_AUTHOR_NAME" = "$OLD_NAME" ]; then
    export GIT_AUTHOR_NAME="$NEW_NAME"
    export GIT_AUTHOR_EMAIL="$NEW_EMAIL"
fi

if [ "$GIT_COMMITTER_NAME" = "$OLD_NAME" ]; then
    export GIT_COMMITTER_NAME="$NEW_NAME"
    export GIT_COMMITTER_EMAIL="$NEW_EMAIL"
fi

# 如果指定了新日期
if [ -n "$NEW_DATE" ]; then
    export GIT_AUTHOR_DATE="$NEW_DATE"
    export GIT_COMMITTER_DATE="$NEW_DATE"
fi
```

### 提交信息过滤

如果提供了额外的提交信息，脚本会使用 `--msg-filter` 选项来修改提交信息：
```bash
# 读取原始提交信息
ORIGINAL_MESSAGE=$(cat)
# 添加额外信息
echo "$ORIGINAL_MESSAGE

$ADDITIONAL_MSG"
```

这种方法确保了所有历史提交都会被正确修改。