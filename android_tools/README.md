# Android Tools

用于 Android Native 库（SO/ELF）分析与对比。

| 工具名 | 用途 | 使用示例 | 依赖 | 平台支持 | 风险级别 |
|---|---|---|---|---|---|
| `android_so_analyzer.py` | 全量分析 SO 结构、符号、依赖和 Android 优化项 | `python3 android_tools/android_so_analyzer.py android_tools/test_hash_both.so` | `readelf/objdump/file/strings` | macOS/Linux | 低 |
| `check_android_so.py` | 快速检查关键链接器选项 | `python3 android_tools/check_android_so.py libfoo.so` | `readelf` 或等价工具 | macOS/Linux | 低 |
| `apk_native_libs_report.py` | 扫描 APK/AAB 中 `lib/<abi>/*.so` 并输出 ABI 体积报告 | `python3 android_tools/apk_native_libs_report.py -i app.apk --format text` | Python 标准库 | 跨平台 | 低 |
| `so_symbol_diff.py` | 对比两个 SO 的导出符号增删变化 | `python3 android_tools/so_symbol_diff.py --old old.so --new new.so -o diff.txt` | `nm` 或 `objdump` | macOS/Linux | 中 |
| `test_so_analyzer.py` | 分析器基础测试脚本 | `python3 android_tools/test_so_analyzer.py` | Python 标准库 | 跨平台 | 低 |

## 何时使用

- 新接入第三方 so 包时先跑 `android_so_analyzer.py`。
- 升级 native SDK 后用 `so_symbol_diff.py` 做导出符号回归检查。
- 发布前用 `apk_native_libs_report.py` 检查 ABI 覆盖与体积分布。

## 相关文档

- `android_tools/android_so_analyzer_readme.md`
