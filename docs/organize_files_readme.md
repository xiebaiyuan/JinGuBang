
```bash
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
```

**脚本说明：**

- **新增部分：**
  - **接受目录参数：** 脚本现在可以接受一个目录作为参数。如果没有提供参数，脚本会提示用法并退出。
    ```bash
    if [ $# -eq 0 ]; then
      echo "用法: $0 [目录]"
      exit 1
    fi
    ```
  - **检查目录是否存在：** 如果提供的目录不存在，脚本会给出错误提示并退出。
    ```bash
    if [ ! -d "$TARGET_DIR" ]; then
      echo "错误: 目录 $TARGET_DIR 不存在"
      exit 1
    fi
    ```
  - **切换到目标目录：** 使用 `cd` 命令进入指定的目标目录。
    ```bash
    cd "$TARGET_DIR"
    ```

- **其余部分与之前的脚本相同：**
  - 遍历指定目录下的所有文件，按照文件后缀名分类并移动到对应的文件夹中。

**使用方法：**

1. **保存脚本：** 将上述脚本保存为 `organize_files.sh`。

2. **赋予执行权限：**

   ```bash
   chmod +x organize_files.sh
   ```

3. **运行脚本：**

   - 整理当前目录：

     ```bash
     ./organize_files.sh ./
     ```

   - 整理其他目录（例如 `/path/to/your/directory`）：

     ```bash
     ./organize_files.sh /path/to/your/directory
     ```

**注意事项：**

- **只处理指定目录：** 该脚本只会整理指定的目录，不会递归处理子目录。

- **文件过滤：** 只处理包含`.`的文件，即有后缀名的常规文件。隐藏文件和没有后缀名的文件将被忽略。

- **备份建议：** 在运行脚本前，建议备份重要文件，防止意外的数据丢失。

- **错误处理：** 如果提供的目录不存在，脚本会提示错误；如果没有提供目录参数，脚本会显示用法信息。

**示例：**

假设你的目录结构如下：

```
your_directory/
├── file1.txt
├── file2.pdf
├── image.jpg
└── document.docx
```

运行脚本：

```bash
./organize_files.sh your_directory/
```

运行后，目录结构将变为：

```
your_directory/
├── docx/
│   └── document.docx
├── jpg/
│   └── image.jpg
├── pdf/
│   └── file2.pdf
└── txt/
    └── file1.txt
