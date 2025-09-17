#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Android SO文件分析工具
用于全面分析Android SO库文件的各项信息，包括：
- 文件基本信息（大小、哈希值等）
- SO库架构信息
- 导出符号表
- 依赖的其他库
- 对齐方式（支持16KB对齐检测）
- ELF头信息
- 哈希样式（GNU Hash/SysV Hash）
- 重定位表压缩（Android Pack Relocations）
- NDK版本分析（通过Clang版本推断）
"""

import os
import sys
import hashlib
import subprocess
import argparse
import json
import textwrap
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Union
import re
import platform

def colorize(text, color_code):
    """为终端输出添加颜色"""
    if sys.stdout.isatty():  # 只在真实终端中应用颜色
        return f"\033[{color_code}m{text}\033[0m"
    return text

def print_header(text):
    """打印带颜色的标题"""
    header = f" {text} "
    terminal_width = os.get_terminal_size().columns if sys.stdout.isatty() else 80
    padding = "=" * ((terminal_width - len(header)) // 2)
    print(colorize(f"\n{padding}{header}{padding}", "1;36"))

def print_subheader(text):
    """打印带颜色的子标题"""
    print(colorize(f"\n▶ {text}", "1;33"))

def print_info(label, value, color="0;32"):
    """打印带颜色的信息行"""
    print(f"  {colorize(label, '1;37')}: {colorize(value, color)}")

def print_warning(text):
    """打印警告信息"""
    print(colorize(f"  ⚠️  {text}", "1;33"))

def print_error(text):
    """打印错误信息"""
    print(colorize(f"  ❌ {text}", "1;31"))

def print_success(text):
    """打印成功信息"""
    print(colorize(f"  ✅ {text}", "1;32"))

def print_table(headers, rows, column_widths=None):
    """打印格式化表格"""
    if not rows:
        return
        
    if not column_widths:
        # 计算每列的最大宽度
        column_widths = [len(h) for h in headers]
        for row in rows:
            for i, cell in enumerate(row):
                cell_str = str(cell)
                if i < len(column_widths):
                    column_widths[i] = max(column_widths[i], len(cell_str))
    
    # 打印表头
    header_line = "  "
    for i, header in enumerate(headers):
        header_line += colorize(header.ljust(column_widths[i] + 2), "1;37")
    print(header_line)
    
    # 打印分隔线
    separator = "  " + "─" * (sum(column_widths) + len(headers) * 2)
    print(colorize(separator, "0;37"))
    
    # 打印数据行
    for row in rows:
        row_line = "  "
        for i, cell in enumerate(row):
            cell_str = str(cell)
            if i < len(column_widths):
                row_line += cell_str.ljust(column_widths[i] + 2)
        print(row_line)

def print_symbol_details(symbols, max_symbols=20, filter_type=None, show_all=False):
    """打印详细的符号信息"""
    # 符号类型说明
    type_descriptions = {
        'T': '导出函数 (text)',
        'W': '弱符号',
        'R': '只读数据 (read-only data)',
        'D': '初始化数据 (data)',
        'B': '未初始化数据 (BSS)',
        'U': '未定义符号 (依赖外部)',
        'V': '弱对象',
        'w': '弱未定义符号'
    }
    
    filtered_symbols = symbols
    if filter_type:
        filtered_symbols = [s for s in symbols if s['type'] == filter_type]
    
    headers = ["类型", "地址", "符号名"]
    rows = []
    
    display_count = len(filtered_symbols) if show_all else min(max_symbols, len(filtered_symbols))
    
    for i in range(display_count):
        symbol = filtered_symbols[i]
        sym_type = symbol['type']
        sym_addr = symbol.get('address', 'N/A')
        rows.append([sym_type, sym_addr, symbol['name']])
    
    if rows:
        print_table(headers, rows)
        if not show_all and len(filtered_symbols) > max_symbols:
            print(f"\n  ... 共有 {len(filtered_symbols)} 个符号，只显示前 {max_symbols} 个。使用 --show-all-symbols 选项查看全部。")
    else:
        print_warning("没有找到符号")

def get_file_basic_info(file_path):
    """获取文件的基本信息：大小、时间戳、MD5、SHA1、SHA256等"""
    file_stats = os.stat(file_path)
    file_size = file_stats.st_size
    modified_time = datetime.fromtimestamp(file_stats.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
    
    # 计算各种哈希值
    md5_hash = hashlib.md5()
    sha1_hash = hashlib.sha1()
    sha256_hash = hashlib.sha256()
    
    with open(file_path, 'rb') as f:
        # 读取文件内容并更新哈希对象
        chunk = f.read(8192)
        while chunk:
            md5_hash.update(chunk)
            sha1_hash.update(chunk)
            sha256_hash.update(chunk)
            chunk = f.read(8192)
    
    return {
        'file_name': os.path.basename(file_path),
        'file_path': file_path,
        'file_size': {
            'bytes': file_size,
            'human_readable': format_size(file_size)
        },
        'modified_time': modified_time,
        'md5': md5_hash.hexdigest(),
        'sha1': sha1_hash.hexdigest(),
        'sha256': sha256_hash.hexdigest()
    }

def format_size(size_bytes):
    """将字节大小转换为人类可读格式"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024 or unit == 'GB':
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024

def get_so_architecture(file_path):
    """获取SO库的架构信息"""
    try:
        result = subprocess.run(['file', file_path], capture_output=True, text=True, check=True)
        file_info = result.stdout
        
        arch_info = {
            'file_info': file_info.strip(),
            'architecture': 'unknown'
        }
        
        # 分析架构类型
        if 'ARM aarch64' in file_info:
            arch_info['architecture'] = 'arm64-v8a'
        elif 'ARM,' in file_info:
            arch_info['architecture'] = 'armeabi-v7a'
        elif 'Intel 80386' in file_info:
            arch_info['architecture'] = 'x86'
        elif 'x86-64' in file_info:
            arch_info['architecture'] = 'x86_64'
        
        return arch_info
    except subprocess.CalledProcessError as e:
        return {'error': f"Error getting architecture info: {e}"}

def get_symbol_type_description(symbol_type):
    """获取符号类型的描述"""
    descriptions = {
        'T': '导出函数 (text section)',
        'W': '弱符号 (weak symbol)',
        'R': '只读数据 (read-only data)',
        'D': '初始化数据 (initialized data)',
        'B': '未初始化数据 (uninitialized data)',
        'U': '未定义符号 (依赖外部)',
        'V': '弱对象 (weak object)',
        'w': '弱未定义符号'
    }
    return descriptions.get(symbol_type, '未知符号类型')

