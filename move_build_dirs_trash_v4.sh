#!/usr/bin/env bash
set -e  # 当命令出错时退出脚本

# 版本信息
VERSION="4.0.0"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 日志级别定义
LOG_LEVEL_DEBUG=3
LOG_LEVEL_INFO=2
LOG_LEVEL_WARN=1
LOG_LEVEL_ERROR=0

# 默认日志级别
current_log_level=$LOG_LEVEL_INFO

# 日志文件
LOG_FILE="/Users/$(whoami)/Downloads/clean_$(date +%Y%m%d_%H%M%S).log"

# 终端宽度
TERM_WIDTH=$(tput cols 2>/dev/null || echo 80)

# 显示进度条
show_progress_bar() {
    local percent=$1
    local width=$((TERM_WIDTH - 20))
    local completed=$((width * percent / 100))
    local remaining=$((width - completed))
    
    # 保存光标位置
    printf "\033[s"
    
    # 清除当前行
    printf "\033[K"
    
    # 打印进度条
    printf "[%s%s] %3d%%" "$(printf "%${completed}s" | tr ' ' '#')" "$(printf "%${remaining}s" | tr ' ' '-')" "$percent"
    
    # 恢复光标位置
    printf "\033[u"
}

# 日志函数
log_to_file() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $*" >> "$LOG_FILE"
}

log_debug() {
    log_to_file "[DEBUG] $*"
    if [ $current_log_level -ge $LOG_LEVEL_DEBUG ]; then
        printf "${CYAN}[DEBUG] %s${NC}\n" "$*"
    fi
}

log_info() {
    log_to_file "[INFO] $*"
    if [ $current_log_level -ge $LOG_LEVEL_INFO ]; then
        printf "${GREEN}[INFO] %s${NC}\n" "$*"
    fi
}

log_warn() {
    log_to_file "[WARN] $*"
    if [ $current_log_level -ge $LOG_LEVEL_WARN ]; then
        printf "${YELLOW}[WARN] %s${NC}\n" "$*"
    fi
}

log_error() {
    log_to_file "[ERROR] $*"
    if [ $current_log_level -ge $LOG_LEVEL_ERROR ]; then
        printf "${RED}[ERROR] %s${NC}\n" "$*"
    fi
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
    printf "${BLUE}目录和文件清理工具 v${VERSION}${NC}\n"
    echo "用法：$0 目标目录 [选项] [额外的模式...]"
    echo "选项："
    echo "  --dry-run       模拟运行，不实际删除文件"
    echo "  --no-confirm    不需要确认直接删除"
    echo "  --help          显示此帮助信息"
    echo "  --exclude       排除指定模式的目录或文件"
    echo "  --file          包含文件匹配模式"
    echo "  --whitelist-dir 添加白名单目录（默认包括 .git、.mgit 和 third-party）"
    echo "  --quiet         静默模式，只显示错误和最终结果"
    echo "  --verbose       详细模式，显示更多信息"
    echo "  --debug         调试模式，显示所有信息"
    echo "额外的模式会被添加到默认模式中"
}

# 检查 trash 命令
if ! command -v trash &> /dev/null; then
    log_error "错误：未找到 'trash' 命令，请先安装。"
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
        --quiet) 
            current_log_level=$LOG_LEVEL_ERROR
            shift
            ;;
        --verbose) 
            current_log_level=$LOG_LEVEL_INFO
            shift
            ;;
        --debug) 
            current_log_level=$LOG_LEVEL_DEBUG
            shift
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
    log_error "错误：未提供目标目录"
    show_help
    exit 1
fi

if [ ! -d "$target_dir" ]; then
    log_error "错误：目标目录 $target_dir 不存在"
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

