#!/usr/bin/env bash
# filepath: /Users/xiebaiyuan/tools/move_build_dirs_trash_v3.sh
set -e  # 当命令出错时退出脚本

# 版本信息
VERSION="3.0.0"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color
print_color() {
    local color="$1"
    local message="$2"
    printf "%b%s%b\n" "$color" "$message" "$NC"
}
# 日志文件
LOG_FILE="/Users/$(whoami)/Downloads/clean_$(date +%Y%m%d_%H%M%S).log"

# 函数定义
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
    print_color "${GREEN}$1${NC}"
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
    print_color "${BLUE}目录和文件清理工具 v${VERSION}${NC}"
    echo "用法：$0 目标目录 [选项] [额外的模式...]"
    echo "选项："
    echo "  --dry-run       模拟运行，不实际删除文件"
    echo "  --no-confirm    不需要确认直接删除"
    echo "  --help          显示此帮助信息"
    echo "  --exclude       排除指定模式的目录或文件"
    echo "  --file          包含文件匹配模式"
    echo "  --whitelist-dir 添加白名单目录（默认包括 .git、.mgit 和 third-party）"
    echo "额外的模式会被添加到默认模式中"
}

# 检查 trash 命令
if ! command -v trash &> /dev/null; then
    print_color "${RED}错误：未找到 'trash' 命令，请先安装。${NC}"
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
    print_color "${RED}错误：未提供目标目录${NC}" >&2
    show_help
    exit 1
fi

if [ ! -d "$target_dir" ]; then
    print_color "${RED}错误：目标目录 $target_dir 不存在${NC}"
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

# 替换有问题的函数
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

# 显示项目完整信息，按父目录分组
# 显示项目完整信息，按父目录分组
show_grouped_items() {
    local current_parent=""
    local count=0
    
    # 创建临时文件
    local temp_file=$(mktemp)
    printf '%s\0' "${items[@]}" | sort -z > "$temp_file"
    
    # 使用临时文件而不是管道
    while IFS= read -r -d '' item; do
        local parent_dir=$(dirname "$item")
        local name=$(basename "$item")
        local type
        
        if [ -d "$item" ]; then
            type="目录"
            # 跳过不存在的目录（可能在先前的列表生成后被删除）
            if [ ! -d "$item" ]; then
                continue
            fi
            local size=$(du -sk "$item" 2>/dev/null | cut -f1)
            if [ -z "$size" ]; then size=0; fi
        elif [ -f "$item" ]; then
            type="文件"
            # 跳过不存在的文件
            if [ ! -f "$item" ]; then
                continue
            fi
            local size=$(du -sk "$item" 2>/dev/null | cut -f1)
            if [ -z "$size" ]; then size=0; fi
        elif [ -L "$item" ]; then
            type="符号链接"
            local size=0
        else
            type="未知类型"
            local size=0
        fi
        local pattern=$(get_matching_pattern "$item")

        if [[ "$parent_dir" != "$current_parent" ]]; then
            if [[ -n "$current_parent" ]]; then
                echo "---"
            fi
            print_color "${GREEN}${parent_dir}${NC}"
            current_parent="$parent_dir"
        fi

        print_color "  ${YELLOW}${name}${NC}"
        if [ "$type" == "目录" ]; then
            print_color "    类型: ${type}, 大小: $(format_size $size), 匹配模式: ${pattern}"
        elif [ "$type" == "符号链接" ]; then
            local target=$(readlink "$item")
            print_color "    类型: ${type}, 指向: ${target}, 匹配模式: ${pattern}"
        else
            print_color "    类型: ${type}, 大小: $(format_size $size), 匹配模式: ${pattern}"
        fi
        
        ((count++))
        # 每100项显示一次进度
        if [ $((count % 100)) -eq 0 ]; then
            print_color "${BLUE}已分析 $count 个项目...${NC}"
        fi
    done < "$temp_file"
    
    # 删除临时文件
    rm "$temp_file"
    echo "---"
}
# 检查路径是否应该被跳过（是否在已删除的父目录中）
should_skip() {
    local item="$1"
    for path in "${deleted_dirs[@]}"; do
        if [[ "$item" == "$path"* ]]; then
            return 0  # 返回0表示应该跳过
        fi
    done
    return 1  # 返回1表示不应该跳过
}

# 显示标题和版本信息
print_color "${BLUE}======================================${NC}"
print_color "${BLUE}目录和文件清理工具 v${VERSION}${NC}"
print_color "${BLUE}======================================${NC}"

