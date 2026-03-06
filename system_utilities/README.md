# System Utilities

System maintenance and environment helper scripts.

## Tools

- `update_zsh_plugin.sh` - Update zsh plugins.
- `collect_ip.sh` - Collect local/network IP information.
- `batch_file_md5.sh` - Batch-calculate MD5 for files in a directory (general-purpose).
- `current_dir_so_md5.sh` - Legacy helper for hashing files in a directory.

## Docs

- `update_zsh_plugin.md`
- `batch_file_md5.md`

## Quick Start

```bash
# Hash all files recursively under current directory
./batch_file_md5.sh

# Hash only .so files under target directory
./batch_file_md5.sh -d ./build -i "*.so" --count
```
