#!/bin/sh

# 打印目录大小并带序号
echo "目录大小列表 (从大到小)："
du -sh -- * 2>/dev/null | sort -hr | nl -w2 -s". "

# 读取用户输入的N
echo ""
echo -n "请输入要输出的前N个目录名 (例如 3): "
read N

# 输出前N个目录名，用逗号拼接
LIST=$(du -sh -- * 2>/dev/null | sort -hr | head -n "$N" | awk '{print $2}' | paste -sd "," -)

echo "前 $N 个目录列表："
echo "$LIST"