# 主要处理逻辑
print_color "${YELLOW}警告：此脚本会删除匹配特定模式的目录和文件。请确保您了解将要删除的内容。${NC}"
print_color "${GREEN}白名单目录（不会被删除）：${NC}${whitelist_dirs[*]}"
print_color "${GREEN}要删除的目录模式：${NC}${all_dir_patterns[*]}"
print_color "${GREEN}要删除的文件模式：${NC}${all_file_patterns[*]}"
echo "---"


print_color "${BLUE}正在查找匹配的项目...${NC}"
# 使用临时文件替代进程替换
temp_items_file=$(mktemp)
process_items > "$temp_items_file"
items=()
while IFS= read -r -d '' item; do
    items+=("$item")
done < "$temp_items_file"
rm "$temp_items_file"

if [ ${#items[@]} -eq 0 ]; then
    print_color "${YELLOW}未找到符合条件的目录或文件。${NC}"
    exit 0
fi

# 按路径长度排序（从长到短）确保子目录/文件在父目录之前
# 避免先删除父目录，后面的子目录操作出错
print_color "${BLUE}正在对项目进行排序...${NC}"
IFS=$'\n' sorted_items=($(printf "%s\n" "${items[@]}" | sort -r))
unset IFS

print_color "${GREEN}以下项目将被删除：${NC}"
show_grouped_items

# 计算总大小（忽略已经不存在的项目）
print_color "${BLUE}正在计算总大小...${NC}"
total_size=0
valid_items=0
for item in "${sorted_items[@]}"; do
    if [ -e "$item" ]; then
        size=$(du -sk "$item" 2>/dev/null | cut -f1)
        if [ -n "$size" ]; then
            total_size=$((total_size + size))
            valid_items=$((valid_items + 1))
        fi
    fi
done

print_color "\n${GREEN}总计将删除的项目数量：${NC}${valid_items}"
print_color "${GREEN}总体积：${NC}$(format_size $total_size)"


# 添加调试信息
print_color "${BLUE}干运行模式: $dry_run${NC}"
print_color "${BLUE}无需确认模式: $no_confirm${NC}"


if [ "$dry_run" = true ]; then
    print_color "${YELLOW}(干运行模式，未实际删除)${NC}"
    exit 0
fi

# 修改确认逻辑，确保正确提示
if [ "$no_confirm" = false ]; then
    print_color "${YELLOW}是否确认删除以上项目？输入 'yes' 确认：${NC}"
    read -p "" confirm
    echo "用户输入: '$confirm'"
    if [ "$confirm" != "yes" ]; then
        print_color "${YELLOW}操作已取消。${NC}"
        exit 0
    fi
fi

log "开始删除操作"
print_color "${BLUE}开始执行删除操作...${NC}"

# 跟踪已删除的目录
deleted_dirs=()
skipped_items=0
failed_items=0
success_items=0

# 进度显示
total_items=${#sorted_items[@]}
progress=0
progress_step=$((total_items / 10))
if [ $progress_step -lt 1 ]; then progress_step=1; fi

for item in "${sorted_items[@]}"; do
    # 检查项目是否在已删除的父目录中
    if should_skip "$item"; then
        log "跳过项目(父目录已删除)：$item"
        skipped_items=$((skipped_items + 1))
        continue
    fi
    
    # 检查项目是否仍然存在
    if [ ! -e "$item" ]; then
        log "跳过项目(不存在)：$item"
        skipped_items=$((skipped_items + 1))
        continue
    fi
    
    print_color "${GREEN}正在删除项目：${NC}$item"
    if trash "$item" 2>/dev/null; then
        log "成功删除项目：$item"
        success_items=$((success_items + 1))
        # 如果是目录，添加到已删除路径列表
        if [ -d "$item" ]; then
            deleted_dirs+=("$item/")
        fi
    else
        log "删除失败：$item"
        failed_items=$((failed_items + 1))
    fi
    
    # 更新和显示进度
    progress=$((progress + 1))
    if [ $((progress % progress_step)) -eq 0 ]; then
        percent=$((progress * 100 / total_items))
        print_color "${BLUE}进度：${percent}% (${progress}/${total_items})${NC}"
    fi
done

log "删除操作完成"
print_color "${GREEN}删除操作完成！${NC}"
print_color "${GREEN}成功删除：${NC}${success_items} 个项目"
print_color "${YELLOW}跳过项目：${NC}${skipped_items} 个项目"
if [ $failed_items -gt 0 ]; then
    print_color "${RED}删除失败：${NC}${failed_items} 个项目"
fi
print_color "${GREEN}日志已保存到 ${NC}$LOG_FILE"