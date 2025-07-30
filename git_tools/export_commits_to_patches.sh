#!/bin/zsh
# export_commits_to_patches.sh
# 将 git 仓库中的 N 个最新 commit 逐个导出为 patch 文件

# 显示脚本使用方法
show_usage() {
    echo "用法: $0 [选项]"
    echo "选项:"
    echo "  -n, --number NUM    导出最近 NUM 个 commit (默认: 5)"
    echo "  -d, --directory DIR  存储 patch 文件的目录 (默认: patches)"
    echo "  -s, --skip NUM       跳过最新的 NUM 个 commit (默认: 0)"
    echo "  -a, --author NAME    只导出指定作者的 commit (默认: xiebaiyuan)"
    echo "  -A, --all-authors    导出所有作者的 commit (覆盖 -a 选项)"
    echo "  -h, --help           显示此帮助信息"
}

# 设置默认值
COMMITS_COUNT=5
OUTPUT_DIR="patches"
SKIP_COUNT=0
AUTHOR="xiebaiyuan"
FILTER_AUTHOR=true

# 解析命令行参数
while [[ $# -gt 0 ]]; do
    case "$1" in
        -n|--number)
            COMMITS_COUNT="$2"
            shift 2
            ;;
        -d|--directory)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        -s|--skip)
            SKIP_COUNT="$2"
            shift 2
            ;;
        -a|--author)
            AUTHOR="$2"
            FILTER_AUTHOR=true
            shift 2
            ;;
        -A|--all-authors)
            FILTER_AUTHOR=false
            shift
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            echo "错误: 未知参数 $1"
            show_usage
            exit 1
            ;;
    esac
done

# 确保在 git 仓库中执行
if ! git rev-parse --is-inside-work-tree > /dev/null 2>&1; then
    echo "错误: 当前目录不是 git 仓库"
    exit 1
fi

# 创建输出目录
mkdir -p "$OUTPUT_DIR"
if [ ! -d "$OUTPUT_DIR" ]; then
    echo "错误: 无法创建目录 $OUTPUT_DIR"
    exit 1
fi

# 清理旧的 patch 文件
echo "清理目录 $OUTPUT_DIR 中的旧 patch 文件..."
rm -f "$OUTPUT_DIR"/*.patch

# 构建 git log 命令
if [ "$FILTER_AUTHOR" = true ]; then
    echo "获取作者 '$AUTHOR' 的最近 $COMMITS_COUNT 个 commit (跳过 $SKIP_COUNT 个)..."
    GIT_LOG_CMD="git log --skip=$SKIP_COUNT -n $COMMITS_COUNT --author=\"$AUTHOR\" --format=\"%H\""
else
    echo "获取所有作者的最近 $COMMITS_COUNT 个 commit (跳过 $SKIP_COUNT 个)..."
    GIT_LOG_CMD="git log --skip=$SKIP_COUNT -n $COMMITS_COUNT --format=\"%H\""
fi

# 获取提交数量
TOTAL_COMMITS=$(eval "$GIT_LOG_CMD" | wc -l | tr -d ' ')
echo "找到 $TOTAL_COMMITS 个 commit 将导出为 patch 文件"

# 逐个导出 commit 为 patch
COUNTER=1
eval "$GIT_LOG_CMD" | while read COMMIT; do
    if [ -z "$COMMIT" ]; then
        continue  # 跳过空行
    fi
    
    # 去除可能的引号
    COMMIT=$(echo "$COMMIT" | tr -d '"')
    
    # 获取提交信息的第一行作为文件名
    COMMIT_MSG=$(git log -n 1 --pretty=format:"%s" "$COMMIT" | sed 's/[^a-zA-Z0-9._-]/_/g')
    # 限制文件名长度
    COMMIT_MSG=$(echo "$COMMIT_MSG" | cut -c 1-50)
    
    # 构建有序文件名（添加前导零以便按字母顺序正确排序）
    PADDED_NUM=$(printf "%03d" $COUNTER)
    FILENAME="${OUTPUT_DIR}/${PADDED_NUM}_${COMMIT_MSG}_${COMMIT:0:7}.patch"
    
    echo "[$COUNTER/$TOTAL_COMMITS] 导出 commit ${COMMIT:0:7}..."
    # 导出单个 commit 为 patch 文件
    git format-patch -1 "$COMMIT" --stdout > "$FILENAME"
    
    COUNTER=$((COUNTER + 1))
done

# 因为我们在管道中运行了 while 循环，COUNTER 可能不会正确更新
# 所以我们通过计算文件数量来获取实际导出的 patch 数量
EXPORTED_COUNT=$(ls -1 "$OUTPUT_DIR"/*.patch 2>/dev/null | wc -l | tr -d ' ')

echo "完成! 所有 patch 文件已导出至 $OUTPUT_DIR 目录"
echo "共导出 $EXPORTED_COUNT 个 patch 文件"

# 列出生成的 patch 文件
ls -1 "$OUTPUT_DIR"
