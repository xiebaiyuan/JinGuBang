#!/bin/bash

# 查找当前目录及所有子目录下名为 build 的目录，并逐一删除
find . -type d -name 'build' -exec rm -rf {} +

echo "所有名为 'build' 的目录已被删除。"
