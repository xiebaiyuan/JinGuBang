# Android Tools

Android native library (SO/ELF) analysis tools.

## Tools

- `android_so_analyzer.py`: Comprehensive SO/ELF analyzer (headers, symbols, dependencies, Android optimization checks).
- `check_android_so.py`: Quick validation for linker options such as `--hash-style=gnu` and `--pack-dyn-relocs=android`.
- `test_so_analyzer.py`: Basic test script for analyzer output.
- `test_hash_both.so`: Test sample binary.

## Docs

- `android_so_analyzer_readme.md`

## Quick Start

```bash
python3 android_so_analyzer.py test_hash_both.so
python3 check_android_so.py test_hash_both.so
python3 test_so_analyzer.py
```
