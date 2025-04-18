#!/usr/bin/env python3
# filepath: /Users/xiebaiyuan/tools/move_build_dirs_trash.py

import os
import sys
import subprocess
import argparse
import re
import shutil
import time
import tempfile
import fnmatch
from collections import defaultdict
from datetime import datetime
import json
from pathlib import Path


# 颜色定义
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[0;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'  # No Color


# 日志文件
LOG_DIR = Path(f"/Users/{os.environ.get('USER')}/Downloads")
LOG_TIMESTAMP = datetime.now().strftime('%Y%m%d_%H%M%S')
LOG_FILE = LOG_DIR / f"clean_{LOG_TIMESTAMP}.log"
DELETED_ITEMS_FILE = LOG_DIR / f"deleted_items_{LOG_TIMESTAMP}.json"
DELETED_SUMMARY_FILE = LOG_DIR / f"deleted_summary_{LOG_TIMESTAMP}.txt"

def log_to_file(message):
    """写入日志到文件"""
    with open(LOG_FILE, 'a') as log_file:
        log_file.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")

def save_deleted_items(deleted_items):
    """保存已删除项目的详细信息到 JSON 文件"""
    with open(DELETED_ITEMS_FILE, 'w') as f:
        json.dump(deleted_items, f, indent=2)
    
    # 同时创建一个易读的文本摘要文件
    with open(DELETED_SUMMARY_FILE, 'w') as f:
        f.write(f"删除操作摘要 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 60 + "\n\n")
        
        # 写入统计信息
        total_dirs = sum(item['is_dir'] for item in deleted_items)
        total_files = len(deleted_items) - total_dirs
        f.write(f"删除目录数: {total_dirs}\n")
        f.write(f"删除文件数: {total_files}\n")
        f.write(f"总计: {len(deleted_items)} 个项目\n\n")
        
        # 按目录分组写入
        current_parent = ""
        for item in sorted(deleted_items, key=lambda x: x['path']):
            parent = os.path.dirname(item['path'])
            
            # 当父目录变化时，打印一个新的标题
            if parent != current_parent:
                if current_parent:
                    f.write("\n")
                f.write(f"目录: {parent}\n")
                f.write("-" * 50 + "\n")
                current_parent = parent
            
            # 打印项目信息
            item_type = "目录" if item['is_dir'] else "文件"
            size_kb = item['size_kb']
            if size_kb >= 1048576:
                size_str = f"{size_kb/1048576:.2f} GB"
            elif size_kb >= 1024:
                size_str = f"{size_kb/1024:.2f} MB"
            else:
                size_str = f"{size_kb} KB"
                
            f.write(f"  {os.path.basename(item['path'])} ({item_type}, {size_str}, 匹配模式: {item['pattern']})\n")


def print_color(color, message):
    """带颜色打印消息"""
    print(f"{color}{message}{Colors.NC}")


def format_size(size_kb):
    """格式化文件大小显示"""
    if size_kb >= 1048576:  # 1 GB = 1048576 KB
        return f"{Colors.RED}{size_kb / 1048576:.2f} GB{Colors.NC}"
    elif size_kb >= 1024:  # 1 MB = 1024 KB
        return f"{Colors.YELLOW}{size_kb / 1024:.2f} MB{Colors.NC}"
    else:
        return f"{size_kb} KB"


def check_trash_command():
    """检查trash命令是否可用"""
    try:
        subprocess.run(['which', 'trash'], stdout=subprocess.PIPE, check=True)
        return True
    except subprocess.SubprocessError:
        return False


class BuildDirCleaner:
    def __init__(self):
        self.version = "1.0.0"
        self.parser = self.setup_argument_parser()
        self.args = None
        
        # 默认模式
        self.default_dir_patterns = [
            'build', 'cmake-build-*', 'build.lite.*', 'build.mml.*', 'build.macos.*', 
            'build.opt', 'tmp', 'CMakeFiles', 'node_modules', 'dist', '.cache', 
            '.tmp', '.sass-cache', 'coverage', 'target', 'obj', 'out', 'Debug', 'Release'
        ]
        self.default_file_patterns = ['*.log', 'libpaddle_api_light_bundled.a']
        
        # 处理结果统计
        self.dir_type_counts = defaultdict(int)
        self.file_type_counts = defaultdict(int)
        self.total_sizes = defaultdict(int)
        self.deleted_dirs = []
        self.items = []
        self.sorted_items = []
        self.skipped_items = 0
        self.failed_items = 0
        self.success_items = 0
        
        # 终端宽度
        try:
            self.term_width = os.get_terminal_size().columns
        except:
            self.term_width = 80

    def setup_argument_parser(self):
        """设置命令行参数解析"""
        parser = argparse.ArgumentParser(
            description='目录和文件清理工具',
            formatter_class=argparse.RawTextHelpFormatter
        )
        parser.add_argument('target_dir', help='目标目录')
        parser.add_argument('--dry-run', action='store_true', help='模拟运行，不实际删除文件')
        parser.add_argument('--no-confirm', action='store_true', help='不需要确认直接删除')
        parser.add_argument('--exclude', action='append', default=[], help='排除指定模式的目录或文件')
        parser.add_argument('--file', action='append', default=[], help='包含文件匹配模式')
        parser.add_argument('--whitelist-dir', action='append', default=['.git', '.mgit', 'third-party'],
                           help='添加白名单目录（默认包括 .git, .mgit 和 third-party）')
        parser.add_argument('extra_patterns', nargs='*', help='额外的模式')
        return parser

    def parse_args(self):
        """解析命令行参数"""
        self.args = self.parser.parse_args()
        
        # 检查目标目录
        if not os.path.isdir(self.args.target_dir):
            print_color(Colors.RED, f"错误：目标目录 {self.args.target_dir} 不存在")
            sys.exit(1)
        
        # 合并模式
        self.all_dir_patterns = self.default_dir_patterns + self.args.extra_patterns
        self.all_file_patterns = self.default_file_patterns + self.args.file

    def find_matching_items(self):
        """查找匹配的项目"""
        print_color(Colors.BLUE, "正在查找匹配的项目...")
        
        matches = []
        
        # 遍历目录
        for root, dirs, files in os.walk(self.args.target_dir):
            # 检查是否在白名单目录中
            if any(white_dir in root.split(os.sep) for white_dir in self.args.whitelist_dir):
                continue
                
            # 检查目录
            for dirname in dirs:
                full_path = os.path.join(root, dirname)
                
                # 检查是否匹配目录模式
                for pattern in self.all_dir_patterns:
                    if fnmatch.fnmatch(dirname, pattern) or fnmatch.fnmatch(full_path, f"*/{pattern}/*"):
                        # 检查排除模式
                        if not any(fnmatch.fnmatch(dirname, exclude) for exclude in self.args.exclude):
                            matches.append(full_path)
                            break
                
            # 检查文件
            for filename in files:
                full_path = os.path.join(root, filename)
                
                # 检查是否匹配文件模式
                matched = False
                
                # 检查是否匹配目录模式（文件在匹配目录内）
                for pattern in self.all_dir_patterns:
                    if fnmatch.fnmatch(os.path.basename(root), pattern):
                        matched = True
                        break
                
                # 检查是否匹配文件模式
                if not matched:
                    for pattern in self.all_file_patterns:
                        if fnmatch.fnmatch(filename, pattern):
                            matched = True
                            break
                
                if matched and not any(fnmatch.fnmatch(filename, exclude) for exclude in self.args.exclude):
                    matches.append(full_path)
        
        self.items = matches
        
        if not self.items:
            print_color(Colors.YELLOW, "未找到符合条件的目录或文件。")
            sys.exit(0)
            
        # 按路径长度排序（从长到短）确保子目录/文件在父目录之前
        print_color(Colors.BLUE, "正在对项目进行排序...")
        self.sorted_items = sorted(self.items, key=len, reverse=True)

    def get_matching_pattern(self, item):
        """获取匹配的模式"""
        basename = os.path.basename(item)
        
        # 检查目录模式
        for pattern in self.all_dir_patterns:
            if '*' in pattern:
                if fnmatch.fnmatch(basename, pattern) or item.find(f"/{pattern}/") >= 0:
                    return pattern
            elif basename == pattern:
                return pattern
        
        # 检查文件模式
        for pattern in self.all_file_patterns:
            if '*' in pattern:
                if fnmatch.fnmatch(basename, pattern):
                    return pattern
            elif basename == pattern:
                return pattern
                
        return "未匹配模式"

    def should_skip(self, item):
        """检查路径是否应该被跳过（是否在已删除的父目录中）"""
        for path in self.deleted_dirs:
            if item.startswith(path):
                return True
        return False

    def update_stats(self, item, is_delete=False):
        """更新统计信息"""
        if os.path.isdir(item):
            # 获取目录类型
            item_type = self.get_matching_pattern(item)
            self.dir_type_counts[item_type] += 1
            
            # 如果是删除操作，更新大小
            if is_delete:
                try:
                    # 使用du命令获取目录大小
                    output = subprocess.check_output(['du', '-sk', item], stderr=subprocess.DEVNULL)
                    size = int(output.split()[0])
                    self.total_sizes[item_type] += size
                except:
                    pass
        elif os.path.isfile(item):
            # 获取文件类型
            item_type = self.get_matching_pattern(item)
            if item_type == "未匹配模式":
                # 使用文件扩展名作为类型
                _, ext = os.path.splitext(item)
                item_type = ext if ext else "无扩展名"
                
            self.file_type_counts[item_type] += 1
            
            # 如果是删除操作，更新大小
            if is_delete:
                try:
                    size = os.path.getsize(item) // 1024  # 转换为KB
                    self.total_sizes[item_type] += size
                except:
                    pass

    def update_stats_display(self, progress, total, action="analyzing"):
        """更新并显示统计信息"""
        percent = progress * 100 // total
        
        # 构建统计显示
        stats_display = []
        
        # 目录统计
        if self.dir_type_counts:
            dir_stats = []
            for type_name, count in sorted(self.dir_type_counts.items(), key=lambda x: x[1], reverse=True)[:3]:
                size = self.total_sizes[type_name]
                if size >= 1048576:  # GB
                    size_str = f"{size/1048576:.1f}GB"
                elif size >= 1024:  # MB
                    size_str = f"{size/1024:.1f}MB"
                else:
                    size_str = f"{size}KB"
                dir_stats.append(f"{type_name}({count}个, {size_str})")
            
            stats_display.append("目录: " + " ".join(dir_stats))
            
            if len(self.dir_type_counts) > 3:
                stats_display[-1] += f" 等{len(self.dir_type_counts)}种"
        
        # 文件统计
        if self.file_type_counts:
            file_stats = []
            for type_name, count in sorted(self.file_type_counts.items(), key=lambda x: x[1], reverse=True)[:3]:
                file_stats.append(f"{type_name}({count}个)")
            
            stats_display.append("文件: " + " ".join(file_stats))
            
            if len(self.file_type_counts) > 3:
                stats_display[-1] += f" 等{len(self.file_type_counts)}种"
        
        # 显示进度条
        bar_size = 20
        completed = bar_size * percent // 100
        remaining = bar_size - completed
        
        progress_bar = "["
        progress_bar += "#" * completed
        progress_bar += "-" * remaining
        progress_bar += "]"
        
        # 适应终端宽度的状态行
        status_line = f"{action.title()}进度: {progress_bar} {percent}% ({progress}/{total})"
        
        # 添加统计信息，但确保行长度不超过终端宽度
        stats_str = " | " + " | ".join(stats_display)
        available_width = self.term_width - len(status_line) - 10  # 预留一些空间
        
        if len(stats_str) > available_width:
            stats_str = stats_str[:available_width-3] + "..."
            
        status_line += stats_str
        
        # 显示状态行
        color = Colors.BLUE if action == "analyzing" else Colors.GREEN
        sys.stdout.write(f"\r\033[K{color}{status_line}{Colors.NC}")
        sys.stdout.flush()

    def show_final_stats(self):
        """显示最终统计信息"""
        # 清除状态行
        sys.stdout.write("\r\033[K")
        sys.stdout.flush()
        
        print_color(Colors.GREEN, "====== 删除操作统计 ======")
        
        # 目录统计
        if self.dir_type_counts:
            print_color(Colors.BLUE, "目录统计:")
            for type_name, count in sorted(self.dir_type_counts.items(), key=lambda x: x[1], reverse=True):
                size = self.total_sizes[type_name]
                if size >= 1048576:  # GB
                    size_str = f"{size/1048576:.2f} GB"
                elif size >= 1024:  # MB
                    size_str = f"{size/1024:.2f} MB"
                else:
                    size_str = f"{size} KB"
                print(f"  {Colors.YELLOW}{type_name}{Colors.NC}: {count} 个目录, 共 {size_str}")
        
        # 文件统计
        if self.file_type_counts:
            print_color(Colors.BLUE, "文件统计:")
            for type_name, count in sorted(self.file_type_counts.items(), key=lambda x: x[1], reverse=True):
                size = self.total_sizes[type_name]
                if size >= 1048576:  # GB
                    size_str = f"{size/1048576:.2f} GB"
                elif size >= 1024:  # MB
                    size_str = f"{size/1024:.2f} MB"
                else:
                    size_str = f"{size} KB"
                print(f"  {Colors.YELLOW}{type_name}{Colors.NC}: {count} 个文件, 共 {size_str}")
        
        # 总计统计
        total_dirs = sum(self.dir_type_counts.values())
        total_files = sum(self.file_type_counts.values())
        total_size = sum(self.total_sizes.values())
        
        print_color(Colors.GREEN, "总计:")
        print(f"  {Colors.BLUE}目录:{Colors.NC} {total_dirs} 个")
        print(f"  {Colors.BLUE}文件:{Colors.NC} {total_files} 个")
        
        if total_size >= 1048576:
            print(f"  {Colors.BLUE}总大小:{Colors.NC} {total_size/1048576:.2f} GB")
        elif total_size >= 1024:
            print(f"  {Colors.BLUE}总大小:{Colors.NC} {total_size/1024:.2f} MB")
        else:
            print(f"  {Colors.BLUE}总大小:{Colors.NC} {total_size} KB")

    def analyze_items(self):
        """分析项目阶段"""
        print_color(Colors.BLUE, "正在分析项目...")
        total_count = len(self.sorted_items)
        current = 0

        # 初始化统计变量
        for item in self.sorted_items:
            current += 1
            self.update_stats(item)
            
            # 每10个项目更新一次显示
            if current % 10 == 0 or current == total_count:
                self.update_stats_display(current, total_count, "analyzing")
                
        # 清除进度显示
        sys.stdout.write("\r\033[K")
        sys.stdout.flush()
        print_color(Colors.GREEN, "分析完成！")
        
        # 显示统计摘要
        self.show_final_stats()

    def calculate_total_size(self):
        """计算总大小"""
        print_color(Colors.BLUE, "正在计算总大小...")
        total_size = 0
        valid_items = 0
        
        for item in self.sorted_items:
            if os.path.exists(item):
                try:
                    if os.path.isdir(item):
                        output = subprocess.check_output(['du', '-sk', item], stderr=subprocess.DEVNULL)
                        size = int(output.split()[0])
                    else:
                        size = os.path.getsize(item) // 1024  # 转换为KB
                    
                    total_size += size
                    valid_items += 1
                except:
                    pass
        
        print_color(Colors.GREEN, f"总计将删除的项目数量：{valid_items}")
        print(f"{Colors.GREEN}总体积：{format_size(total_size)}")
        
        return total_size

    def show_pre_delete_summary(self, total_size):
        """显示删除前的汇总信息，帮助用户做出决定"""
        print_color(Colors.BLUE, "\n======== 删除前汇总信息 ========")
        print_color(Colors.YELLOW, "以下是将要删除的内容概览:")
        
        # 1. 目录统计 (按数量排序)
        if self.dir_type_counts:
            print_color(Colors.BLUE, "\n目录汇总:")
            for pattern, count in sorted(self.dir_type_counts.items(), key=lambda x: x[1], reverse=True):
                print(f"  {Colors.GREEN}{pattern}{Colors.NC}: {count} 个目录")
            
            # 列出前5个最大的目录
            print_color(Colors.BLUE, "\n占用空间最大的目录 (前5个):")
            top_dirs = []
            for item in self.sorted_items:
                if os.path.isdir(item) and os.path.exists(item):
                    try:
                        output = subprocess.check_output(['du', '-sk', item], stderr=subprocess.DEVNULL)
                        size = int(output.split()[0])
                        top_dirs.append((item, size))
                    except:
                        pass
                        
            # 按大小排序并显示前5个
            for item, size in sorted(top_dirs, key=lambda x: x[1], reverse=True)[:5]:
                if size >= 1048576:  # GB
                    size_str = f"{size/1048576:.2f} GB"
                elif size >= 1024:  # MB
                    size_str = f"{size/1024:.2f} MB"
                else:
                    size_str = f"{size} KB"
                print(f"  {Colors.YELLOW}{item}{Colors.NC}: {size_str}")
        
        # 2. 文件类型统计
        if self.file_type_counts:
            print_color(Colors.BLUE, "\n文件类型汇总:")
            for pattern, count in sorted(self.file_type_counts.items(), key=lambda x: x[1], reverse=True):
                print(f"  {Colors.GREEN}{pattern}{Colors.NC}: {count} 个文件")
        
        # 3. 路径分布统计
        print_color(Colors.BLUE, "\n按路径分布:")
        path_counts = defaultdict(int)
        for item in self.sorted_items:
            if os.path.exists(item):
                # 获取前3级路径
                parts = item.split(os.sep)
                if len(parts) > 3:
                    path_prefix = os.sep.join(parts[:3])
                else:
                    path_prefix = os.sep.join(parts[:-1])
                path_counts[path_prefix] += 1
        
        # 显示主要路径分布
        for path, count in sorted(path_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"  {Colors.YELLOW}{path}{Colors.NC}: {count} 个项目")
        
        if len(path_counts) > 5:
            print(f"  ... 等共 {len(path_counts)} 个路径")
        
        # 4. 总体统计
        print_color(Colors.BLUE, "\n总体统计:")
        print(f"  {Colors.GREEN}总项目数:{Colors.NC} {len(self.sorted_items)} 个")
        print(f"  {Colors.GREEN}目录数量:{Colors.NC} {sum(self.dir_type_counts.values())} 个")
        print(f"  {Colors.GREEN}文件数量:{Colors.NC} {sum(self.file_type_counts.values())} 个")
        
        # 显示总大小
        if total_size >= 1048576:
            print(f"  {Colors.GREEN}总体积:{Colors.NC} {total_size/1048576:.2f} GB")
        elif total_size >= 1024:
            print(f"  {Colors.GREEN}总体积:{Colors.NC} {total_size/1024:.2f} MB")
        else:
            print(f"  {Colors.GREEN}总体积:{Colors.NC} {total_size} KB")
        
        # 5. 提示查看方式
        print_color(Colors.BLUE, "\n您可以采取以下操作:")
        print(f"  1. 输入 'yes' 确认删除上述内容")
        print(f"  2. 输入任意其他内容取消操作")
        print(f"  3. 使用 --dry-run 参数重新运行脚本，仅查看不删除")
        print(f"  4. 使用 --exclude 参数排除特定模式的文件或目录")

    def delete_items(self):
        """删除项目阶段"""
        print_color(Colors.BLUE, "开始执行删除操作...")
        
        # 重置统计
        self.dir_type_counts.clear()
        self.file_type_counts.clear()
        self.total_sizes.clear()
        
        # 用于跟踪所有成功删除的项目
        deleted_items = []
        
        total_items = len(self.sorted_items)
        progress = 0
        
        for item in self.sorted_items:
            # 检查项目是否在已删除的父目录中
            if self.should_skip(item):
                log_to_file(f"跳过项目(父目录已删除)：{item}")
                self.skipped_items += 1
                progress += 1
                continue
            
            # 检查项目是否仍然存在
            if not os.path.exists(item):
                log_to_file(f"跳过项目(不存在)：{item}")
                self.skipped_items += 1
                progress += 1
                continue
            
            log_to_file(f"正在删除项目：{item}")
            
            # 获取项目信息
            is_dir = os.path.isdir(item)
            pattern = self.get_matching_pattern(item)
            
            try:
                # 获取文件/目录大小
                size_kb = 0
                try:
                    if is_dir:
                        output = subprocess.check_output(['du', '-sk', item], stderr=subprocess.DEVNULL)
                        size_kb = int(output.split()[0])
                    else:
                        size_kb = os.path.getsize(item) // 1024  # 转换为KB
                except:
                    # 如果无法获取大小，使用0
                    pass
                
                # 使用trash命令移动到垃圾箱
                subprocess.run(['trash', item], stderr=subprocess.DEVNULL, check=True)
                log_to_file(f"成功删除项目：{item}")
                self.success_items += 1
                
                # 记录已删除的项目信息
                deleted_items.append({
                    'path': item,
                    'is_dir': is_dir,
                    'pattern': pattern,
                    'size_kb': size_kb,
                    'timestamp': datetime.now().isoformat()
                })
                
                # 更新统计信息
                self.update_stats(item, True)
                
                # 如果是目录，添加到已删除路径列表
                if is_dir:
                    self.deleted_dirs.append(item + os.sep)
                    
            except subprocess.SubprocessError:
                log_to_file(f"删除失败：{item}")
                self.failed_items += 1
            
            # 更新进度
            progress += 1
            
            # 每5个项目更新一次显示
            if progress % 5 == 0 or progress == total_items:
                self.update_stats_display(progress, total_items, "deleting")
                
        # 清除进度显示
        sys.stdout.write("\r\033[K")
        sys.stdout.flush()
        print_color(Colors.GREEN, "删除操作完成！")
        
        # 保存已删除项目的详细记录
        if deleted_items:
            save_deleted_items(deleted_items)
            print_color(Colors.GREEN, f"删除记录已保存到:")
            print(f"  - 详细日志: {LOG_FILE}")
            print(f"  - 删除记录 (JSON): {DELETED_ITEMS_FILE}")
            print(f"  - 删除摘要: {DELETED_SUMMARY_FILE}")
        
        # 显示最终统计
        self.show_final_stats()
        
        # 显示额外的统计信息
        print_color(Colors.GREEN, f"成功删除：{self.success_items} 个项目")
        print_color(Colors.YELLOW, f"跳过项目：{self.skipped_items} 个项目")
        if self.failed_items > 0:
            print_color(Colors.RED, f"删除失败：{self.failed_items} 个项目")

    def run(self):
        """运行清理过程"""
        # 显示标题
        print_color(Colors.BLUE, "======================================")
        print_color(Colors.BLUE, f"目录和文件清理工具 v{self.version}")
        print_color(Colors.BLUE, "======================================")
        
        # 检查trash命令
        if not check_trash_command():
            print_color(Colors.RED, "错误：未找到 'trash' 命令，请先安装。")
            print("可以使用 'brew install trash' 进行安装。")
            sys.exit(1)
        
        # 解析参数
        self.parse_args()
        
        # 显示基本信息
        print_color(Colors.YELLOW, "警告：此脚本会删除匹配特定模式的目录和文件。请确保您了解将要删除的内容。")
        print_color(Colors.GREEN, f"白名单目录（不会被删除）：{', '.join(self.args.whitelist_dir)}")
        print_color(Colors.GREEN, f"要删除的目录模式：{', '.join(self.all_dir_patterns)}")
        print_color(Colors.GREEN, f"要删除的文件模式：{', '.join(self.all_file_patterns)}")
        print("---")
        
        # 查找匹配项目
        self.find_matching_items()
        
        # 分析项目
        self.analyze_items()
        
        # 计算总大小
        total_size = self.calculate_total_size()
        
        # 显示删除前的汇总信息
        self.show_pre_delete_summary(total_size)
        
        # 显示运行模式
        print_color(Colors.BLUE, f"干运行模式: {self.args.dry_run}")
        print_color(Colors.BLUE, f"无需确认模式: {self.args.no_confirm}")
        
        if self.args.dry_run:
            print_color(Colors.YELLOW, "(干运行模式，未实际删除)")
            sys.exit(0)
            
        # 确认
        if not self.args.no_confirm:
            print_color(Colors.YELLOW, "是否确认删除以上项目？输入 'yes' 确认：")
            confirm = input()
            
            if confirm.lower() != 'yes':
                print_color(Colors.YELLOW, "操作已取消。")
                sys.exit(0)
                
        # 执行删除
        self.delete_items()


if __name__ == "__main__":
    cleaner = BuildDirCleaner()
    cleaner.run()