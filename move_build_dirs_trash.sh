#!/bin/bash
set -e  # 当命令出错时退出脚本
# set -x  # 取消注释以启用调试模式
RED='\033[0;31m'
NC='\033[0m' # No Color
LOG_FILE="./$(date +%Y%m%d_%H%M%S).log"
# 记录日志
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
}
# 格式化文件大小
format_size() {
    local size=$1
    if [ $size -ge 1048576 ]; then
        printf "${RED}%.2f GB${NC}" $(echo "scale=2; $size/1048576" | bc)
    elif [ $size -ge 1024 ]; then
        printf "%.2f MB" $(echo "scale=2; $size/1024" | bc)
    else
        echo "$size KB"
    fi
}

# 检查是否安装了 trash 命令
if ! command -v trash &> /dev/null; then
    echo "错误：未找到 'trash' 命令，请先安装。"
    exit 1
fi

# 检查参数
if [ $# -lt 1 ]; then
    echo "用法：$0 目标目录 [--dry-run] [额外的目录模式...]"
    exit 1
fi

# 获取目标目录
target_dir=$1
shift  # 移动到下一个参数

dry_run=false
extra_patterns=()

# 处理剩余的参数
while [[ $# -gt 0 ]]; do
    case "$1" in
        --dry-run)
            dry_run=true
            shift
            ;;
        *)
            extra_patterns+=("$1")
            shift
            ;;
    esac
done

# 检查目标目录是否存在
if [ ! -d "$target_dir" ]; then
    echo "错误：目标目录 $target_dir 不存在"
    exit 1
fi

# 初始化总体积和目录列表
total_size=0
dir_list=()
dir_contents=()
dir_sizes=()

# 定义要匹配的目录模式
# 默认模式
default_patterns=('build' 'cmake-build-*' 'build.lite.*' 'build.macos.*' 'tmp' 'CMakeFiles' )

# 合并默认模式和额外模式
all_patterns=("${default_patterns[@]}" "${extra_patterns[@]}")

process_dirs() {
    # 构建 find 命令的 -name 参数
    name_args=()
    for pattern in "${all_patterns[@]}"; do
        name_args+=(-name "$pattern" -o)
    done
    # 移除最后一个 -o
    unset 'name_args[${#name_args[@]}-1]'

    while IFS= read -r -d '' dir; do
        # 获取目录大小
        size=$(du -sk "$dir" | awk '{print $1}')
        dir_sizes+=("$size")

        # 将目录添加到列表
        dir_list+=("$dir")

        # 获取目录内容并添加到列表
        content=$(ls -A "$dir")
        if [ -z "$content" ]; then
            content="(空目录)"
        fi
        dir_contents+=("$content")

        # 累加到总体积
        total_size=$((total_size + size))
    done < <(find "$target_dir" -type d \( "${name_args[@]}" \) -print0)
}

# 处理目录
process_dirs

# 如果没有找到任何目录，提示并退出
if [ ${#dir_list[@]} -eq 0 ]; then
    echo "未找到符合条件的目录。"
    exit 0
fi

# 显示将要删除的目录、其内容和大小
echo "以下目录将被删除："
for i in "${!dir_list[@]}"; do
    dir="${dir_list[$i]}"
    content="${dir_contents[$i]}"
    size="${dir_sizes[$i]}"
    formatted_size=$(format_size $size)
    echo "目录：$dir"
    echo -e "大小：$formatted_size"
    echo "内容："
    echo "$content" | awk '{print "  "$0}'
    echo "-------------------------------"
done

formatted_total_size=$(format_size $total_size)
echo "总计将删除的目录数量：${#dir_list[@]}"
echo -e "已处理目录的总体积：$formatted_total_size"
echo "-------------------------------"

# 显示实际将要执行的命令
echo "实际将要执行的命令："
for dir in "${dir_list[@]}"; do
    echo "trash \"$dir\""
done
echo "-------------------------------"

# 如果是干运行模式，直接退出
if [ "$dry_run" = true ]; then
    echo "(干运行模式，未实际删除)"
    exit 0
fi

# 提示用户确认删除
read -p "是否确认删除以上目录？输入 'yes' 确认：" confirm
if [ "$confirm" != "yes" ]; then
    echo "操作已取消。"
    exit 0
fi

# 开始记录日志
log "开始删除操作"
log "总计删除目录数量：${#dir_list[@]}"
log "总体积：$(format_size $total_size)"

# 记录将要删除的目录、其内容和大小
for i in "${!dir_list[@]}"; do
    dir="${dir_list[$i]}"
    content="${dir_contents[$i]}"
    size="${dir_sizes[$i]}"
    formatted_size=$(format_size $size)
    
    log "准备删除目录：$dir"
    log "大小：$formatted_size"
    log "内容："
    echo "$content" | while IFS= read -r line; do
        log "  $line"
    done
    log "-------------------------------"
done

# 执行删除操作
for dir in "${dir_list[@]}"; do
    echo "正在删除目录：$dir"
    if trash "$dir"; then
        log "成功删除目录：$dir ($(format_size ${dir_sizes[${dir_list[@]%%$dir*}]}))"
    else
        log "删除失败：$dir"
    fi
done

log "删除操作完成"

echo "删除完成。日志已保存到 $LOG_FILE"