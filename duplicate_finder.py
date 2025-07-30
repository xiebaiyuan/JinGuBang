#!/usr/bin/env python3
# filepath: duplicate_finder.py

import os
import re
import sys
import hashlib
import argparse
from pathlib import Path
import shutil
import subprocess
from datetime import datetime
from typing import Dict, List, Tuple, Set
from tqdm import tqdm
import logging
import colorama
from colorama import Fore, Style
import filecmp
import difflib
from collections import defaultdict

# 初始化颜色支持
colorama.init()

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# 正则表达式匹配类似 "文件名 (1).ext", "文件名 副本.ext" 等格式
DUPLICATE_PATTERNS = [
    r'^(.+)[ _]?\((\d+)\)(\.[^.]*)?$',  # 匹配 "文件名 (1).扩展名" 或 "文件名(1).扩展名"
    r'^(.+)[ _]?副本(\d*)(\.[^.]*)?$',  # 匹配 "文件名 副本.扩展名" 或 "文件名副本2.扩展名"
    r'^(.+)[ _]?copy(\d*)(\.[^.]*)?$',  # 匹配 "文件名 copy.扩展名" 或 "文件名copy2.扩展名"
    r'^(.+)[ _]?复制(\d*)(\.[^.]*)?$',  # 匹配 "文件名 复制.扩展名" 或 "文件名复制2.扩展名"
]

# 用于存储文件信息的数据结构
class FileInfo:
    def __init__(self, path, size, md5=None):
        self.path = path
        self.size = size
        self.md5 = md5

    def __str__(self):
        return f"{self.path} ({format_size(self.size)})"