def get_exported_symbols(file_path):
    """获取SO库导出的符号表"""
    ndk_root = os.environ.get('NDK_ROOT')
    if not ndk_root:
        return {'error': 'NDK_ROOT环境变量未设置'}
    
    try:
        # 获取文件架构信息
        arch_info = get_so_architecture(file_path)
        arch = arch_info.get('architecture', 'unknown')
        
        # 选择适当的nm工具
        nm_path = None
        if arch == 'arm64-v8a':
            nm_path = os.path.join(ndk_root, 'toolchains', 'llvm', 'prebuilt', 'darwin-x86_64', 'bin', 'llvm-nm')
        elif arch == 'armeabi-v7a':
            nm_path = os.path.join(ndk_root, 'toolchains', 'llvm', 'prebuilt', 'darwin-x86_64', 'bin', 'llvm-nm')
        elif arch == 'x86':
            nm_path = os.path.join(ndk_root, 'toolchains', 'llvm', 'prebuilt', 'darwin-x86_64', 'bin', 'llvm-nm')
        elif arch == 'x86_64':
            nm_path = os.path.join(ndk_root, 'toolchains', 'llvm', 'prebuilt', 'darwin-x86_64', 'bin', 'llvm-nm')
        
        if not nm_path or not os.path.exists(nm_path):
            # 如果找不到特定的nm工具，尝试使用系统默认的nm
            nm_path = 'nm'
        
        # 获取所有符号
        result = subprocess.run([nm_path, '-D', '--demangle', file_path], capture_output=True, text=True)
        
        if result.returncode != 0:
            return {'error': f'Error getting symbols: {result.stderr}'}
        
        # 解析符号表输出
        all_symbols = []
        for line in result.stdout.splitlines():
            if line.strip():
                parts = line.split()
                if len(parts) >= 3:  # 地址、类型、符号名
                    addr = parts[0]
                    symbol_type = parts[1]
                    symbol_name = ' '.join(parts[2:])  # 支持有空格的符号名
                    all_symbols.append({
                        'address': addr,
                        'type': symbol_type, 
                        'name': symbol_name
                    })
                elif len(parts) == 2:  # 类型、符号名（无地址）
                    symbol_type = parts[0]
                    symbol_name = parts[1]
                    all_symbols.append({
                        'address': 'N/A',
                        'type': symbol_type, 
                        'name': symbol_name
                    })
        
        # 获取仅定义的导出符号（即暴露的符号）
        defined_result = subprocess.run([nm_path, '-D', '--defined-only', '--demangle', file_path], 
                                        capture_output=True, text=True)
        
        exported_symbols = []
        if defined_result.returncode == 0:
            for line in defined_result.stdout.splitlines():
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 3:  # 地址、类型、符号名
                        addr = parts[0]
                        symbol_type = parts[1]
                        symbol_name = ' '.join(parts[2:])  # 支持有空格的符号名
                        exported_symbols.append({
                            'address': addr,
                            'type': symbol_type, 
                            'name': symbol_name
                        })
                    elif len(parts) == 2:  # 类型、符号名（无地址）
                        symbol_type = parts[0]
                        symbol_name = parts[1]
                        exported_symbols.append({
                            'address': 'N/A',
                            'type': symbol_type, 
                            'name': symbol_name
                        })
        
        # 按类型排序符号
        all_symbols.sort(key=lambda x: x['type'])
        exported_symbols.sort(key=lambda x: x['type'])
        
        # 统计所有符号类型
        all_symbol_stats = {}
        for symbol in all_symbols:
            sym_type = symbol['type']
            if sym_type in all_symbol_stats:
                all_symbol_stats[sym_type] += 1
            else:
                all_symbol_stats[sym_type] = 1
        
        # 统计导出符号类型
        exported_symbol_stats = {}
        for symbol in exported_symbols:
            sym_type = symbol['type']
            if sym_type in exported_symbol_stats:
                exported_symbol_stats[sym_type] += 1
            else:
                exported_symbol_stats[sym_type] = 1
        
        # 将统计数据转换为列表，便于排序
        all_symbol_stats_list = [{'type': t, 'count': c, 'description': get_symbol_type_description(t)} 
                                for t, c in all_symbol_stats.items()]
        all_symbol_stats_list.sort(key=lambda x: x['count'], reverse=True)
        
        exported_symbol_stats_list = [{'type': t, 'count': c, 'description': get_symbol_type_description(t)} 
                                     for t, c in exported_symbol_stats.items()]
        exported_symbol_stats_list.sort(key=lambda x: x['count'], reverse=True)
        
        return {
            'total_symbols': len(all_symbols),
            'total_exported_symbols': len(exported_symbols),
            'symbol_stats': all_symbol_stats,
            'symbol_stats_list': all_symbol_stats_list,
            'exported_symbol_stats': exported_symbol_stats,
            'exported_symbol_stats_list': exported_symbol_stats_list,
            'symbols': all_symbols,
            'exported_symbols': exported_symbols
        }
    except Exception as e:
        return {'error': f'Error analyzing symbols: {str(e)}'}

def get_dependencies(file_path):
    """获取SO库的依赖信息"""
    try:
        # 使用readelf工具获取依赖库信息
        ndk_root = os.environ.get('NDK_ROOT')
        if not ndk_root:
            readelf_cmd = 'readelf'  # 使用系统自带的readelf
        else:
            arch_info = get_so_architecture(file_path)
            arch = arch_info.get('architecture', 'unknown')
            readelf_cmd = os.path.join(ndk_root, 'toolchains', 'llvm', 'prebuilt', 'darwin-x86_64', 'bin', 'llvm-readelf')
            if not os.path.exists(readelf_cmd):
                readelf_cmd = 'readelf'  # 备选方案
        
        result = subprocess.run([readelf_cmd, '-d', file_path], capture_output=True, text=True)
        
        if result.returncode != 0:
            return {'error': f'Error getting dependencies: {result.stderr}'}
        
        # 解析依赖库
        dependencies = []
        for line in result.stdout.splitlines():
            if 'NEEDED' in line and 'Shared library' in line:
                # 提取括号中的库名
                lib_start = line.find('[') + 1
                lib_end = line.find(']')
                if lib_start > 0 and lib_end > lib_start:
                    lib_name = line[lib_start:lib_end]
                    dependencies.append(lib_name)
        
        return {
            'total_dependencies': len(dependencies),
            'dependencies': dependencies
        }
    except Exception as e:
        return {'error': f'Error analyzing dependencies: {str(e)}'}

