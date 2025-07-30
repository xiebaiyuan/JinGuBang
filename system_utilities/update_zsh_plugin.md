# Oh My Zsh 插件更新脚本

## 简介

这是一个用于自动更新 Oh My Zsh 自定义插件的 Zsh 脚本。它会遍历您的自定义插件目录，检查每个插件是否是 Git 仓库，如果是，则会尝试更新该插件。

## 功能

- 自动检测并更新 Oh My Zsh 自定义插件目录中的所有 Git 仓库
- 提供详细的更新过程输出
- 使用安全的快进合并策略
- 在遇到错误时立即停止执行

## 使用方法

1. 将 `update_zsh_plugin.sh` 脚本保存到您的计算机上。
2. 给予脚本执行权限：
   ```
   chmod +x update_zsh_plugin.sh
   ```
3. 运行脚本：
   ```
   ./update_zsh_plugin.sh
   ```

## 注意事项

- 此脚本默认使用 `$ZSH_CUSTOM` 环境变量来定位自定义插件目录。如果未设置，它将默认为 `$HOME/.oh-my-zsh/custom/plugins`。
- 脚本使用 `--ff-only` 选项进行 Git 拉取，这意味着它只会执行快进合并。如果远程分支有任何冲突的更改，更新将失败。
- 建议在运行此脚本之前，确保您的本地更改已提交或存储。

## 自定义

如果您的 Oh My Zsh 自定义插件目录位于不同的位置，您可以修改脚本中的 `PLUGIN_DIR` 变量：

PLUGIN_DIR="/path/to/your/custom/plugins"


## 贡献

欢迎提出问题、建议或提交拉取请求来改进这个脚本。