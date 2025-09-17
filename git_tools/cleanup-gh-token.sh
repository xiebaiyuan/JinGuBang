#!/bin/bash
# cleanup-gh-token.sh
# 自动检测并清理 GITHUB_TOKEN / GH_TOKEN

CONFIG_FILES=(~/.bashrc ~/.zshrc ~/.bash_profile ~/.zprofile)

echo "🔍 检查环境变量..."
if [ -n "$GITHUB_TOKEN" ] || [ -n "$GH_TOKEN" ]; then
    echo "⚠️  当前环境变量中有 GitHub Token:"
    [ -n "$GITHUB_TOKEN" ] && echo "  - GITHUB_TOKEN=$GITHUB_TOKEN"
    [ -n "$GH_TOKEN" ] && echo "  - GH_TOKEN=$GH_TOKEN"

    echo "🧹 临时清除环境变量..."
    unset GITHUB_TOKEN
    unset GH_TOKEN
else
    echo "✅ 当前环境变量中没有 GitHub Token"
fi

echo
echo "🔍 检查常见配置文件..."
for f in "${CONFIG_FILES[@]}"; do
    if [ -f "$f" ]; then
        if grep -q "GITHUB_TOKEN" "$f" || grep -q "GH_TOKEN" "$f"; then
            echo "⚠️  在 $f 中找到 GitHub Token 配置:"
            grep -nE "GITHUB_TOKEN|GH_TOKEN" "$f"

            echo "👉 请手动编辑 $f，把相关 export 行注释掉："
            echo "   nano $f   # 或 vim $f"
        else
            echo "✅ $f 中未找到相关配置"
        fi
    fi
done

echo
echo "🎯 完成。现在你可以重新运行："
echo "   gh auth login"
