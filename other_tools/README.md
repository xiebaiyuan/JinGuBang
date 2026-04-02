# Other Tools

用于不易归类但高频的小工具集合。

| 工具名 | 用途 | 使用示例 | 依赖 | 平台支持 | 风险级别 |
|---|---|---|---|---|---|
| `parseminecrash.py` | 解析 Minecraft 崩溃日志 | `python3 other_tools/parseminecrash.py crash.log` | Python 标准库 | 跨平台 | 低 |
| `json_yaml_convert.py` | JSON/YAML 双向转换与格式化 | `python3 other_tools/json_yaml_convert.py -i a.json --to yaml --pretty` | Python 标准库，PyYAML 可选 | 跨平台 | 低 |
| `post.sh` | 通用辅助脚本 | `bash other_tools/post.sh` | Shell | macOS/Linux | 低 |
| `text_convert.py` | 万能文本转换：Base64/URL/Hex 编解码、时间戳、JWT 解码 | `python3 other_tools/text_convert.py b64enc "hello"` | Python 标准库 | 跨平台 | 低 |
| `csv_quick_stats.py` | CSV 文件快速统计：行列数、类型检测、数值统计 | `python3 other_tools/csv_quick_stats.py data.csv` | Python 标准库 | 跨平台 | 低 |

## 何时使用

- 临时格式转换优先用 `json_yaml_convert.py`。
- 崩溃日志快速初筛用 `parseminecrash.py`。
- 编解码/时间戳转换用 `text_convert.py`（支持管道输入）。
- 快速了解 CSV 文件结构用 `csv_quick_stats.py`。

## 相关文档

- `other_tools/parse_me_crash.md`
