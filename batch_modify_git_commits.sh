#!/bin/bash

# 脚本用于批量修改 Git 仓库中的提交作者信息和提交信息
# 使用 git filter-branch 工具实现（兼容性更好）

# 检查参数
if [ $# -lt 4 ]; then
    echo "用法: $0 <repo_path> <old_name> <new_name> <new_email> [additional_commit_msg]"
    echo "示例: $0 ./myrepo \"Old Name\" \"New Name\" \"new@example.com\" \"[Updated by script]\""
    exit 1
fi

REPO_PATH="$1"
OLD_NAME="$2"
NEW_NAME="$3"
NEW_EMAIL="$4"
ADDITIONAL_MSG="${5:-}"

# 检查仓库路径是否存在
if [ ! -d "$REPO_PATH/.git" ]; then
    echo "错误: $REPO_PATH 不是一个有效的 Git 仓库"
    exit 1
fi

# 进入仓库目录
cd "$REPO_PATH" || exit 1

# 备份原始仓库（可选但推荐）
echo "正在创建仓库备份..."
git clone --mirror . ../repo_backup_$(date +%s)
echo "备份已创建在 ../repo_backup_*"

# 设置环境变量用于过滤
export OLD_NAME NEW_NAME NEW_EMAIL ADDITIONAL_MSG

# 创建过滤脚本
cat > /tmp/filter_script.sh << 'EOF'
#!/bin/bash

# 修改作者和提交者信息
if [ "$GIT_AUTHOR_NAME" = "$OLD_NAME" ]; then
    export GIT_AUTHOR_NAME="$NEW_NAME"
    export GIT_AUTHOR_EMAIL="$NEW_EMAIL"
fi

if [ "$GIT_COMMITTER_NAME" = "$OLD_NAME" ]; then
    export GIT_COMMITTER_NAME="$NEW_NAME"
    export GIT_COMMITTER_EMAIL="$NEW_EMAIL"
fi

# 如果需要添加额外信息到提交信息
if [ -n "$ADDITIONAL_MSG" ]; then
    # 读取原始提交信息
    ORIGINAL_MESSAGE=$(cat)
    # 添加额外信息
    echo "$ORIGINAL_MESSAGE
    
$ADDITIONAL_MSG"
else
    # 不修改提交信息
    cat
fi
EOF

chmod +x /tmp/filter_script.sh

# 执行过滤操作
echo "正在修改提交历史..."
if [ -n "$ADDITIONAL_MSG" ]; then
    git filter-branch --force --env-filter "
        if [ \"\$GIT_AUTHOR_NAME\" = \"$OLD_NAME\" ]; then
            export GIT_AUTHOR_NAME=\"$NEW_NAME\"
            export GIT_AUTHOR_EMAIL=\"$NEW_EMAIL\"
        fi
        
        if [ \"\$GIT_COMMITTER_NAME\" = \"$OLD_NAME\" ]; then
            export GIT_COMMITTER_NAME=\"$NEW_NAME\"
            export GIT_COMMITTER_EMAIL=\"$NEW_EMAIL\"
        fi
    " --msg-filter "/tmp/filter_script.sh" --tag-name-filter cat -- --all
else
    git filter-branch --force --env-filter "
        if [ \"\$GIT_AUTHOR_NAME\" = \"$OLD_NAME\" ]; then
            export GIT_AUTHOR_NAME=\"$NEW_NAME\"
            export GIT_AUTHOR_EMAIL=\"$NEW_EMAIL\"
        fi
        
        if [ \"\$GIT_COMMITTER_NAME\" = \"$OLD_NAME\" ]; then
            export GIT_COMMITTER_NAME=\"$NEW_NAME\"
            export GIT_COMMITTER_EMAIL=\"$NEW_EMAIL\"
        fi
    " --tag-name-filter cat -- --all
fi

# 清理临时文件
rm -f /tmp/filter_script.sh

# 移除备份引用
git for-each-ref --format="%(refname)" refs/original/ | xargs -n 1 git update-ref -d

# 过期对象清理
git reflog expire --expire=now --all
git gc --prune=now

echo "提交历史修改完成！"
echo "请检查修改结果，如果满意请推送更改："
echo "git push origin --force --all"
echo "git push origin --force --tags"