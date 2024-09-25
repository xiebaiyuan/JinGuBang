#!/bin/bash

# 检查是否提供了目录参数
if [ $# -eq 0 ]; then
  echo "用法: $0 [目录]"
  exit 1
fi

# 获取目标目录
TARGET_DIR="$1"

# 检查目标目录是否存在
if [ ! -d "$TARGET_DIR" ]; then
  echo "错误: 目录 $TARGET_DIR 不存在"
  exit 1
fi

# 进入目标目录
cd "$TARGET_DIR"

# 遍历目录下的所有文件
for file in *.*; do
  # 检查是否为常规文件
  if [ -f "$file" ]; then
    # 提取文件的后缀名
    ext="${file##*.}"
    # 如果不存在对应的文件夹，则创建一个
    if [ ! -d "$ext" ]; then
      mkdir "$ext"
    fi
    # 将文件移动到对应的文件夹
    mv "$file" "$ext/"
  fi
done