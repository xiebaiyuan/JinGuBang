#!/bin/zsh

# 设置错误时退出
set -e

# 定义插件目录
PLUGIN_DIR="${ZSH_CUSTOM:-$HOME/.oh-my-zsh/custom}/plugins"

# 更新函数
update_plugin() {
  local plugin_name=$(basename "$1")
  echo "正在更新 $plugin_name..."
  if git -C "$1" pull --ff-only; then
    echo "$plugin_name 更新成功"
  else
    echo "$plugin_name 更新失败"
  fi
}

# 主循环
for plugin in "$PLUGIN_DIR"/*; do
  if [ -d "$plugin/.git" ]; then
    update_plugin "$plugin"
  fi
done

echo "所有插件更新完成"
