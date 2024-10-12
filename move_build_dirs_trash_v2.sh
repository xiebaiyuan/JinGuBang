#!/usr/bin/env bash
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
    echo "用法：$0 目标目录 [选项] [额外的模式...]"
    echo "选项："
    echo "  --dry-run       模拟运行，不实际删除文件"
    echo "  --no-confirm    不需要确认直接删除"
    echo "  --help          显示此帮助信息"
    echo "  --exclude       排除指定模式的目录或文件"
    echo "  --file          包含文件匹配模式"
    echo "  --whitelist-dir 添加白名单目录（默认包括 .git 和 .mgit）"
    echo "额外的模式会被添加到默认模式中"
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
file_patterns=()
whitelist_dirs=('.git' '.mgit' 'third-party')

# 解析参数
while [[ $# -gt 0 ]]; do
    case "$1" in
        --dry-run) dry_run=true; shift ;;
        --no-confirm) no_confirm=true; shift ;;
        --help) show_help; exit 0 ;;
        --exclude) exclude_patterns+=("$2"); shift 2 ;;
        --file) file_patterns+=("$2"); shift 2 ;;
        --whitelist-dir)
            whitelist_dirs+=("$2")
            shift 2
            ;;
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
default_dir_patterns=(
    'build' 'cmake-build-*' 'build.lite.*' 'build.mml.*' 'build.macos.*' 'build.opt' 'tmp' 'CMakeFiles'
    'node_modules' 'dist' '.cache' '.tmp' '.sass-cache' 'coverage'
    'target' 'obj' 'out' 'Debug' 'Release'
)

default_file_patterns=(
    '*.log' 'libpaddle_api_light_bundled.a'
)

# 合并模式
all_dir_patterns=("${default_dir_patterns[@]}" "${extra_patterns[@]}")
all_file_patterns=("${default_file_patterns[@]}" "${file_patterns[@]}")

# 处理目录和文件
process_items() {
    local dir_args=() file_args=() exclude_args=() whitelist_args=()
    for pattern in "${all_dir_patterns[@]}"; do
        if [[ $pattern == *"*"* ]]; then
            dir_args+=(-path "*/$pattern" -o -path "*/$pattern/*" -o)
        else
            dir_args+=(-name "$pattern" -o)
        fi
    done
    unset 'dir_args[${#dir_args[@]}-1]'

    for pattern in "${all_file_patterns[@]}"; do
        if [[ $pattern == *"*"* ]]; then
            file_args+=(-path "*/$pattern" -o)
        else
            file_args+=(-name "$pattern" -o)
        fi
    done
    unset 'file_args[${#file_args[@]}-1]'

    for pattern in "${exclude_patterns[@]}"; do
        exclude_args+=(-not -path "*/$pattern/*" -and -not -name "$pattern")
    done

    for dir in "${whitelist_dirs[@]}"; do
        whitelist_args+=(-not -path "*/$dir/*")
    done

    find "$target_dir" \( \( -type d \( "${dir_args[@]}" \) \) -o \( -type f \( \( "${dir_args[@]}" \) -o \( "${file_args[@]}" \) \) \) \) "${exclude_args[@]}" "${whitelist_args[@]}" -print0
}

# 显示项目完整信息，按父目录分组
show_grouped_items() {
    local current_parent=""

    while IFS= read -r -d '' item; do
        local parent_dir=$(dirname "$item")
        local name=$(basename "$item")
        local size=$(du -sh "$item" 2>&1)
        local type
        if [ -d "$item" ]; then
            type="目录"
        elif [ -f "$item" ]; then
            type="文件"
        elif [ -L "$item" ]; then
            type="符号链接"
        else
            type="未知类型"
        fi
        local pattern=$(get_matching_pattern "$item")

        if [[ "$parent_dir" != "$current_parent" ]]; then
            if [[ -n "$current_parent" ]]; then
                echo "---"
            fi
            echo -e "${GREEN}${parent_dir}${NC}"
            current_parent="$parent_dir"
        fi

        echo -e "  ${YELLOW}${name}${NC}"
        if [[ $size == *"No such file or directory"* ]]; then
            echo -e "    类型: ${type}, 大小: 无法获取 (可能是无效的符号链接或已被删除), 匹配模式: ${pattern}"
        else
            echo -e "    类型: ${type}, 大小: ${size}, 匹配模式: ${pattern}"
        fi
    done < <(printf '%s\0' "${items[@]}" | sort -z)
    echo "---"
}

get_matching_pattern() {
    local item=$1
    for pattern in "${all_dir_patterns[@]}"; do
        if [[ $pattern == *"*"* ]]; then
            if [[ $item == */$pattern || $item == */$pattern/* ]]; then
                echo "$pattern"
                return
            fi
        elif [[ $(basename "$item") == $pattern ]]; then
            echo "$pattern"
            return
        fi
    done
    for pattern in "${all_file_patterns[@]}"; do
        if [[ $pattern == *"*"* ]]; then
            if [[ $item == */$pattern ]]; then
                echo "$pattern"
                return
            fi
        elif [[ $(basename "$item") == $pattern ]]; then
            echo "$pattern"
            return
        fi
    done
    echo "未匹配模式"
}

# 主要处理逻辑
echo -e "${YELLOW}警告：此脚本会删除匹配特定模式的目录和文件。请确保您了解将要删除的内容。${NC}"
echo -e "${GREEN}白名单目录（不会被删除）：${NC}${whitelist_dirs[*]}"
echo -e "${GREEN}要删除的目录模式：${NC}${all_dir_patterns[*]}"
echo -e "${GREEN}要删除的文件模式：${NC}${all_file_patterns[*]}"
echo "---"

# 替换 mapfile 命令
items=()
while IFS= read -r -d '' item; do
    items+=("$item")
done < <(process_items)

if [ ${#items[@]} -eq 0 ]; then
    echo -e "${YELLOW}未找到符合条件的目录或文件。${NC}"
    exit 0
fi

echo -e "${GREEN}以下项目将被删除：${NC}"
show_grouped_items

total_size=$(du -sc "${items[@]}" | tail -n1 | cut -f1)

echo -e "\n${GREEN}总计将删除的项目数量：${NC}${#items[@]}"
echo -e "${GREEN}总体积：${NC}$(format_size $total_size)"

if [ "$dry_run" = true ]; then
    echo -e "${YELLOW}(干运行模式，未实际删除)${NC}"
    exit 0
fi

if [ "$no_confirm" = false ]; then
    read -p "是否确认删除以上项目？输入 'yes' 确认：" confirm
    if [ "$confirm" != "yes" ]; then
        echo -e "${YELLOW}操作已取消。${NC}"
        exit 0
    fi
fi

log "开始删除操作"
for item in "${items[@]}"; do
    echo -e "${GREEN}正在删除项目：${NC}$item"
    if trash "$item"; then
        log "成功删除项目：$item"
    else
        log "删除失败：$item"
    fi
done

log "删除操作完成"
echo -e "${GREEN}删除完成。日志已保存到 $LOG_FILE${NC}"