def format_size(size_bytes):
    """将字节大小转换为人类可读格式"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024 or unit == 'GB':
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024

def get_md5(file_path):
    """计算文件MD5哈希值"""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def get_base_filename(filename):
    """尝试获取可能的原始文件名"""
    # 获取文件扩展名和基本名
    base, ext = os.path.splitext(filename)
    
    for pattern in DUPLICATE_PATTERNS:
        match = re.match(pattern, filename)
        if match:
            # 返回捕获的基本文件名部分
            base_name = match.group(1)
            extension = ext if ext else (match.group(match.lastindex) or "")
            return base_name + extension
    
    # 检查是否有数字编号的模式，比如 "filename (1).jpg"
    # 这里单独处理，以处理各种复杂文件名情况
    match = re.match(r'^(.+)[ _]?\((\d+)\)(\.[^.]*)?$', filename)
    if match:
        # 文件名中包含 (数字)
        base_name = match.group(1).strip()
        extension = ext
        possible_original = base_name + extension
        return possible_original
    
    return None

# 简化的重复文件名检测规则
def is_likely_duplicate_name(filename):
    """判断文件名是否可能是副本"""
    patterns = [
        r'\(\d+\)',       # (1), (2), ...
        r'副本\d*',        # 副本, 副本1, ...
        r'copy\d*',       # copy, copy1, ...
        r'复制\d*',        # 复制, 复制1, ...
        r' \d+$',         # 文件名后加空格和数字
        r' \d+\.',        # 文件名后加空格和数字后接扩展名
    ]
    
    for pattern in patterns:
        if re.search(pattern, filename):
            return True
    return False

def calculate_file_hash(file_path, hash_algorithm='md5'):
    """
    计算文件的哈希值，支持多种哈希算法
    """
    hash_func = None
    if hash_algorithm == 'md5':
        hash_func = hashlib.md5()
    elif hash_algorithm == 'sha1':
        hash_func = hashlib.sha1()
    elif hash_algorithm == 'sha256':
        hash_func = hashlib.sha256()
    else:
        raise ValueError(f"不支持的哈希算法: {hash_algorithm}")
        
    with open(file_path, 'rb') as f:
        # 读取文件块并更新哈希
        for chunk in iter(lambda: f.read(4096), b''):
            hash_func.update(chunk)
    return hash_func.hexdigest()

def get_filename_similarity(file1, file2):
    """
    计算两个文件名的相似度，返回0-1之间的值
    """
    basename1 = os.path.basename(file1)
    basename2 = os.path.basename(file2)
    
    # 使用difflib计算字符串相似度
    similarity = difflib.SequenceMatcher(None, basename1, basename2).ratio()
    return similarity

def are_files_identical(file1, file2, min_name_similarity=0.5):
    """
    使用多种方法确认两个文件是否完全相同，并检查文件名相似性
    """
    # 检查文件名相似度
    name_similarity = get_filename_similarity(file1, file2)
    if name_similarity < min_name_similarity:
        return False, name_similarity
    
    # 首先比较文件大小
    if os.path.getsize(file1) != os.path.getsize(file2):
        return False, name_similarity
    
    # 使用filecmp进行快速比较
    if not filecmp.cmp(file1, file2, shallow=False):
        return False, name_similarity
    
    # 使用MD5进行哈希比较
    if calculate_file_hash(file1, 'md5') != calculate_file_hash(file2, 'md5'):
        return False, name_similarity
        
    # 文件可能很大，通过以上三重检查已经足够可靠
    # 如果需要更高安全性，可以再添加SHA-256比较
    return True, name_similarity

def find_duplicates(directory, exclude_dirs=None, size_only=False, global_search=False, hash_algorithm='md5', min_name_similarity=0.5):
    """
    在指定目录中查找重复文件
    
    参数:
        directory: 要扫描的目录
        exclude_dirs: 要排除的目录列表
        size_only: 是否只基于文件大小判断重复
        global_search: 是否全局搜索（不限于同一目录）
        hash_algorithm: 使用的哈希算法
        min_name_similarity: 最小文件名相似度阈值
    
    返回：
        original_files: 原始文件列表
        duplicate_files: 重复文件列表
    """
    print(f"正在扫描目录: {directory}")
    print(f"使用哈希算法: {hash_algorithm}")
    print(f"最小文件名相似度阈值: {min_name_similarity}")
    
    if exclude_dirs is None:
        exclude_dirs = []
    print(f"排除的目录: {', '.join(exclude_dirs) if exclude_dirs else '无'}")
    
    start_time = datetime.now()
    
    # 第一阶段：按照文件大小分组
    size_map = defaultdict(list)
    file_count = 0
    
    for root, _, files in os.walk(directory):
        # 检查是否在排除目录中
        if any(os.path.abspath(root).startswith(os.path.abspath(ex_dir)) for ex_dir in exclude_dirs):
            continue
            
        for filename in files:
            file_path = os.path.join(root, filename)
            try:
                file_size = os.path.getsize(file_path)
                size_map[file_size].append(file_path)
                file_count += 1
            except (IOError, OSError):
                print(f"警告: 无法访问文件 {file_path}")
    
    print(f"共扫描了 {file_count} 个文件")
    
    # 过滤出具有相同大小的文件组
    potential_duplicates = {size: files for size, files in size_map.items() if len(files) > 1}
    print(f"发现 {len(potential_duplicates)} 组大小相同的文件")
    
    # 第二阶段：对大小相同的文件计算哈希值
    hash_map = defaultdict(list)
    
    if not size_only:
        for size, files in potential_duplicates.items():
            for file_path in files:
                try:
                    file_hash = calculate_file_hash(file_path, hash_algorithm)
                    hash_map[file_hash].append(file_path)
                except Exception as e:
                    print(f"警告: 计算文件哈希时出错 {file_path}: {e}")
    else:
        # 如果仅使用大小判断，跳过哈希计算
        for size, files in potential_duplicates.items():
            hash_key = f"size_{size}"  # 使用大小作为哈希键
            hash_map[hash_key] = files
    
    # 第三阶段：进行最终确认
    duplicates = []
    skipped_by_name = 0
    
    for file_hash, files in hash_map.items():
        if len(files) <= 1:
            continue
            
        # 如果不是全局搜索，则按目录分组
        if not global_search:
            # 按目录分组
            dir_groups = defaultdict(list)
            for file_path in files:
                dir_path = os.path.dirname(file_path)
                dir_groups[dir_path].append(file_path)
            
            # 只处理同一目录内有多个文件的情况
            for dir_path, dir_files in dir_groups.items():
                if len(dir_files) > 1:
                    group_duplicates = []
                    reference_file = dir_files[0]
                    group_duplicates.append(reference_file)
                    
                    for file_path in dir_files[1:]:
                        is_identical, similarity = are_files_identical(reference_file, file_path, min_name_similarity)
                        if is_identical:
                            group_duplicates.append(file_path)
                        else:
                            if similarity < min_name_similarity:
                                skipped_by_name += 1
                    
                    if len(group_duplicates) > 1:
                        duplicates.append(group_duplicates)
        else:
            # 全局搜索模式
            reference_file = files[0]
            confirmed_duplicates = [reference_file]
            
            for file_path in files[1:]:
                is_identical, similarity = are_files_identical(reference_file, file_path, min_name_similarity)
                if is_identical:
                    confirmed_duplicates.append(file_path)
                else:
                    if similarity < min_name_similarity:
                        skipped_by_name += 1
            
            if len(confirmed_duplicates) > 1:
                duplicates.append(confirmed_duplicates)
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    print(f"\n扫描完成，耗时: {duration:.2f} 秒")
    print(f"因文件名不相似而跳过: {skipped_by_name} 个文件")
    print(f"发现 {len(duplicates)} 组重复文件")
    
    # 处理返回值格式，区分原始文件和重复文件
    original_files = []
    duplicate_files = []
    
    for group in duplicates:
        # 优先保留不带重复后缀的文件作为原始文件
        # 如果没有不带后缀的文件，则使用第一个文件
        orig_path = group[0]
        for file_path in group:
            filename = os.path.basename(file_path)
            if not is_likely_duplicate_name(filename):
                orig_path = file_path
                break
        
        orig_size = os.path.getsize(orig_path)
        orig_md5 = calculate_file_hash(orig_path, hash_algorithm) if not size_only else None
        original_files.append(FileInfo(orig_path, orig_size, orig_md5))
        
        # 剩余文件视为重复文件
        for dup_path in group:
            if dup_path != orig_path:
                dup_size = os.path.getsize(dup_path)
                dup_md5 = calculate_file_hash(dup_path, hash_algorithm) if not size_only else None
                duplicate_files.append(FileInfo(dup_path, dup_size, dup_md5))
    
    return original_files, duplicate_files

def move_to_trash(file_path):
    """将文件移动到废纸篓"""
    if sys.platform == 'darwin':  # macOS
        try:
            # 使用AppleScript将文件移动到废纸篓
            subprocess.run(['osascript', '-e', f'tell application "Finder" to delete POSIX file "{file_path}"'], 
                          check=True, capture_output=True)
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"移动到废纸篓失败: {e}")
            return False
    else:
        # 非macOS系统，尝试使用send2trash库
        try:
            # 动态导入以避免依赖问题
            import send2trash
            send2trash.send2trash(file_path)
            return True
        except ImportError:
            logger.error("未找到send2trash库。在非macOS系统上需要安装: pip install send2trash")
            return False
        except Exception as e:
            logger.error(f"移动到废纸篓失败: {e}")
            return False

def main():
    parser = argparse.ArgumentParser(description='查找并移除重复文件')
    parser.add_argument('directory', help='要扫描的目录')
    parser.add_argument('--exclude', nargs='*', default=[], help='要排除的目录')
    parser.add_argument('--confirm', action='store_true', help='自动确认删除而不提示')
    parser.add_argument('--debug', action='store_true', help='启用调试日志')
    parser.add_argument('--size-only', action='store_true', help='仅基于文件大小判断重复（不计算MD5）')
    parser.add_argument('--global', dest='global_search', action='store_true', 
                        help='全局查找重复文件（默认只在同一目录内查找）')
    parser.add_argument('--algorithm', choices=['md5', 'sha1', 'sha256'], default='md5',
                        help='使用的哈希算法 (默认: md5)')
    parser.add_argument('--min-name-similarity', type=float, default=0.5,
                        help='最小文件名相似度 (0.0-1.0, 默认: 0.5)')
    parser.add_argument('--output', help='输出结果到文件')
    args = parser.parse_args()
    
    # 设置调试级别
    if args.debug:
        logger.setLevel(logging.DEBUG)
        
    directory = os.path.abspath(args.directory)
    exclude_dirs = [os.path.abspath(p) for p in args.exclude]
    
    if not os.path.isdir(directory):
        logger.error(f"目录不存在: {directory}")
        return 1
    
    # 查找重复文件
    original_files, duplicate_files = find_duplicates(
        directory, 
        exclude_dirs, 
        args.size_only, 
        args.global_search, 
        args.algorithm,
        args.min_name_similarity
    )
    
    if not duplicate_files:
        print(f"{Fore.GREEN}未发现重复文件。{Style.RESET_ALL}")
        return 0
    
    # 计算可释放空间
    saved_space = sum(f.size for f in duplicate_files)
    
    # 显示重复文件
    print(f"\n{Fore.CYAN}分析结果:{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}找到 {len(duplicate_files)} 个重复文件，可释放 {format_size(saved_space)}{Style.RESET_ALL}")
    
    # 按原始文件分组显示
    duplicates_by_original = {}
    for dup in duplicate_files:
        # 查找对应的原始文件
        for orig in original_files:
            if (args.size_only and orig.size == dup.size) or \
               (not args.size_only and orig.md5 == dup.md5):
                if orig not in duplicates_by_original:
                    duplicates_by_original[orig] = []
                duplicates_by_original[orig].append(dup)
                break
    
    # 显示分组结果和输出到文件
    group_index = 1
    output_lines = []
    
    for orig, dups in duplicates_by_original.items():
        group_line = f"\n[组 {group_index}]"
        orig_line = f"  保留文件: {orig.path} ({format_size(orig.size)})"
        
        print(f"{Fore.CYAN}{group_line}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}{orig_line}{Style.RESET_ALL}")
        
        output_lines.append(group_line)
        output_lines.append(orig_line)
        
        for i, dup in enumerate(dups, 1):
            dup_line = f"  {i}. 重复文件: {dup.path}"
            print(f"{Fore.RED}{dup_line}{Style.RESET_ALL}")
            output_lines.append(dup_line)
            
        if not args.size_only and orig.md5:
            md5_line = f"  MD5: {orig.md5}"
            print(md5_line)
            output_lines.append(md5_line)
            
        group_index += 1
    
    # 如果指定了输出文件，将结果写入文件
    if args.output:
        try:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write("\n".join(output_lines))
            print(f"\n结果已保存到文件: {args.output}")
        except Exception as e:
            logger.error(f"无法写入输出文件: {e}")
    
    # 确认操作
    if not args.confirm:
        confirm = input(f"\n{Fore.YELLOW}确认将这些重复文件移动到废纸篓？ (yes/no): {Style.RESET_ALL}").lower()
        if confirm not in ['yes', 'y']:
            print("操作已取消。")
            return 0
    
    # 移动到废纸篓
    success_count = 0
    failed_count = 0
    
    for dup in duplicate_files:
        print(f"正在移动到废纸篓: {dup.path}")
        if move_to_trash(dup.path):
            success_count += 1
        else:
            failed_count += 1
    
    # 显示摘要
    print(f"\n{Fore.GREEN}操作完成:{Style.RESET_ALL}")
    print(f"  成功移动: {success_count} 个文件")
    if failed_count > 0:
        print(f"  {Fore.RED}失败: {failed_count} 个文件{Style.RESET_ALL}")
    print(f"  释放空间: {format_size(saved_space)}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())