def check_alignment(file_path):
    """检查SO文件的对齐方式，包括ZIP对齐和LOAD段对齐"""
    try:
        # 获取文件大小用于ZIP对齐检测
        file_stats = os.stat(file_path)
        file_size = file_stats.st_size
        
        alignment_info = {
            'file_size': file_size,
            'zip_alignment': {},
            'load_alignment': {}
        }
        
        # 检测ZIP对齐（Android APK中的SO文件对齐）
        # ZIP对齐是为了优化APK中的SO文件在内存中的加载和映射
        # 常见的对齐大小：16KB (0x4000) 或 64KB (0x10000)
        zip_alignments = [16384, 65536]  # 16KB, 64KB
        zip_alignment_found = False
        for align in zip_alignments:
            if file_size % align == 0:
                alignment_info['zip_alignment'] = {
                    'alignment': f'0x{align:x}',
                    'alignment_bytes': align,
                    'alignment_human': f'{align//1024}KB',
                    'is_aligned': True,
                    'purpose': 'APK压缩优化',
                    'benefit': '减少内存映射开销'
                }
                zip_alignment_found = True
                break
        
        if not zip_alignment_found:
            # 找到最接近的对齐
            min_remainder = float('inf')
            best_align = 0
            for align in zip_alignments:
                remainder = file_size % align
                if remainder < min_remainder:
                    min_remainder = remainder
                    best_align = align
            alignment_info['zip_alignment'] = {
                'alignment': f'0x{best_align:x}',
                'alignment_bytes': best_align,
                'alignment_human': f'{best_align//1024}KB',
                'is_aligned': False,
                'remainder': min_remainder,
                'purpose': 'APK压缩优化',
                'benefit': '减少内存映射开销',
                'recommendation': f'建议填充 {min_remainder} 字节以达到 {best_align//1024}KB 对齐'
            }
        
        # 使用readelf获取段信息
        readelf_cmd = 'readelf'  # 先尝试系统自带的readelf
        objdump_cmd = 'objdump'
        
        # 尝试使用NDK中的工具
        ndk_root = os.environ.get('NDK_ROOT')
        if ndk_root:
            ndk_readelf = os.path.join(ndk_root, 'toolchains', 'llvm', 'prebuilt', 'darwin-x86_64', 'bin', 'llvm-readelf')
            ndk_objdump = os.path.join(ndk_root, 'toolchains', 'llvm', 'prebuilt', 'darwin-x86_64', 'bin', 'llvm-objdump')
            if os.path.exists(ndk_readelf):
                readelf_cmd = ndk_readelf
            if os.path.exists(ndk_objdump):
                objdump_cmd = ndk_objdump
        
        # 首先尝试使用objdump -p命令获取程序头信息（更准确的对齐信息）
        try:
            result = subprocess.run([objdump_cmd, '-p', file_path], capture_output=True, text=True)
            
            if result.returncode == 0:
                alignment_info['load_alignment']['raw_info'] = ''
                found_align = False
                max_align = 0
                
                # 解析LOAD段的对齐信息
                for line in result.stdout.splitlines():
                    line = line.strip()
                    # 记录原始信息
                    if 'LOAD' in line:
                        alignment_info['load_alignment']['raw_info'] += line + '\n'
                        
                        # 尝试解析对齐值，格式可能是 "align 2**14" 或其他格式
                        align_match = re.search(r'align\s+2\*\*(\d+)', line)
                        if align_match:
                            align_power = int(align_match.group(1))
                            align_value = 2 ** align_power
                            # 保存最大的对齐值
                            if align_value > max_align:
                                max_align = align_value
                                alignment_info['load_alignment']['alignment'] = f'0x{align_value:x}'
                                alignment_info['load_alignment']['alignment_bytes'] = align_value
                                alignment_info['load_alignment']['alignment_power'] = align_power
                                found_align = True
                
                if found_align:
                    # 添加对齐评估信息
                    align_value = alignment_info['load_alignment'].get('alignment_bytes', 0)
                    if align_value >= 65536:  # 64K对齐
                        alignment_info['load_alignment']['assessment'] = 'Excellent (64K alignment)'
                    elif align_value >= 16384:  # 16K对齐
                        alignment_info['load_alignment']['assessment'] = 'Very Good (16K alignment)'
                    elif align_value >= 4096:  # 4K对齐
                        alignment_info['load_alignment']['assessment'] = 'Good (4K alignment)'
                    elif align_value >= 1024:  # 1K对齐
                        alignment_info['load_alignment']['assessment'] = 'Acceptable (1K alignment)'
                    else:
                        alignment_info['load_alignment']['assessment'] = f'Sub-optimal ({align_value} bytes alignment)'
                    
                    return alignment_info
        except Exception as e:
            # 如果objdump失败，记录错误但继续尝试readelf
            pass
        
        # 如果objdump方法失败，尝试使用readelf -l命令
        result = subprocess.run([readelf_cmd, '-l', file_path], capture_output=True, text=True)
        
        if result.returncode != 0:
            # 如果readelf也失败，尝试使用file命令作为备选方案
            file_result = subprocess.run(['file', file_path], capture_output=True, text=True)
            alignment_info['load_alignment']['file_info'] = file_result.stdout.strip()
            return alignment_info
        
        # 分析对齐信息
        alignment_info['load_alignment']['raw_info'] = ''
        found_align = False
        max_align = 0
        
        for line in result.stdout.splitlines():
            # 保存原始输出供参考
            if 'LOAD' in line:
                alignment_info['load_alignment']['raw_info'] += line + '\n'
                
                # 尝试解析对齐值，格式可能是 "Align 0x1000" 
                align_match = re.search(r'Align\s+(0x[0-9a-fA-F]+)', line)
                if align_match:
                    align_str = align_match.group(1)
                    align_value = int(align_str, 16)
                    # 保存最大的对齐值
                    if align_value > max_align:
                        max_align = align_value
                        alignment_info['load_alignment']['alignment'] = align_str
                        alignment_info['load_alignment']['alignment_bytes'] = align_value
                        found_align = True
        
        # 如果无法从readelf输出中解析对齐信息，使用启发式方法
        if not found_align:
            # 尝试从file命令获取一些信息
            file_result = subprocess.run(['file', file_path], capture_output=True, text=True)
            alignment_info['load_alignment']['file_info'] = file_result.stdout.strip()
            
            # 大多数现代SO库使用4K对齐
            alignment_info['load_alignment']['alignment'] = '0x1000'  # 假设4K对齐
            alignment_info['load_alignment']['alignment_bytes'] = 4096
            alignment_info['load_alignment']['estimation_method'] = 'heuristic'
        
        # 添加对齐评估信息
        align_value = alignment_info['load_alignment'].get('alignment_bytes', 0)
        if align_value >= 65536:  # 64K对齐
            alignment_info['load_alignment']['assessment'] = 'Excellent (64K alignment)'
        elif align_value >= 16384:  # 16K对齐
            alignment_info['load_alignment']['assessment'] = 'Very Good (16K alignment)'
        elif align_value >= 4096:  # 4K对齐
            alignment_info['load_alignment']['assessment'] = 'Good (4K alignment)'
        elif align_value >= 1024:  # 1K对齐
            alignment_info['load_alignment']['assessment'] = 'Acceptable (1K alignment)'
        else:
            alignment_info['load_alignment']['assessment'] = f'Sub-optimal ({align_value} bytes alignment)'
        
        return alignment_info
    except Exception as e:
        return {'error': f'Error analyzing alignment: {str(e)}'}

def get_elf_header_info(file_path):
    """获取ELF头信息"""
    try:
        ndk_root = os.environ.get('NDK_ROOT')
        if not ndk_root:
            readelf_cmd = 'readelf'
        else:
            readelf_cmd = os.path.join(ndk_root, 'toolchains', 'llvm', 'prebuilt', 'darwin-x86_64', 'bin', 'llvm-readelf')
            if not os.path.exists(readelf_cmd):
                readelf_cmd = 'readelf'
        
        result = subprocess.run([readelf_cmd, '-h', file_path], capture_output=True, text=True)
        
        if result.returncode != 0:
            return {'error': f'Error getting ELF header info: {result.stderr}'}
        
        # 解析ELF头信息
        header_info = {}
        for line in result.stdout.splitlines():
            line = line.strip()
            if ':' in line:
                key, value = line.split(':', 1)
                header_info[key.strip()] = value.strip()
        
        return header_info
    except Exception as e:
        return {'error': f'Error analyzing ELF header: {str(e)}'}

def get_section_info(file_path):
    """获取节区信息"""
    try:
        ndk_root = os.environ.get('NDK_ROOT')
        if not ndk_root:
            readelf_cmd = 'readelf'
        else:
            readelf_cmd = os.path.join(ndk_root, 'toolchains', 'llvm', 'prebuilt', 'darwin-x86_64', 'bin', 'llvm-readelf')
            if not os.path.exists(readelf_cmd):
                readelf_cmd = 'readelf'
        
        result = subprocess.run([readelf_cmd, '-S', file_path], capture_output=True, text=True)
        
        if result.returncode != 0:
            return {'error': f'Error getting section info: {result.stderr}'}
        
        # 解析节区信息
        sections = []
        lines = result.stdout.splitlines()
        header_found = False
        
        for line in lines:
            line = line.strip()
            if 'Section Headers:' in line:
                header_found = True
                continue
            
            if header_found and line and line[0] == '[' and ']' in line:
                parts = line.split()
                if len(parts) >= 7:
                    section = {
                        'index': parts[0].strip('[]'),
                        'name': parts[1],
                        'type': parts[2],
                        'address': parts[3],
                        'offset': parts[4],
                        'size': parts[5],
                    }
                    sections.append(section)
        
        # 计算节区大小统计
        total_size = 0
        section_sizes = {}
        
        for section in sections:
            try:
                size = int(section['size'], 16)
                total_size += size
                section_sizes[section['name']] = {
                    'size_hex': section['size'],
                    'size_bytes': size,
                    'size_human': format_size(size)
                }
            except ValueError:
                pass
        
        return {
            'total_sections': len(sections),
            'total_size': {
                'bytes': total_size,
                'human_readable': format_size(total_size)
            },
            'section_sizes': section_sizes,
            'sections': sections
        }
    except Exception as e:
        return {'error': f'Error analyzing sections: {str(e)}'}

