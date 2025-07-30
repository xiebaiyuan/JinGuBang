#!/bin/bash

# 切换到您的Git仓库目录
pwd

# 查询变化的.so文件并计算MD5
git status --porcelain | awk '{print $2}' | grep '\.so$' | while read -r file; do
    if [ -f "$file" ]; then
        MD5 "$file"
    fi
done
