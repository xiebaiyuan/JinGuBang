#!/bin/bash
set -e  # 当命令出错时退出脚本

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# 日志文件
LOG_FILE="/Users/$(whoami)/Downloads/clean_$(date +%Y%m%d_%H%M%S).log"

# 函数定义
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
    echo -e "${GREEN}$1${NC}"
}

format_size() {
    local size=$1
    if [ $size -ge 1048576 ]; then
        printf "${RED}%.2f GB${NC}" $(echo "scale=2; $size/1048576" | bc)
    elif [ $size -ge 1024 ]; then
        printf "${YELLOW}%.2f MB${NC}" $(echo "scale=2; $size/1024" | bc)
    else
        echo "$size KB"
    fi
}

show_help() {
    echo "用法：$0 目标目录 [选项] [额外的目录模式...]"
    echo "选项："
    echo "  --dry-run       模拟运行，不实际删除文件"
    echo "  --no-confirm    不需要确认直接删除"
    echo "  --help          显示此帮助信息"
    echo "  --exclude       排除指定模式的目录"
    echo "额外的目录模式会被添加到默认模式中"
}

# 检查 trash 命令
if ! command -v trash &> /dev/null; then
    echo -e "${RED}错误：未找到 'trash' 命令，请先安装。${NC}"
    echo "可以使用 'brew install trash' 进行安装。"
    exit 1
fi

# 初始化变量
target_dir=""
dry_run=false
no_confirm=false
extra_patterns=()
exclude_patterns=()

# 解析参数
while [[ $# -gt 0 ]]; do
    case "$1" in
        --dry-run) dry_run=true; shift ;;
        --no-confirm) no_confirm=true; shift ;;
        --help) show_help; exit 0 ;;
        --exclude) exclude_patterns+=("$2"); shift 2 ;;
        -*) echo "未知选项: $1" >&2; show_help; exit 1 ;;
        *)
            if [ -z "$target_dir" ]; then
                target_dir="$1"
            else
                extra_patterns+=("$1")
            fi
            shift
            ;;
    esac
done

# 检查目标目录
if [ -z "$target_dir" ]; then
    echo -e "${RED}错误：未提供目标目录${NC}" >&2
    show_help
    exit 1
fi

if [ ! -d "$target_dir" ]; then
    echo -e "${RED}错误：目标目录 $target_dir 不存在${NC}"
    exit 1
fi

# 默认模式
default_patterns=(
    'build' 'cmake-build-*' 'build.lite.*' 'build.macos.*' 'build.opt' 'tmp' 'CMakeFiles'
    'node_modules' 'dist' '.cache' '.tmp' '.sass-cache' 'coverage'
    'target' 'bin' 'obj' 'out' 'Debug' 'Release'
    '*.log'
)

# 合并模式
all_patterns=("${default_patterns[@]}" "${extra_patterns[@]}")

# 处理目录
process_dirs() {
    local name_args=() exclude_args=()
    for pattern in "${all_patterns[@]}"; do
        name_args+=(-name "$pattern" -o)
    done
    unset 'name_args[${#name_args[@]}-1]'

    for pattern in "${exclude_patterns[@]}"; do
        exclude_args+=(-not -path "*/$pattern/*")
    done

    find "$target_dir" \( "${name_args[@]}" \) "${exclude_args[@]}" -type d -print0
}

# 主要处理逻辑
echo -e "${YELLOW}警告：此脚本会删除匹配特定模式的目录。请确保您了解将要删除的内容。${NC}"

total_size=0
dirs=()
while IFS= read -r -d '' dir; do
    dirs+=("$dir")
done < <(process_dirs)

if [ ${#dirs[@]} -eq 0 ]; then
    echo -e "${YELLOW}未找到符合条件的目录。${NC}"
    exit 0
fi

echo -e "${GREEN}以下目录将被删除：${NC}"
for dir in "${dirs[@]}"; do
    size=$(du -sk "$dir" | awk '{print $1}')
    total_size=$((total_size + size))
    formatted_size=$(format_size $size)
    echo -e "${YELLOW}目录：${NC}$dir ${YELLOW}大小：${NC}$formatted_size"
done

echo -e "${GREEN}总计将删除的目录数量：${NC}${#dirs[@]}"
echo -e "${GREEN}总体积：${NC}$(format_size $total_size)"

if [ "$dry_run" = true ]; then
    echo -e "${YELLOW}(干运行模式，未实际删除)${NC}"
    exit 0
fi

if [ "$no_confirm" = false ]; then
    read -p "是否确认删除以上目录？输入 'yes' 确认：" confirm
    if [ "$confirm" != "yes" ]; then
        echo -e "${YELLOW}操作已取消。${NC}"
        exit 0
    fi
fi

log "开始删除操作"
for dir in "${dirs[@]}"; do
    echo -e "${GREEN}正在删除目录：${NC}$dir"
    if trash "$dir"; then
        log "成功删除目录：$dir"
    else
        log "删除失败：$dir"
    fi
done

log "删除操作完成"
echo -e "${GREEN}删除完成。日志已保存到 $LOG_FILE${NC}"
