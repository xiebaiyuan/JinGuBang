#!/bin/bash
USER=xiebaiyuan
EXCLUDE=("big-repo" "legacy-project")

SUCCESS=()
FAILED=()
SKIPPED=()

# 获取未归档的 fork 仓库
repos=$(gh repo list $USER --fork --limit 1000 --json name,isArchived -q '.[] | select(.isArchived == false) | .name')

for repo in $repos; do
    # 检查是否在排除名单
    if [[ " ${EXCLUDE[@]} " =~ " ${repo} " ]]; then
        echo "跳过仓库: $repo"
        SKIPPED+=("$repo")
        continue
    fi

    echo "正在同步仓库: $repo"
    if gh repo sync "$USER/$repo" >/tmp/sync_$repo.log 2>&1; then
        echo "✅ 同步成功: $repo"
        SUCCESS+=("$repo")
    else
        echo "❌ 同步失败: $repo (错误日志见 /tmp/sync_$repo.log)"
        FAILED+=("$repo")
    fi
done

echo
echo "==================== 总结 ===================="
echo "成功同步: ${#SUCCESS[@]} 个"
for r in "${SUCCESS[@]}"; do echo "  - $r"; done

echo
echo "失败: ${#FAILED[@]} 个"
for r in "${FAILED[@]}"; do echo "  - $r"; done

echo
echo "跳过: ${#SKIPPED[@]} 个"
for r in "${SKIPPED[@]}"; do echo "  - $r"; done