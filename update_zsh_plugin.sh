for plugin in ${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/plugins/*; do
  if [ -d "$plugin/.git" ]; then
    echo "正在更新 $(basename $plugin)..."
    git -C "$plugin" pull
  fi
done
