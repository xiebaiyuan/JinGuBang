# Media Tools

用于图片格式转换、批量处理、元数据提取和 Markdown 资源收集。

| 工具名 | 用途 | 使用示例 | 依赖 | 平台支持 | 风险级别 |
|---|---|---|---|---|---|
| `avif_to_png_converter.py` | 批量 AVIF 转 PNG | `python3 media_tools/avif_to_png_converter.py ./in -o ./out -r` | Pillow + pillow-avif-plugin | 跨平台 | 低 |
| `image_batch_resize.py` | 批量改图尺寸并保留目录结构 | `python3 media_tools/image_batch_resize.py -i ./in -o ./out --width 1080 --keep-ratio` | Pillow | 跨平台 | 中 |
| `image_metadata_report.py` | 批量导出图片元数据 CSV/JSON | `python3 media_tools/image_metadata_report.py -i ./imgs --format csv -o report.csv` | Pillow | 跨平台 | 低 |
| `collect_md.py` / `collect.sh` | 收集 Markdown 中引用的资源 | `python3 media_tools/collect_md.py ./docs` | Python 标准库 / Shell | macOS/Linux | 低 |
| `modify_exif.py` | EXIF 元数据修改 | `python3 media_tools/modify_exif.py --help` | Pillow | 跨平台 | 中 |
| `create_test_images.py` | 生成测试图片样本 | `python3 media_tools/create_test_images.py` | Pillow | 跨平台 | 低 |
| `setup_kindle_converter.sh` / `run_kindle_converter.sh` | Kindle 转换工具环境准备与执行 | `bash media_tools/run_kindle_converter.sh ./imgs` | Python, Pillow | macOS/Linux | 中 |
| `apple_music_player.py` | Apple Music 辅助脚本 | `python3 media_tools/apple_music_player.py --help` | Python 标准库 | macOS | 低 |

## 何时使用

- 批量统一图尺寸时用 `image_batch_resize.py`。
- 要快速统计图片基础信息时用 `image_metadata_report.py`。
- 迁移 Markdown 文档资源时用 `collect_md.py`。

## 相关文档

- `media_tools/avif_to_png_converter.md`
- `media_tools/kindle_image_converter_readme.md`