# 显示项目汇总信息
show_summary_items() {
    local dir_count=0
    local file_count=0
    local total_size=0
    
    # 按目录分组统计
    local dirs_info=()
    local current_parent=""
    local parent_size=0
    local parent_count=0
    
    # 创建临时文件
    local temp_file=$(mktemp)
    printf '%s\0' "${items[@]}" | sort -z > "$temp_file"
    
    log_debug "开始处理项目汇总..."
    
    # 使用临时文件而不是管道
    while IFS= read -r -d '' item; do
        log_to_file "处理项目: $item"
        local parent_dir=$(dirname "$item")
        
        if [ -d "$item" ]; then
            dir_count=$((dir_count + 1))
            # 计算目录大小
            local size=$(du -sk "$item" 2>/dev/null | cut -f1)
            if [ -z "$size" ]; then size=0; fi
            total_size=$((total_size + size))
            
            if [[ "$parent_dir" != "$current_parent" ]]; then
                if [[ -n "$current_parent" ]]; then
                    dirs_info+=("$current_parent:$parent_count:$parent_size")
                fi
                current_parent="$parent_dir"
                parent_count=1
                parent_size=$size
            else
                parent_count=$((parent_count + 1))
                parent_size=$((parent_size + size))
            fi
            log_debug "目录: $item, 大小: $(format_size $size)"
        elif [ -f "$item" ]; then
            file_count=$((file_count + 1))
            local size=$(du -sk "$item" 2>/dev/null | cut -f1)
            if [ -z "$size" ]; then size=0; fi
            total_size=$((total_size + size))
            
            if [[ "$parent_dir" != "$current_parent" ]]; then
                if [[ -n "$current_parent" ]]; then
                    dirs_info+=("$current_parent:$parent_count:$parent_size")
                fi
                current_parent="$parent_dir"
                parent_count=1
                parent_size=$size
            else
                parent_count=$((parent_count + 1))
                parent_size=$((parent_size + size))
            fi
            log_debug "文件: $item, 大小: $(format_size $size)"
        fi
    done < "$temp_file"
    
    # 添加最后一个目录
    if [[ -n "$current_parent" ]]; then
        dirs_info+=("$current_parent:$parent_count:$parent_size")
    fi
    
    # 删除临时文件
    rm "$temp_file"
    
    # 显示汇总信息
    log_info "找到 ${#dirs_info[@]} 个匹配的父目录"
    log_info "总计 $dir_count 个目录, $file_count 个文件"
    log_info "总体积: $(format_size $total_size)"
    
    # 显示按目录分组的详细信息
    if [ $current_log_level -ge $LOG_LEVEL_INFO ]; then
        echo "---"
        echo "按目录分组的详细信息:"
        for dir_info in "${dirs_info[@]}"; do
            IFS=':' read -r dir count size <<< "$dir_info"
            printf "${GREEN}%s${NC}\n" "$dir"
            printf "  包含 %d 个项目, 大小: %s\n" "$count" "$(format_size $size)"
        done
        echo "---"
    fi
    
    # 返回总大小
    echo $total_size
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
log_info "======================================="
log_info "目录和文件清理工具 v${VERSION}"
log_info "======================================="

# 主要处理逻辑
log_warn "警告：此脚本会删除匹配特定模式的目录和文件。请确保您了解将要删除的内容。"
log_info "白名单目录（不会被删除）：${whitelist_dirs[*]}"
log_info "要删除的目录模式：${all_dir_patterns[*]}"
log_info "要删除的文件模式：${all_file_patterns[*]}"

log_info "正在查找匹配的项目..."
# 使用临时文件替代进程替换
temp_items_file=$(mktemp)
process_items > "$temp_items_file"
items=()
while IFS= read -r -d '' item; do
    items+=("$item")
done < "$temp_items_file"
rm "$temp_items_file"

if [ ${#items[@]} -eq 0 ]; then
    log_warn "未找到符合条件的目录或文件。"
    exit 0
fi

# 按路径长度排序（从长到短）确保子目录/文件在父目录之前
log_debug "正在对 ${#items[@]} 个项目进行排序..."
IFS=$'\n' sorted_items=($(printf "%s\n" "${items[@]}" | sort -r))
unset IFS

log_info "以下是匹配项目的汇总信息:"
total_size=$(show_summary_items)

# 明确状态
log_debug "干运行模式: $dry_run"
log_debug "无需确认模式: $no_confirm"

if [ "$dry_run" = true ]; then
    log_warn "(干运行模式，未实际删除)"
    exit 0
fi

if [ "$no_confirm" = false ]; then
    printf "${YELLOW}是否确认删除以上项目？输入 'yes' 确认：${NC}"
    read -r confirm
    log_to_file "用户输入: '$confirm'"
    
    if [ "$confirm" != "yes" ]; then
        log_warn "操作已取消。"
        exit 0
    fi
fi

log_info "开始删除操作..."

# 跟踪已删除的目录
deleted_dirs=()
skipped_items=0
failed_items=0
success_items=0

# 进度显示
total_items=${#sorted_items[@]}
progress=0

# 使用动态进度条
printf "\n"  # 为进度条预留一行
show_progress_bar 0

batch_size=10  # 批处理大小，每处理这么多个项目才更新一次屏幕
batch_count=0
batch_logs=""

for item in "${sorted_items[@]}"; do
    # 检查项目是否在已删除的父目录中
    if should_skip "$item"; then
        log_to_file "跳过项目(父目录已删除)：$item"
        skipped_items=$((skipped_items + 1))
        batch_count=$((batch_count + 1))
        continue
    fi
    
    # 检查项目是否仍然存在
    if [ ! -e "$item" ]; then
        log_to_file "跳过项目(不存在)：$item"
        skipped_items=$((skipped_items + 1))
        batch_count=$((batch_count + 1))
        continue
    fi
    
    log_debug "正在删除项目：$item"
    log_to_file "正在删除项目：$item"
    
    if trash "$item" 2>/dev/null; then
        log_to_file "成功删除项目：$item"
        success_items=$((success_items + 1))
        # 如果是目录，添加到已删除路径列表
        if [ -d "$item" ]; then
            deleted_dirs+=("$item/")
        fi
    else
        log_to_file "删除失败：$item"
        log_error "删除失败：$item"
        failed_items=$((failed_items + 1))
    fi
    
    # 更新进度
    progress=$((progress + 1))
    batch_count=$((batch_count + 1))
    
    # 每批次更新一次进度条
    if [ $batch_count -ge $batch_size ] || [ $progress -eq $total_items ]; then
        percent=$((progress * 100 / total_items))
        show_progress_bar $percent
        batch_count=0
    fi
done

# 完成进度条
show_progress_bar 100
printf "\n\n"  # 在进度条后添加换行

log_info "删除操作完成！"
log_info "成功删除：${success_items} 个项目"
log_info "跳过项目：${skipped_items} 个项目"
if [ $failed_items -gt 0 ]; then
    log_error "删除失败：${failed_items} 个项目"
fi
log_info "日志已保存到 $LOG_FILE"