def check_hash_style(file_path):
    """检查SO文件使用的哈希样式（GNU Hash或SysV Hash）
    
    哈希表是ELF文件中用于符号查找的数据结构。有两种主要类型：
    1. SysV Hash（.hash节）：传统哈希表，兼容所有Android版本
    2. GNU Hash（.gnu.hash节）：更高效的哈希表，但需要Android 6.0+
    
    不同的链接标志会影响哈希表的生成：
    - --hash-style=sysv：只生成SysV哈希表
    - --hash-style=gnu：只生成GNU哈希表
    - --hash-style=both：同时生成两种哈希表（兼容性好但文件更大）
    
    Returns:
        dict: 哈希样式分析结果
    """
    try:
        # 获取readelf命令
        ndk_root = os.environ.get('NDK_ROOT')
        if not ndk_root:
            readelf_cmd = 'readelf'
        else:
            readelf_cmd = os.path.join(ndk_root, 'toolchains', 'llvm', 'prebuilt', 'darwin-x86_64', 'bin', 'llvm-readelf')
            if not os.path.exists(readelf_cmd):
                readelf_cmd = 'readelf'
        
        # 使用readelf -S检查节区名称
        result = subprocess.run([readelf_cmd, '-S', file_path], capture_output=True, text=True)
        
        if result.returncode != 0:
            return {'error': f'Error analyzing hash style: {result.stderr}'}
        
        # 检查是否存在.gnu.hash和.hash节
        has_gnu_hash = '.gnu.hash' in result.stdout
        has_sysv_hash = '.hash' in result.stdout
        
        # 分析哈希样式
        if has_gnu_hash and has_sysv_hash:
            hash_style = 'both'
            compatibility = 'all'
            description = '同时使用GNU和SysV哈希表 (兼容所有Android版本)'
            recommendation = '如果最小SDK ≥ 23 (Android 6.0)，可使用 --hash-style=gnu 减小文件大小'
            link_flag = '-Wl,--hash-style=both'
        elif has_gnu_hash:
            hash_style = 'gnu'
            compatibility = '≥23 (Android 6.0+)'
            description = '仅使用GNU哈希表 (Android 6.0+)'
            recommendation = '如果需要支持Android 5.x，需改用 --hash-style=both'
            link_flag = '-Wl,--hash-style=gnu'
        elif has_sysv_hash:
            hash_style = 'sysv'
            compatibility = 'all'
            description = '仅使用SysV哈希表 (传统格式)'
            recommendation = '如果最小SDK ≥ 23 (Android 6.0)，建议使用 --hash-style=gnu 减小文件大小'
            link_flag = '-Wl,--hash-style=sysv'
        else:
            hash_style = 'unknown'
            compatibility = 'unknown'
            description = '未检测到哈希表'
            recommendation = '检查文件是否为有效的共享库'
            link_flag = 'unknown'
        
        return {
            'hash_style': hash_style,
            'compatibility': compatibility,
            'description': description,
            'recommendation': recommendation,
            'has_gnu_hash': has_gnu_hash,
            'has_sysv_hash': has_sysv_hash,
            'link_flag': link_flag,
            'sdk_impact': '哈希样式影响SO库大小和符号查找性能'
        }
    except Exception as e:
        return {'error': f'Error analyzing hash style: {str(e)}'}

def check_relocation_packing(file_path):
    """检查SO文件是否使用了重定位表压缩
    
    重定位表压缩（--pack-dyn-relocs=android）是一种减小SO库大小的技术：
    1. 传统：使用.rel.dyn或.rela.dyn节
    2. 压缩：使用Android格式的压缩重定位表，节约空间
    
    注意：压缩重定位表要求minSdk ≥ 23 (Android 6.0+)
    
    Returns:
        dict: 重定位表分析结果
    """
    try:
        # 获取readelf命令
        ndk_root = os.environ.get('NDK_ROOT')
        if not ndk_root:
            readelf_cmd = 'readelf'
        else:
            readelf_cmd = os.path.join(ndk_root, 'toolchains', 'llvm', 'prebuilt', 'darwin-x86_64', 'bin', 'llvm-readelf')
            if not os.path.exists(readelf_cmd):
                readelf_cmd = 'readelf'
        
        # 使用readelf -S检查节区名称
        result = subprocess.run([readelf_cmd, '-S', file_path], capture_output=True, text=True)
        
        if result.returncode != 0:
            return {'error': f'Error analyzing relocation packing: {result.stderr}'}
        
        # Android重定位表压缩使用.relr.dyn节
        has_relr = '.relr.dyn' in result.stdout
        
        # 传统重定位表使用.rel.dyn或.rela.dyn
        has_traditional_rel = '.rel.dyn' in result.stdout
        has_traditional_rela = '.rela.dyn' in result.stdout
        
        # 获取重定位表大小
        section_info = get_section_info(file_path)
        rel_size = 0
        relr_size = 0
        
        if 'section_sizes' in section_info:
            for section_name, size_info in section_info['section_sizes'].items():
                if section_name in ['.rel.dyn', '.rela.dyn']:
                    rel_size += size_info.get('size_bytes', 0)
                elif section_name == '.relr.dyn':
                    relr_size = size_info.get('size_bytes', 0)
        
        # 分析重定位表压缩状态
        if has_relr:
            reloc_packing = 'android'
            compatibility = '≥23 (Android 6.0+)'
            description = '使用了Android重定位表压缩'
            recommendation = '保持现状，已使用优化'
            link_flag = '-Wl,--pack-dyn-relocs=android'
        elif has_traditional_rel or has_traditional_rela:
            reloc_packing = 'none'
            compatibility = 'all'
            description = '使用传统重定位表'
            recommendation = '如果minSdk ≥ 23 (Android 6.0)，建议使用 --pack-dyn-relocs=android 减小文件大小'
            link_flag = '未使用 --pack-dyn-relocs=android'
        else:
            reloc_packing = 'unknown'
            compatibility = 'unknown'
            description = '未检测到重定位表'
            recommendation = '检查文件是否为有效的共享库'
            link_flag = 'unknown'
        
        return {
            'relocation_packing': reloc_packing,
            'compatibility': compatibility,
            'description': description,
            'recommendation': recommendation,
            'has_relr': has_relr,
            'has_traditional_rel': has_traditional_rel or has_traditional_rela,
            'rel_size': rel_size,
            'relr_size': relr_size,
            'link_flag': link_flag,
            'potential_savings': '对于大型SO库，压缩重定位表可减小数百KB大小'
        }
    except Exception as e:
        return {'error': f'Error analyzing relocation packing: {str(e)}'}

