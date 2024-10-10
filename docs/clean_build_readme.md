
## 完整使用示例

	1.	查看帮助：

./move_build_dirs_trash.sh
用法：./move_build_dirs_trash.sh 目标目录 [--dry-run] [额外的目录模式...]


	2.	干运行模式，删除默认模式的目录：

./move_build_dirs_trash.sh /path/to/dir --dry-run


	3.	干运行模式，删除默认模式和 .cxx 目录：

./move_build_dirs_trash.sh /path/to/dir --dry-run .cxx


	4.	实际删除模式，删除默认模式和多个额外目录：

./move_build_dirs_trash.sh /path/to/dir .cxx .vs .idea

	•	注意：实际删除操作会提示确认，输入 yes 才会执行删除。
