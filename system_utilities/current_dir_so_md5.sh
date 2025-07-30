#!/bin/bash

# 初始化变量
SORT=false
COUNT=false
DIRECTORY="."

# 函数：显示使用说明
show_usage() {
    echo "用法: $0 [-s] [-c] [-d 目录]"
    echo "  -s: 对输出进行排序"
    echo "  -c: 显示文件计数"
    echo "  -d: 指定要处理的目录（默认为当前目录）"
    echo "  -h: 显示此帮助信息"
}

# 解析命令行参数
while getopts "scd:h" opt; do
    case $opt in
        s) SORT=true ;;
        c) COUNT=true ;;
        d) DIRECTORY="$OPTARG" ;;
        h) show_usage; exit 0 ;;
        \?) echo "无效选项: -$OPTARG" >&2; show_usage; exit 1 ;;
    esac
done

# 显示当前工作目录
echo "处理目录: $DIRECTORY"

# 计算并显示所有文件的MD5值
echo -e "\n计算所有文件的MD5值:"
result=$(find "$DIRECTORY" -type f -print0 | while IFS= read -r -d '' file; do
    md5_value=$(md5sum "$file" | awk '{print $1}')
    echo "$md5_value  $file"
done)

# 根据选项决定是否排序
if $SORT; then
    echo "$result" | sort
else
    echo "$result"
fi

# 根据选项决定是否显示文件计数
if $COUNT; then
    file_count=$(echo "$result" | wc -l)
    echo -e "\n总文件数: $file_count"
fi