def analyze_clang_ndk_version(file_path):
    """分析SO文件中的Clang版本信息并推断NDK版本
    
    方法：
    1. 使用strings工具提取SO文件中的字符串
    2. 查找Clang版本信息（如"clang version X.Y.Z"）
    3. 查找NDK相关信息
    4. 根据已知的Clang/NDK版本映射关系推断NDK版本
    
    Returns:
        dict: Clang和NDK版本分析结果
    """
    # NDK版本与Clang版本的映射关系
    # 来源: https://developer.android.com/ndk/guides/other_build_systems
    NDK_CLANG_MAPPING = {
        # NDK版本: [clang版本, llvm版本]
        "r27": ["18.1.0", "18.1.0"],
        "r26": ["17.0.2", "17.0.6"],
        "r25": ["14.0.7", "14.0.1"],
        "r24": ["14.0.1", "14.0.1"],
        "r23": ["12.0.9", "12.0.9"],
        "r22": ["11.0.5", "11.0.5"],
        "r21": ["9.0.9", "9.0.9"],
        "r20": ["8.0.7", "8.0.7"],
        "r19": ["7.0.2", "7.0.2"],
        "r18": ["6.0.2", "6.0.2"],
        "r17": ["6.0.2", "6.0.2"],
        "r16": ["5.0.300080", "5.0.300080"],
        "r15": ["5.0.300080", "5.0.300080"],
        "r14": ["4.0.0", "4.0.0"],
        "r13": ["3.8.275480", "3.8.275480"],
        "r12": ["3.8.256229", "3.8.256229"],
    }
    
    try:
        # 提取SO文件中的字符串
        result = subprocess.run(['strings', file_path], capture_output=True, text=True)
        
        if result.returncode != 0:
            return {'error': f'Error extracting strings from file: {result.stderr}'}
        
        content = result.stdout
        
        # 初始化结果
        version_info = {
            'clang_version': 'unknown',
            'clang_version_full': 'unknown',
            'ndk_version': 'unknown',
            'ndk_version_certainty': 'unknown',
            'detection_method': 'unknown',
            'clang_indicators': [],
            'ndk_indicators': []
        }
        
        # 1. 直接查找NDK版本标识
        ndk_direct_patterns = [
            r'Android NDK ([a-z][0-9]+[a-z]?)',
            r'NDK ([a-z][0-9]+[a-z]?)',
            r'android-ndk-([a-z][0-9]+[a-z]?)'
        ]
        
        for pattern in ndk_direct_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                version_info['ndk_version'] = matches[0]
                version_info['ndk_version_certainty'] = 'high'
                version_info['detection_method'] = 'direct'
                version_info['ndk_indicators'].append(f'Found direct NDK version: {matches[0]}')
                break
        
        # 2. 查找Clang版本
        clang_patterns = [
            r'clang version ([0-9]+\.[0-9]+\.[0-9]+)',
            r'clang-([0-9]+\.[0-9]+\.[0-9]+)'
        ]
        
        clang_version = None
        clang_version_full = None
        
        for pattern in clang_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                clang_version = matches[0]
                # 查找完整的clang版本行
                for line in content.splitlines():
                    if f'clang version {clang_version}' in line:
                        clang_version_full = line.strip()
                        break
                version_info['clang_version'] = clang_version
                version_info['clang_version_full'] = clang_version_full or f'clang version {clang_version}'
                version_info['clang_indicators'].append(f'Found Clang version: {clang_version}')
                break
        
        # 如果找不到Clang版本，尝试匹配LLVM版本
        if not clang_version:
            llvm_patterns = [
                r'LLVM version ([0-9]+\.[0-9]+\.[0-9]+)',
                r'libLLVM-([0-9]+\.[0-9]+\.[0-9]+)'
            ]
            
            for pattern in llvm_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    llvm_version = matches[0]
                    version_info['llvm_version'] = llvm_version
                    version_info['clang_indicators'].append(f'Found LLVM version: {llvm_version}')
                    # 通常Clang和LLVM版本是对应的
                    if not clang_version:
                        clang_version = llvm_version
                        version_info['clang_version'] = clang_version
                        version_info['clang_version_full'] = f'inferred from LLVM {llvm_version}'
                    break
        
        # 3. 根据Clang版本推断NDK版本
        if clang_version and version_info['ndk_version'] == 'unknown':
            closest_ndk = None
            closest_diff = float('inf')
            
            clang_version_parts = [int(part) for part in clang_version.split('.')]
            
            for ndk, versions in NDK_CLANG_MAPPING.items():
                clang_ref = versions[0]
                clang_ref_parts = [int(part) for part in clang_ref.split('.')]
                
                # 计算版本差异（只比较主要和次要版本号）
                diff = abs(clang_version_parts[0] - clang_ref_parts[0]) * 100
                if len(clang_version_parts) > 1 and len(clang_ref_parts) > 1:
                    diff += abs(clang_version_parts[1] - clang_ref_parts[1])
                
                if diff < closest_diff:
                    closest_diff = diff
                    closest_ndk = ndk
            
            if closest_ndk:
                version_info['ndk_version'] = closest_ndk
                
                # 确定可信度
                if closest_diff == 0:
                    version_info['ndk_version_certainty'] = 'high'
                elif closest_diff < 5:
                    version_info['ndk_version_certainty'] = 'medium'
                else:
                    version_info['ndk_version_certainty'] = 'low'
                
                version_info['detection_method'] = 'clang_inference'
                version_info['ndk_indicators'].append(
                    f'Inferred from Clang {clang_version} (maps to NDK {closest_ndk}, certainty: {version_info["ndk_version_certainty"]})'
                )
        
        # 4. 查找Android API级别
        api_patterns = [
            r'__ANDROID_API__=([0-9]+)',
            r'android-([0-9]+)'
        ]
        
        for pattern in api_patterns:
            matches = re.findall(pattern, content)
            if matches:
                version_info['android_api_level'] = matches[0]
                version_info['ndk_indicators'].append(f'Found Android API level: {matches[0]}')
                break
        
        # 5. 检查NDK的建议版本（根据当前日期）
        current_date = datetime.now()
        if current_date.year >= 2024:
            recommended_ndk = "r27"
            recommended_reason = "最新稳定版本 (2024年推荐版本)"
        elif current_date.year >= 2023:
            recommended_ndk = "r26"
            recommended_reason = "2023年推荐版本"
        else:
            recommended_ndk = "r25"
            recommended_reason = "稳定长期支持版本"
        
        # 添加推荐信息
        version_info['recommended_ndk'] = recommended_ndk
        version_info['recommended_reason'] = recommended_reason
        
        # 如果检测到的NDK版本小于推荐版本，添加升级建议
        if version_info['ndk_version'] != 'unknown' and version_info['ndk_version'] < recommended_ndk:
            version_info['upgrade_recommendation'] = f"建议升级到NDK {recommended_ndk} ({recommended_reason})"
        
        # 添加NDK映射表的引用（供参考）
        version_info['ndk_clang_reference'] = {
            "reference": "NDK与Clang版本对应关系",
            "mapping": NDK_CLANG_MAPPING
        }
        
        return version_info
    except Exception as e:
        return {'error': f'Error analyzing Clang/NDK version: {str(e)}'}

def get_optimization_level(file_path):
    """尝试检测SO文件的优化级别"""
    try:
        result = subprocess.run(['strings', file_path], capture_output=True, text=True)
        
        if result.returncode != 0:
            return {'error': f'Error analyzing optimization: {result.stderr}'}
        
        content = result.stdout.lower()
        
        # 检查是否有调试信息
        has_debug_info = '.debug_info' in content or '.debug_str' in content
        
        # 检查编译优化级别的标记
        optimization = 'unknown'
        if '-o0' in content:
            optimization = 'O0 (No optimization)'
        elif '-o1' in content:
            optimization = 'O1 (Basic optimization)'
        elif '-o2' in content:
            optimization = 'O2 (Medium optimization)'
        elif '-o3' in content:
            optimization = 'O3 (High optimization)'
        elif '-os' in content:
            optimization = 'Os (Size optimization)'
        elif '-oz' in content:
            optimization = 'Oz (More size optimization)'
        
        # 检查是否有strip过的标记
        is_stripped = not has_debug_info
        
        return {
            'optimization_level': optimization,
            'has_debug_info': has_debug_info,
            'is_stripped': is_stripped
        }
    except Exception as e:
        return {'error': f'Error analyzing optimization: {str(e)}'}

