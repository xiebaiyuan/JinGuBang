# dev_tools

开发辅助工具，面向日常编码场景。

## 工具列表

### todo_collector.py

从代码库中收集 TODO/FIXME/HACK/XXX/BUG/OPTIMIZE 注释。

```bash
# 扫描当前目录，按文件分组
python3 dev_tools/todo_collector.py .

# 按 tag 分组
python3 dev_tools/todo_collector.py . -g tag

# 自定义 tag
python3 dev_tools/todo_collector.py . -t "TODO,NOTE,PERF"

# 输出 CSV
python3 dev_tools/todo_collector.py . --csv > todos.csv
```

自动跳过 `.git`、`node_modules`、`__pycache__`、`venv` 等目录和二进制文件。

### loc_counter.py

按语言统计代码行数，区分代码行、注释行、空行。

```bash
# 统计当前目录
python3 dev_tools/loc_counter.py .

# 只看前 5 名语言
python3 dev_tools/loc_counter.py . --top 5

# 按文件数排序
python3 dev_tools/loc_counter.py . --sort files
```

支持 30+ 语言：Python, JS/TS, Java, Kotlin, Swift, Go, Rust, C/C++, Ruby, Shell, SQL, YAML 等。

## 依赖

纯 Python 标准库，无额外依赖。
