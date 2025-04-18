# move_build_dirs_trash.py 使用示例

Python3 版本的 move_build_dirs_trash.py 脚本提供了更友好的界面和更高效的处理能力。以下是一些常见使用场景的示例：

## 基本用法

```bash
# 基本使用方式 - 清理当前目录下的构建文件
python3 /Users/xiebaiyuan/tools/move_build_dirs_trash.py .

# 清理特定目录下的构建文件
python3 /Users/xiebaiyuan/tools/move_build_dirs_trash.py /path/to/your/project
```

## 模拟运行模式 (不实际删除)

```bash
# 干运行模式 - 只显示会删除什么，但不真正删除
python3 /Users/xiebaiyuan/tools/move_build_dirs_trash.py . --dry-run
```

## 无需确认模式 (自动确认)

```bash
# 无需确认直接删除
python3 /Users/xiebaiyuan/tools/move_build_dirs_trash.py . --no-confirm
```

## 指定额外匹配模式

```bash
# 添加额外的构建目录模式
python3 /Users/xiebaiyuan/tools/move_build_dirs_trash.py . build-android build-ios

# 添加特定文件匹配模式
python3 /Users/xiebaiyuan/tools/move_build_dirs_trash.py . --file "*.a" --file "*.o"
```

## 排除某些目录或文件

```bash
# 排除特定目录或文件
python3 /Users/xiebaiyuan/tools/move_build_dirs_trash.py . --exclude "important_build"

# 多个排除项
python3 /Users/xiebaiyuan/tools/move_build_dirs_trash.py . --exclude "important_build" --exclude "special_file.log"
```

## 添加白名单目录 (不会检查这些目录内部)

```bash
# 添加白名单目录
python3 /Users/xiebaiyuan/tools/move_build_dirs_trash.py . --whitelist-dir "my_libs"

# 添加多个白名单目录
python3 /Users/xiebaiyuan/tools/move_build_dirs_trash.py . --whitelist-dir "my_libs" --whitelist-dir "external"
```

## 组合使用

```bash
# 复杂场景组合使用
python3 /Users/xiebaiyuan/tools/move_build_dirs_trash.py /Users/xiebaiyuan/projects \
  --dry-run \
  --exclude "special_build" \
  --file "*.temp" \
  --whitelist-dir "important_module" \
  cmake_output custom_build
```

## 创建别名方便使用

在您的 `.bashrc` 或 `.zshrc` 中添加：

```bash
alias clean-builds='python3 /Users/xiebaiyuan/tools/move_build_dirs_trash.py'
```

然后可以简化使用：

```bash
# 简化命令
clean-builds .

# 干运行模式
clean-builds . --dry-run
```

## 常见场景示例

### 清理 Android 项目

```bash
# 清理 Android 项目，保留 gradle 缓存目录
python3 /Users/xiebaiyuan/tools/move_build_dirs_trash.py /Users/xiebaiyuan/AndroidStudioProjects \
  --whitelist-dir ".gradle" \
  --whitelist-dir "gradle"
```

### 清理机器学习项目

```bash
# 清理 ML 项目，同时删除模型缓存和中间文件
python3 /Users/xiebaiyuan/tools/move_build_dirs_trash.py /Users/xiebaiyuan/ml_projects \
  --file "*.h5" --file "*.ckpt" --file "*.pth" \
  model_cache checkpoints
```

### 清理 C++ 项目

```bash
# 清理 C++ 项目，同时删除编译产物
python3 /Users/xiebaiyuan/tools/move_build_dirs_trash.py /Users/xiebaiyuan/cpp_projects \
  --file "*.o" --file "*.so" --file "*.a" \
  --exclude "third_party/build"
```

## 提示

1. 强烈建议首次使用时先加上 `--dry-run` 参数，确保脚本匹配的文件符合预期
2. 脚本会自动记录详细操作到日志文件，日志文件路径会在脚本执行结束时显示
3. 所有删除操作都是通过 `trash` 命令执行的，文件会移到回收站而不是直接删除，可以在需要时恢复

这个 Python3 实现的脚本提供了更友好的进度展示和更全面的统计信息，特别适合处理大型项目中的文件清理工作。