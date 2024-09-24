# 获取目标目录
target_dir=$1

# 初始化总体积
total_size=0

# 查找并移动所有的以build开头的目录和以cmake-build-开头的目录
find "$target_dir" -type d \( -name 'build' -o -name 'cmake-build-*' \) -print0 | (
    while IFS= read -r -d '' dir; do
        # 检查目录是否存在
        if [ -d "$dir" ]; then
            # 获取目录大小
            size=$(du -sk "$dir" | awk '{print $1}')
            
            # 输出目录和其大小
            echo "$dir: $size KB"
            
            # 累加到总体积
            total_size=$(($total_size + $size))
            
            # 移动到垃圾箱
            trash "$dir" 
        else
            echo "目录 $dir 不存在"
        fi
    done
    echo $total_size
) | read total_size

# 输出总体积
echo "总体积: $total_size KB"