def align_so_file(file_path, alignment=16384, output_path=None):
    """对齐SO文件到指定边界
    
    Args:
        file_path: 原始SO文件路径
        alignment: 对齐边界 (默认16KB)
        output_path: 输出文件路径 (默认覆盖原文件)
    
    Returns:
        dict: 对齐结果信息
    """
    if not os.path.exists(file_path):
        return {'error': f'文件不存在: {file_path}'}
    
    if not file_path.endswith('.so'):
        return {'error': f'不是SO文件: {file_path}'}
    
    # 获取原始文件大小
    original_size = os.path.getsize(file_path)
    
    # 计算对齐后的文件大小
    aligned_size = ((original_size + alignment - 1) // alignment) * alignment
    padding_needed = aligned_size - original_size
    
    if padding_needed == 0:
        return {
            'status': 'already_aligned',
            'original_size': original_size,
            'alignment': alignment,
            'message': f'文件已按 {alignment} 字节对齐'
        }
    
    # 如果没有指定输出路径，使用临时文件
    if output_path is None:
        output_path = file_path + '.aligned'
    
    try:
        # 复制文件并添加填充
        with open(file_path, 'rb') as src:
            with open(output_path, 'wb') as dst:
                # 复制原始内容
                dst.write(src.read())
                # 添加填充 (通常填充0或NOP指令)
                dst.write(b'\x00' * padding_needed)
        
        return {
            'status': 'aligned',
            'original_size': original_size,
            'aligned_size': aligned_size,
            'padding_added': padding_needed,
            'alignment': alignment,
            'output_path': output_path,
            'message': f'成功对齐文件，添加了 {padding_needed} 字节填充'
        }
        
    except Exception as e:
        return {'error': f'对齐失败: {str(e)}'}

def analyze_so_file(file_path):
    """全面分析SO文件"""
    if not os.path.exists(file_path):
        return {'error': f'File not found: {file_path}'}
    
    if not file_path.endswith('.so'):
        return {'error': f'Not a .so file: {file_path}'}
    
    # 收集所有分析结果
    results = {
        'basic_info': get_file_basic_info(file_path),
        'architecture': get_so_architecture(file_path),
        'exported_symbols': get_exported_symbols(file_path),
        'dependencies': get_dependencies(file_path),
        'alignment': check_alignment(file_path),
        'elf_header': get_elf_header_info(file_path),
        'section_info': get_section_info(file_path),
        'optimization': get_optimization_level(file_path),
        'hash_style': check_hash_style(file_path),               # 新增：哈希样式分析
        'relocation_packing': check_relocation_packing(file_path), # 新增：重定位表压缩分析
        'ndk_version': analyze_clang_ndk_version(file_path)      # 新增：NDK版本分析
    }
    
    return results

def analyze_directory(dir_path):
    """分析目录中的所有SO文件"""
    if not os.path.exists(dir_path):
        return {'error': f'Directory not found: {dir_path}'}
    
    results = {}
    so_files = []
    
    # 遍历目录查找所有SO文件
    for root, _, files in os.walk(dir_path):
        for file in files:
            if file.endswith('.so'):
                so_path = os.path.join(root, file)
                so_files.append(so_path)
    
    if not so_files:
        return {'error': f'No .so files found in directory: {dir_path}'}
    
    # 分析每个SO文件
    for so_file in so_files:
        relative_path = os.path.relpath(so_file, dir_path)
        results[relative_path] = analyze_so_file(so_file)
    
    # 添加目录概览信息
    results['summary'] = {
        'total_so_files': len(so_files),
        'directory': dir_path,
        'so_files': so_files
    }
    
    return results

def main():
    parser = argparse.ArgumentParser(
        description='Android SO文件分析工具 - 全面分析Android SO库文件',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  %(prog)s libnative.so                    # 分析单个SO文件
  %(prog)s /path/to/libs -v                # 详细分析目录
  %(prog)s lib.so --symbols all            # 显示所有符号
  %(prog)s lib.so -c --no-color            # 紧凑无色输出
  %(prog)s lib.so -o result.json           # 保存JSON结果
  %(prog)s lib.so --align 16384            # 对齐到16KB边界
  %(prog)s lib.so --align 65536 --align-output aligned.so  # 对齐并指定输出

符号类型说明:
  T: 导出函数    W: 弱符号    R: 只读数据
  D: 初始化数据  B: 未初始化数据 (BSS)
  U: 未定义符号  V: 弱对象

哈希样式说明:
  gnu: 仅GNU哈希表 (Android 6.0+，更小更快)
  sysv: 仅SysV哈希表 (兼容所有Android版本)
  both: 同时使用两种哈希表 (兼容所有版本但更大)

重定位表压缩说明:
  android: 使用Android压缩格式 (Android 6.0+，可减小几百KB)
  none: 使用传统重定位表 (兼容所有Android版本)
        """
    )
    parser.add_argument('path', help='SO文件或包含SO文件的目录路径')
    parser.add_argument('-o', '--output', help='输出JSON文件路径')
    parser.add_argument('-v', '--verbose', action='store_true', help='显示详细输出')
    parser.add_argument('-c', '--compact', action='store_true', help='紧凑输出模式')
    parser.add_argument('--symbols', choices=['exported', 'all'], default='exported', 
                       help='显示符号类型 (默认: exported)')
    parser.add_argument('--filter-symbol-type', help='按符号类型过滤 (例如: T, W, R, D, B, U, V)')
    parser.add_argument('--align', type=int, choices=[4096, 8192, 16384, 32768, 65536], 
                       help='对齐SO文件到指定边界 (字节)')
    parser.add_argument('--align-output', help='对齐后文件输出路径')
    parser.add_argument('--max-symbols', type=int, default=20, help='最多显示的符号数量 (默认: 20)')
    parser.add_argument('--no-color', action='store_true', help='禁用彩色输出')
    args = parser.parse_args()
    
    # 如果禁用颜色，覆盖colorize函数
    if args.no_color:
        global colorize
        colorize = lambda text, color_code: text
    
    # 检查NDK环境变量
    if 'NDK_ROOT' not in os.environ:
        print_warning("NDK_ROOT环境变量未设置，某些分析功能可能受限")
    
    # 分析文件或目录
    path = os.path.abspath(args.path)
    
    # 处理对齐操作
    if args.align:
        print_header("🔧 SO文件对齐工具")
        result = align_so_file(path, args.align, args.align_output)
        if 'error' in result:
            print_error(f"对齐失败: {result['error']}")
        else:
            print_success(result['message'])
            print_info("原始大小", f"{result['original_size']:,} 字节")
            print_info("对齐后大小", f"{result['aligned_size']:,} 字节")
            if result['status'] == 'aligned':
                print_info("填充大小", f"{result['padding_added']:,} 字节")
            if 'output_path' in result:
                print_info("输出文件", result['output_path'])
        return
    if os.path.isfile(path):
        if not args.compact:
            print_header("🔍 ANDROID SO分析工具")
            print_info("分析时间", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            print_info("系统环境", f"{platform.system()} {platform.release()} ({platform.machine()})")
        results = analyze_so_file(path)
    else:
        if not args.compact:
            print_header("🔍 ANDROID SO目录分析工具")
            print_info("分析时间", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            print_info("系统环境", f"{platform.system()} {platform.release()} ({platform.machine()})")
        results = analyze_directory(path)
    
    # 输出结果
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print_success(f"分析结果已保存到: {args.output}")
    else:
        # 打印结果摘要
        if 'error' in results:
            print_error(f"错误: {results['error']}")
        elif 'summary' in results:
            # 目录分析摘要
            if not args.compact:
                print_header("📁 目录分析摘要")
            print_info("目录路径", results['summary']['directory'])
            print_info("SO文件数量", str(results['summary']['total_so_files']))
            
            if not args.compact:
                print_subheader("📋 SO文件列表")
            for idx, so_file in enumerate(results['summary']['so_files'], 1):
                rel_path = os.path.relpath(so_file, path)
                so_info = results[rel_path]
                if 'error' in so_info:
                    print_error(f"{idx}. {rel_path} - 分析错误: {so_info['error']}")
                else:
                    arch = so_info['architecture'].get('architecture', 'unknown')
                    size = so_info['basic_info']['file_size']['human_readable']
                    deps = so_info['dependencies'].get('total_dependencies', 0)
                    if args.compact:
                        print_info(f"{idx}. {rel_path}", f"{arch}, {size}, 依赖:{deps}", "0;36")
                    else:
                        print_info(f"{idx}. {rel_path}", f"{arch}, {size}, 依赖: {deps}个库", "0;36")
        else:
            # 单文件分析摘要
            basic_info = results['basic_info']
            arch_info = results['architecture']
            symbols_info = results['exported_symbols']
            deps_info = results['dependencies']
            align_info = results['alignment']
            opt_info = results['optimization']
            
            print_header("📊 SO文件分析报告")
            
            # 基本信息部分
            if not args.compact:
                print_subheader("📌 基本信息")
            print_info("文件名称", basic_info['file_name'])
            print_info("文件大小", basic_info['file_size']['human_readable'])
            print_info("架构类型", arch_info.get('architecture', 'unknown'))
            
            # 哈希值部分
            if not args.compact:
                print_subheader("🔐 哈希值")
            print_info("MD5", basic_info['md5'])
            print_info("SHA1", basic_info['sha1'])
            print_info("SHA256", basic_info['sha256'][:32] + "...")
            
            # 导出符号部分
            print_subheader("🔣 符号信息")
            if 'error' in symbols_info:
                print_error(f"符号分析失败: {symbols_info['error']}")
            else:
                print_info("所有符号总数", str(symbols_info.get('total_symbols', 'unknown')))
                print_info("导出符号总数", str(symbols_info.get('total_exported_symbols', 'unknown')), "1;33")
                
                # 导出符号类型统计
                if 'exported_symbol_stats_list' in symbols_info and symbols_info['exported_symbol_stats_list']:
                    print_info("导出符号类型统计", "", "1;33")
                    headers = ["类型", "数量", "描述"]
                    rows = []
                    for stat in symbols_info['exported_symbol_stats_list']:
                        rows.append([
                            stat['type'], 
                            stat['count'], 
                            stat['description']
                        ])
                    print_table(headers, rows)
                
                # 所有符号类型统计
                if 'symbol_stats_list' in symbols_info and symbols_info['symbol_stats_list'] and args.verbose:
                    print_info("所有符号类型统计", "")
                    headers = ["类型", "数量", "描述"]
                    rows = []
                    for stat in symbols_info['symbol_stats_list']:
                        rows.append([
                            stat['type'], 
                            stat['count'], 
                            stat['description']
                        ])
                    print_table(headers, rows)
                
                # 如果用户请求显示详细符号信息
                if (args.symbols in ['exported', 'all'] or args.filter_symbol_type) and not args.compact:
                    print_subheader("🔍 详细符号列表")
                elif (args.symbols in ['exported', 'all'] or args.filter_symbol_type) and args.compact:
                    print_info("符号详情", "显示中...")
                
                if args.symbols in ['exported', 'all'] or args.filter_symbol_type:
                    # 根据参数选择显示的符号
                    if args.symbols == 'all':
                        symbols_to_show = symbols_info['symbols']
                        if not args.compact:
                            print_info("显示类型", "所有符号")
                    else:
                        symbols_to_show = symbols_info['exported_symbols']
                        if not args.compact:
                            print_info("显示类型", "导出符号", "1;33")
                    
                    if args.filter_symbol_type:
                        if not args.compact:
                            print_info("过滤类型", f"{args.filter_symbol_type} - {get_symbol_type_description(args.filter_symbol_type)}")
                    
                    # 显示符号列表
                    show_all = (args.symbols == 'all' and not args.filter_symbol_type) or (args.max_symbols is None)
                    print_symbol_details(
                        symbols_to_show, 
                        max_symbols=None if show_all else args.max_symbols,
                        filter_type=args.filter_symbol_type,
                        show_all=show_all
                    )
            
            # 依赖库部分
            if not args.compact:
                print_subheader("🔗 依赖库")
            if 'error' in deps_info:
                print_error(f"依赖分析失败: {deps_info['error']}")
            else:
                deps_count = deps_info.get('total_dependencies', 0)
                print_info("依赖库数量", str(deps_count))
                if deps_count > 0:
                    if args.compact:
                        # 紧凑模式：一行显示所有依赖
                        deps_list = deps_info.get('dependencies', [])
                        print_info("依赖列表", ", ".join(deps_list))
                    else:
                        for idx, dep in enumerate(deps_info.get('dependencies', []), 1):
                            print_info(f"  {idx}.", dep)
            
            # 对齐信息部分
            print_subheader("📏 对齐信息")
            if 'error' in align_info:
                print_error(f"对齐分析失败: {align_info['error']}")
            else:
                # ZIP对齐信息
                zip_align = align_info.get('zip_alignment', {})
                if zip_align:
                    zip_status = "✅ 已对齐" if zip_align.get('is_aligned', False) else "❌ 未对齐"
                    zip_value = zip_align.get('alignment_human', 'unknown')
                    print_info("ZIP对齐", f"{zip_value} {zip_status}", "1;32" if zip_align.get('is_aligned', False) else "1;31")
                    
                    if not args.compact:
                        purpose = zip_align.get('purpose', '')
                        benefit = zip_align.get('benefit', '')
                        if purpose:
                            print_info("对齐目的", purpose, "0;36")
                        if benefit:
                            print_info("性能益处", benefit, "0;36")
                    
                    if not zip_align.get('is_aligned', False) and 'remainder' in zip_align:
                        remainder_kb = zip_align['remainder'] / 1024
                        print_info("偏移量", f"{remainder_kb:.1f} KB", "1;33")
                        if not args.compact and 'recommendation' in zip_align:
                            print_info("修复建议", zip_align['recommendation'], "1;33")
                
                # LOAD段对齐信息
                load_align = align_info.get('load_alignment', {})
                if load_align:
                    load_value = load_align.get('alignment', 'unknown')
                    load_bytes = load_align.get('alignment_bytes', 'unknown')
                    load_power = load_align.get('alignment_power', None)
                    assess = load_align.get('assessment', 'unknown')
                    
                    if load_bytes != 'unknown':
                        if load_power:
                            print_info("LOAD段对齐", f"{load_value} (2^{load_power} = {load_bytes} 字节)")
                        else:
                            print_info("LOAD段对齐", f"{load_value} ({load_bytes} 字节)")
                    else:
                        print_info("LOAD段对齐", load_value)
                        
                    # 根据评估结果选择颜色
                    color = "0;32"  # 默认绿色
                    if "Excellent" in assess:
                        color = "1;32"  # 亮绿色
                    elif "Very Good" in assess:
                        color = "0;32"  # 绿色
                    elif "Good" in assess:
                        color = "0;36"  # 青色
                    elif "Acceptable" in assess:
                        color = "1;33"  # 亮黄色
                    elif "Sub-optimal" in assess:
                        color = "1;31"  # 亮红色
                        
                    print_info("对齐评估", assess, color)
                
                # 综合建议
                zip_aligned = align_info.get('zip_alignment', {}).get('is_aligned', False)
                load_assess = align_info.get('load_alignment', {}).get('assessment', '')
                if zip_aligned and "Excellent" in load_assess:
                    print_info("综合评估", "完美对齐 (ZIP + LOAD)", "1;32")
                elif zip_aligned:
                    print_info("综合评估", "ZIP对齐良好", "0;32")
                else:
                    print_info("综合评估", "建议重新对齐", "1;33")
            
            # 优化信息部分
            if not args.compact:
                print_subheader("⚙️ 优化信息")
            if 'error' in opt_info:
                print_error(f"优化分析失败: {opt_info['error']}")
            else:
                opt_level = opt_info.get('optimization_level', 'unknown')
                has_debug = opt_info.get('has_debug_info', False)
                is_stripped = opt_info.get('is_stripped', False)
                
                if args.compact:
                    debug_str = "有调试" if has_debug else "无调试"
                    stripped_str = "已剥离" if is_stripped else "未剥离"
                    print_info("优化状态", f"{opt_level}, {debug_str}, {stripped_str}")
                else:
                    print_info("优化级别", opt_level)
                    print_info("包含调试信息", "是" if has_debug else "否")
                    print_info("已剥离符号", "是" if is_stripped else "否")
            
            # 哈希样式部分（新增）
            hash_info = results.get('hash_style', {})
            print_subheader("🔄 哈希样式 (Hash Style)")
            if 'error' in hash_info:
                print_error(f"哈希样式分析失败: {hash_info['error']}")
            else:
                hash_style = hash_info.get('hash_style', 'unknown')
                compatibility = hash_info.get('compatibility', 'unknown')
                description = hash_info.get('description', '')
                
                # 选择合适的颜色
                hash_color = "0;32"  # 默认绿色
                if hash_style == 'gnu':
                    hash_color = "1;32"  # 亮绿色（最优）
                elif hash_style == 'both':
                    hash_color = "1;33"  # 亮黄色（兼容但不是最优）
                elif hash_style == 'sysv':
                    hash_color = "1;31"  # 亮红色（不是最优）
                
                print_info("哈希样式", hash_style, hash_color)
                print_info("兼容性", f"Android API {compatibility}")
                print_info("描述", description)
                
                if not args.compact:
                    if 'recommendation' in hash_info:
                        print_info("建议", hash_info['recommendation'], "1;36")
                    if 'link_flag' in hash_info:
                        print_info("链接标志", hash_info['link_flag'], "0;36")
            
            # 重定位表压缩部分（新增）
            reloc_info = results.get('relocation_packing', {})
            print_subheader("📦 重定位表压缩 (Relocation Packing)")
            if 'error' in reloc_info:
                print_error(f"重定位表分析失败: {reloc_info['error']}")
            else:
                reloc_packing = reloc_info.get('relocation_packing', 'unknown')
                compatibility = reloc_info.get('compatibility', 'unknown')
                description = reloc_info.get('description', '')
                
                # 选择合适的颜色
                reloc_color = "0;32"  # 默认绿色
                if reloc_packing == 'android':
                    reloc_color = "1;32"  # 亮绿色（最优）
                elif reloc_packing == 'none':
                    reloc_color = "1;31"  # 亮红色（不是最优）
                
                print_info("重定位压缩", reloc_packing, reloc_color)
                print_info("兼容性", f"Android API {compatibility}")
                print_info("描述", description)
                
                # 显示重定位表大小（如果有）
                rel_size = reloc_info.get('rel_size', 0)
                relr_size = reloc_info.get('relr_size', 0)
                if rel_size or relr_size:
                    if rel_size > 0:
                        print_info("传统重定位表大小", format_size(rel_size))
                    if relr_size > 0:
                        print_info("压缩重定位表大小", format_size(relr_size))
                
                if not args.compact:
                    if 'recommendation' in reloc_info:
                        print_info("建议", reloc_info['recommendation'], "1;36")
                    if 'link_flag' in reloc_info:
                        print_info("链接标志", reloc_info['link_flag'], "0;36")
            
            # NDK版本分析部分（新增）
            ndk_info = results.get('ndk_version', {})
            print_subheader("🛠️ NDK版本分析")
            if 'error' in ndk_info:
                print_error(f"NDK版本分析失败: {ndk_info['error']}")
            else:
                ndk_version = ndk_info.get('ndk_version', 'unknown')
                ndk_certainty = ndk_info.get('ndk_version_certainty', 'unknown')
                clang_version = ndk_info.get('clang_version', 'unknown')
                clang_version_full = ndk_info.get('clang_version_full', '')
                detection_method = ndk_info.get('detection_method', '')
                
                # 选择合适的颜色
                certainty_color = "0;32"  # 默认绿色
                if ndk_certainty == 'high':
                    certainty_color = "1;32"  # 亮绿色（高可信度）
                elif ndk_certainty == 'medium':
                    certainty_color = "1;33"  # 亮黄色（中等可信度）
                elif ndk_certainty == 'low':
                    certainty_color = "1;31"  # 亮红色（低可信度）
                
                print_info("检测到的NDK版本", ndk_version, certainty_color)
                if ndk_certainty != 'unknown':
                    print_info("可信度", ndk_certainty, certainty_color)
                
                if clang_version != 'unknown':
                    print_info("Clang版本", clang_version)
                    if not args.compact and clang_version_full:
                        print_info("Clang详细信息", clang_version_full, "0;36")
                
                # 显示API级别
                if 'android_api_level' in ndk_info:
                    print_info("Android API级别", ndk_info['android_api_level'])
                
                # 推荐信息
                if 'recommended_ndk' in ndk_info:
                    recommended_ndk = ndk_info['recommended_ndk']
                    recommended_reason = ndk_info.get('recommended_reason', '')
                    
                    # 当前NDK是否为推荐版本
                    if ndk_version == recommended_ndk:
                        print_info("NDK版本状态", f"当前版本 ({recommended_ndk}) 已是推荐版本", "1;32")
                    else:
                        print_info("推荐NDK版本", recommended_ndk, "1;36")
                        if recommended_reason:
                            print_info("推荐原因", recommended_reason, "0;36")
                
                # 显示升级建议
                if 'upgrade_recommendation' in ndk_info:
                    print_info("升级建议", ndk_info['upgrade_recommendation'], "1;33")
                
                # 显示推断过程的更多信息（详细模式）
                if args.verbose:
                    # 显示推断过程的指标
                    indicators = ndk_info.get('ndk_indicators', [])
                    if indicators:
                        print_info("NDK版本检测指标", '')
                        for idx, indicator in enumerate(indicators, 1):
                            print(f"    {idx}. {indicator}")
                    
                    clang_indicators = ndk_info.get('clang_indicators', [])
                    if clang_indicators:
                        print_info("Clang版本检测指标", '')
                        for idx, indicator in enumerate(clang_indicators, 1):
                            print(f"    {idx}. {indicator}")
            
            # 提示信息
            if not args.compact:
                print("\n提示:")
                print(f"  使用 -o 参数保存完整JSON结果")
                print(f"  使用 --symbols all 查看所有符号详情")
                print(f"  使用 --filter-symbol-type T 只查看导出函数")
                print(f"  使用 --max-symbols 50 设置显示的符号数量")
                print(f"  使用 -c 使用紧凑输出模式")
                print(f"  使用 --no-color 禁用彩色输出")
                print(f"  使用 -v 显示更详细的分析信息")

if __name__ == "__main__":
    main()
