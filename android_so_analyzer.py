#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Android SO文件分析工具
用于全面分析Android SO库文件的各项信息，包括：
- 文件基本信息（大小、哈希值等）
- SO库架构信息
- 导出符号表
- 依赖的其他库
- 对齐方式
- ELF头信息
- 16KB页面对齐检查
- GNU Hash分析  
- 重定位表压缩分析
- NDK版本检测（通过Clang版本推断）
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

def format_size(size_bytes):
    """格式化文件大小显示"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"

def get_readelf_command():
    """获取readelf命令路径，优先使用NDK中的llvm-readelf"""
    # 优先使用NDK中的llvm-readelf
    ndk_root = os.environ.get('NDK_ROOT')
    if ndk_root:
        # 检测系统架构
        system = platform.system().lower()
        if system == 'darwin':
            arch = 'darwin-x86_64'
        elif system == 'linux':
            arch = 'linux-x86_64'
        elif system == 'windows':
            arch = 'windows-x86_64'
        else:
            arch = 'linux-x86_64'  # 默认
            
        ndk_readelf = os.path.join(ndk_root, 'toolchains', 'llvm', 'prebuilt', arch, 'bin', 'llvm-readelf')
        if os.path.exists(ndk_readelf):
            return ndk_readelf
    
    # 回退到系统readelf
    return 'readelf'

def parse_size(s):
    """支持十进制和十六进制"""
    try:
        return int(s.strip(), 0)
    except (ValueError, TypeError):
        return None

def check_enhanced_hash_style(file_path):
    """检查SO文件的哈希表样式（GNU Hash vs SysV Hash），显示详细的节大小信息"""
    try:
        readelf_cmd = get_readelf_command()
        result_sections = subprocess.run([readelf_cmd, '-S', file_path], capture_output=True, text=True)
        if result_sections.returncode != 0:
            return {'error': f'{readelf_cmd} -S failed: {result_sections.stderr}'}
        
        lines = result_sections.stdout.splitlines()
        hash_size = None
        gnu_hash_size = None
        
        # 解析节信息 - 适配llvm-readelf的表格格式
        for line in lines:
            line = line.strip()
            if not line or not line.startswith('['):
                continue
                
            # 解析表格行：[ 6] .gnu.hash         GNU_HASH        0000000000002068 002068 000224 00   A  3   0  8
            parts = line.split()
            if len(parts) >= 7:
                section_name = parts[2]  # 节名称在索引2
                try:
                    # Size 字段在第6个位置（0-indexed）
                    size_hex = parts[6]
                    size = int(size_hex, 16)
                    
                    if section_name == ".hash":
                        hash_size = size
                    elif section_name == ".gnu.hash":
                        gnu_hash_size = size
                except (ValueError, IndexError):
                    continue
        
        # 计算差值
        size_diff = None
        if hash_size is not None and gnu_hash_size is not None:
            size_diff = gnu_hash_size - hash_size
        
        # 确定哈希样式
        if gnu_hash_size is not None:
            style = 'gnu'
            description = f'使用GNU Hash，符号查找速度更快'
            compatibility = '需要Android 5.0+ (API 21+)'
            recommendation = '已使用推荐的GNU Hash格式'
        elif hash_size is not None:
            style = 'sysv'
            description = f'使用传统SysV Hash，兼容性好但查找较慢'
            compatibility = '兼容所有Android版本'
            recommendation = '建议使用GNU Hash：-Wl,--hash-style=gnu'
        else:
            style = 'none'
            description = '未检测到哈希表'
            compatibility = '未知'
            recommendation = '确认文件是否为有效的动态链接库'
        
        # 生成验证命令
        verify_command = f"{readelf_cmd} -S {os.path.basename(file_path)} | grep hash"
        
        return {
            'hash_style': style,
            'hash_size': hash_size,
            'gnu_hash_size': gnu_hash_size,
            'size_diff': size_diff,
            'has_gnu_hash': gnu_hash_size is not None,
            'has_sysv_hash': hash_size is not None,
            'description': description,
            'compatibility': compatibility,
            'recommendation': recommendation,
            'verify_command': verify_command
        }
    except Exception as e:
        return {'error': f'Error checking hash style: {str(e)}'}

def check_enhanced_relocation_packing(file_path):
    """检查重定位表压缩状态，显示详细的节大小和条目数信息"""
    try:
        readelf_cmd = get_readelf_command()
        result = subprocess.run([readelf_cmd, '-S', file_path], capture_output=True, text=True)
        if result.returncode != 0:
            return {'error': f'{readelf_cmd} failed: {result.stderr}'}
        
        lines = result.stdout.splitlines()
        relocation_sections = []
        
        # 解析节信息 - 适配llvm-readelf的表格格式
        for line in lines:
            line = line.strip()
            if not line or not line.startswith('['):
                continue
                
            # 解析表格行：[ 9] .rela.dyn         RELA            0000000000005798 005798 0a2e40 18   A  3   0  8
            parts = line.split()
            if len(parts) >= 8:
                section_name = parts[2]  # 节名称在索引2
                section_type = parts[3]  # 节类型在索引3
                if ('rel' in section_name.lower() or 'android' in section_name.lower()):
                    try:
                        # Size 字段在第6个位置，EntrySize 在第7个位置
                        size_hex = parts[6]
                        entry_size_hex = parts[7]
                        
                        size = int(size_hex, 16)
                        entry_size = int(entry_size_hex, 16)
                        
                        if size > 0 and entry_size > 0:
                            count = size // entry_size
                            relocation_sections.append({
                                'name': section_name,
                                'type': section_type,
                                'size': size,
                                'entry_size': entry_size,
                                'count': count
                            })
                    except (ValueError, IndexError):
                        continue
        
        # 分析重定位表类型 - 更新识别逻辑，检查节类型而不只是节名称
        has_relr = any('.relr.dyn' in sec['name'] for sec in relocation_sections)
        has_android_rel = any('android.rel' in sec['name'] or 'ANDROID_REL' in sec.get('type', '') for sec in relocation_sections)
        has_traditional_rel = any(sec['name'] in ['.rel.dyn', '.rel.plt', '.rela.dyn', '.rela.plt'] and 
                                'ANDROID_REL' not in sec.get('type', '') for sec in relocation_sections)
        
        # 计算总体积和条目数
        total_size = sum(sec['size'] for sec in relocation_sections)
        total_count = sum(sec['count'] for sec in relocation_sections)
        
        # 确定压缩状态
        if has_relr or has_android_rel:
            packing_status = 'android'
            description = f'使用Android重定位表压缩，总大小: {total_size} bytes, 条目数: {total_count}'
            compatibility = '需要Android 6.0+ (API 23+)'
            recommendation = '已启用压缩，优化效果良好'
            link_flag = '-Wl,--pack-dyn-relocs=android'
        elif has_traditional_rel:
            packing_status = 'none'
            description = f'使用传统重定位表，总大小: {total_size} bytes, 条目数: {total_count}'
            compatibility = '兼容所有Android版本'
            recommendation = '可启用重定位压缩减小文件大小'
            link_flag = '建议添加 -Wl,--pack-dyn-relocs=android'
        else:
            packing_status = 'no_relocations'
            description = '未检测到动态重定位表'
            compatibility = '所有Android版本'
            recommendation = '无需配置重定位压缩'
            link_flag = 'N/A'
        
        # 生成验证命令
        verify_command = f"{readelf_cmd} -S {os.path.basename(file_path)} | grep rel"
        
        return {
            'relocation_packing': packing_status,
            'relocation_sections': relocation_sections,
            'total_size': total_size,
            'total_count': total_count,
            'has_relr': has_relr,
            'has_android_rel': has_android_rel,
            'has_traditional_rel': has_traditional_rel,
            'description': description,
            'compatibility': compatibility,
            'recommendation': recommendation,
            'link_flag': link_flag,
            'verify_command': verify_command
        }
    except Exception as e:
        return {'error': f'Error checking relocation packing: {str(e)}'}

def check_16kb_alignment(file_path):
    """检查SO文件是否支持16KB页面对齐
    
    Android 15 (API 35) 引入了16KB页面支持，需要SO文件满足：
    1. 所有可加载段的虚拟地址必须16KB对齐
    2. 文件偏移量必须16KB对齐
    3. 段对齐属性必须是16KB（2^14）
    """
    try:
        # 使用NDK的llvm-objdump获取程序头信息（更准确的对齐信息）
        ndk_root = os.environ.get('NDK_ROOT')
        objdump_cmd = 'objdump'
        
        if ndk_root:
            # 检测系统架构
            system = platform.system().lower()
            if system == 'darwin':
                arch = 'darwin-x86_64'
            elif system == 'linux':
                arch = 'linux-x86_64'
            elif system == 'windows':
                arch = 'windows-x86_64'
            else:
                arch = 'linux-x86_64'  # 默认
                
            ndk_objdump = os.path.join(ndk_root, 'toolchains', 'llvm', 'prebuilt', arch, 'bin', 'llvm-objdump')
            if os.path.exists(ndk_objdump):
                objdump_cmd = ndk_objdump
        
        result = subprocess.run([objdump_cmd, '-p', file_path], capture_output=True, text=True)
        if result.returncode != 0:
            return {'error': f'{objdump_cmd} failed: {result.stderr}'}
        
        lines = result.stdout.split('\n')
        segments = []
        
        # 解析LOAD段，objdump格式：LOAD off 0x0000000000000000 vaddr 0x0000000000000000 paddr 0x0000000000000000 align 2**14
        for line in lines:
            if 'LOAD' in line and 'off' in line and 'vaddr' in line:
                try:
                    # 提取 off, vaddr, align 信息
                    off_match = re.search(r'off\s+0x([0-9a-fA-F]+)', line)
                    vaddr_match = re.search(r'vaddr\s+0x([0-9a-fA-F]+)', line)
                    align_match = re.search(r'align\s+2\*\*(\d+)', line)
                    
                    if off_match and vaddr_match and align_match:
                        offset = int(off_match.group(1), 16)
                        vaddr = int(vaddr_match.group(1), 16)
                        align_power = int(align_match.group(1))
                        alignment = 2 ** align_power
                        
                        segments.append({
                            'offset': offset,
                            'vaddr': vaddr,
                            'alignment': alignment,
                            'offset_16kb_aligned': (offset % 16384) == 0,
                            'vaddr_16kb_aligned': (vaddr % 16384) == 0,
                            'alignment_16kb': alignment >= 16384,
                            'align_power': align_power
                        })
                except (ValueError, AttributeError):
                    continue
        
        # 检查对齐情况
        all_offset_aligned = all(seg['offset_16kb_aligned'] for seg in segments)
        all_vaddr_aligned = all(seg['vaddr_16kb_aligned'] for seg in segments)
        all_alignment_ok = all(seg['alignment_16kb'] for seg in segments)
        
        # 综合判断：段对齐属性是16KB就认为支持16KB页面
        supports_16kb = all_alignment_ok
        
        return {
            'supports_16kb': supports_16kb,
            'total_segments': len(segments),
            'offset_aligned_count': sum(1 for seg in segments if seg['offset_16kb_aligned']),
            'vaddr_aligned_count': sum(1 for seg in segments if seg['vaddr_16kb_aligned']),
            'alignment_ok_count': sum(1 for seg in segments if seg['alignment_16kb']),
            'segments': segments,
            'recommendation': '支持16KB页面，兼容Android 15+' if supports_16kb 
                           else '不支持16KB页面，需要使用-Wl,-z,max-page-size=16384重新链接',
            'objdump_command': objdump_cmd
        }
    except Exception as e:
        return {'error': f'Error checking 16KB alignment: {str(e)}'}

def analyze_clang_ndk_version(file_path):
    """分析SO文件中的Clang版本信息并推断NDK版本"""
    # NDK版本与Clang版本的映射关系
    NDK_CLANG_MAPPING = {
        "r27": "18.1.8",
        "r26": "17.0.6",
        "r25": "14.0.7",
        "r24": "14.0.6",
        "r23": "12.0.8",
        "r22": "11.0.5",
        "r21": "9.0.9",
        "r20": "8.0.7",
    }
    
    try:
        # 使用strings提取SO文件中的字符串
        result = subprocess.run(['strings', file_path], capture_output=True, text=True)
        if result.returncode != 0:
            return {'error': f'strings command failed: {result.stderr}'}
        
        content = result.stdout
        
        # 查找Clang版本
        clang_version = None
        clang_version_full = None
        
        # 查找clang版本模式
        clang_patterns = [
            r'clang version ([0-9]+\.[0-9]+\.[0-9]+)',
            r'Clang ([0-9]+\.[0-9]+\.[0-9]+)'
        ]
        
        for pattern in clang_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                clang_version = matches[0]
                # 查找完整版本行
                for line in content.splitlines():
                    if clang_version in line and ('clang' in line.lower()):
                        clang_version_full = line.strip()
                        break
                break
        
        # 推断NDK版本
        ndk_version = 'unknown'
        certainty = 'unknown'
        
        if clang_version:
            # 寻找最匹配的NDK版本
            for ndk, clang_ref in NDK_CLANG_MAPPING.items():
                if clang_version.startswith(clang_ref.rsplit('.', 1)[0]):  # 比较主要版本
                    ndk_version = ndk
                    if clang_version == clang_ref:
                        certainty = 'high'
                    else:
                        certainty = 'medium'
                    break
        
        # 查找直接的NDK标识
        ndk_patterns = [
            r'Android NDK ([a-z][0-9]+[a-z]?)',
            r'NDK ([a-z][0-9]+[a-z]?)'
        ]
        
        for pattern in ndk_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                ndk_version = matches[0]
                certainty = 'high'
                break
        
        return {
            'clang_version': clang_version or 'unknown',
            'clang_version_full': clang_version_full or 'unknown',
            'ndk_version': ndk_version,
            'ndk_certainty': certainty,
            'detection_method': 'strings_analysis',
            'recommendation': f'检测到NDK {ndk_version}，建议使用最新的NDK r27' if ndk_version != 'unknown' else '无法确定NDK版本'
        }
    except Exception as e:
        return {'error': f'Error analyzing Clang/NDK version: {str(e)}'}

def parse_size(s):
    """支持十进制和十六进制"""
    try:
        return int(s.strip(), 0)
    except (ValueError, TypeError):
        return None

def check_hash_style(file_path):
    """检查SO文件的哈希表样式（GNU Hash vs SysV Hash），显示详细的节大小信息"""
    try:
        # 使用NDK的llvm-readelf检查节信息，获取详细的大小数据
        readelf_cmd = get_readelf_command()
        result_sections = subprocess.run([readelf_cmd, '-S', file_path], capture_output=True, text=True)
        if result_sections.returncode != 0:
            return {'error': f'{readelf_cmd} -S failed: {result_sections.stderr}'}
        
        lines = result_sections.stdout.splitlines()
        hash_size = None
        gnu_hash_size = None
        
        # 解析节信息 - 适配llvm-readelf的表格格式
        for line in lines:
            line = line.strip()
            if not line or not line.startswith('['):
                continue
                
            # 解析表格行：[ 6] .gnu.hash         GNU_HASH        0000000000002068 002068 000224 00   A  3   0  8
            parts = line.split()
            if len(parts) >= 7:
                section_name = parts[2]  # 节名称在索引2
                try:
                    # Size 字段在第6个位置（0-indexed）
                    size_hex = parts[6]
                    size = int(size_hex, 16)
                    
                    if section_name == ".hash":
                        hash_size = size
                    elif section_name == ".gnu.hash":
                        gnu_hash_size = size
                except (ValueError, IndexError):
                    continue
        
        # 计算差值
        size_diff = None
        if hash_size is not None and gnu_hash_size is not None:
            size_diff = gnu_hash_size - hash_size
        
        # 确定哈希样式
        if gnu_hash_size is not None:
            style = 'gnu'
            description = f'使用GNU Hash，符号查找速度更快'
            compatibility = '需要Android 5.0+ (API 21+)'
            recommendation = '已使用推荐的GNU Hash格式'
        elif hash_size is not None:
            style = 'sysv'
            description = f'使用传统SysV Hash，兼容性好但查找较慢'
            compatibility = '兼容所有Android版本'
            recommendation = '建议使用GNU Hash：-Wl,--hash-style=gnu'
        else:
            style = 'none'
            description = '未检测到哈希表'
            compatibility = '未知'
            recommendation = '确认文件是否为有效的动态链接库'
        
        # 生成验证命令
        readelf_cmd = get_readelf_command()
        verify_command = f"{readelf_cmd} -S {os.path.basename(file_path)} | grep hash"
        
        return {
            'hash_style': style,
            'hash_size': hash_size,
            'gnu_hash_size': gnu_hash_size,
            'size_diff': size_diff,
            'has_gnu_hash': gnu_hash_size is not None,
            'has_sysv_hash': hash_size is not None,
            'description': description,
            'compatibility': compatibility,
            'recommendation': recommendation,
            'verify_command': verify_command
        }
    except Exception as e:
        return {'error': f'Error checking hash style: {str(e)}'}

def check_relocation_packing(file_path):
    """检查重定位表压缩状态，显示详细的节大小和条目数信息"""
    try:
        # 使用NDK的llvm-readelf获取节信息
        readelf_cmd = get_readelf_command()
        result = subprocess.run([readelf_cmd, '-S', file_path], capture_output=True, text=True)
        if result.returncode != 0:
            return {'error': f'{readelf_cmd} failed: {result.stderr}'}
        
        lines = result.stdout.splitlines()
        relocation_sections = []
        
        # 解析节信息 - 适配llvm-readelf的表格格式
        for line in lines:
            line = line.strip()
            if not line or not line.startswith('['):
                continue
                
            # 解析表格行：[ 9] .rela.dyn         RELA            0000000000005798 005798 0a2e40 18   A  3   0  8
            parts = line.split()
            if len(parts) >= 8:
                section_name = parts[2]  # 节名称在索引2
                if ('rel' in section_name.lower() or 'android' in section_name.lower()):
                    try:
                        # Size 字段在第6个位置，EntrySize 在第7个位置
                        size_hex = parts[6]
                        entry_size_hex = parts[7]
                        
                        size = int(size_hex, 16)
                        entry_size = int(entry_size_hex, 16)
                        
                        if size > 0 and entry_size > 0:
                            count = size // entry_size
                            relocation_sections.append({
                                'name': section_name,
                                'size': size,
                                'entry_size': entry_size,
                                'count': count
                            })
                    except (ValueError, IndexError):
                        continue
        
        # 分析重定位表类型
        has_relr = any('.relr.dyn' in sec['name'] for sec in relocation_sections)
        has_android_rel = any('android.rel' in sec['name'] for sec in relocation_sections)
        has_traditional_rel = any(sec['name'] in ['.rel.dyn', '.rel.plt', '.rela.dyn', '.rela.plt'] for sec in relocation_sections)
        
        # 计算总体积和条目数
        total_size = sum(sec['size'] for sec in relocation_sections)
        total_count = sum(sec['count'] for sec in relocation_sections)
        
        # 确定压缩状态
        if has_relr or has_android_rel:
            packing_status = 'android'
            description = f'使用Android重定位表压缩，总大小: {total_size} bytes, 条目数: {total_count}'
            compatibility = '需要Android 6.0+ (API 23+)'
            recommendation = '已启用压缩，优化效果良好'
            link_flag = '-Wl,--pack-dyn-relocs=android'
        elif has_traditional_rel:
            packing_status = 'none'
            description = f'使用传统重定位表，总大小: {total_size} bytes, 条目数: {total_count}'
            compatibility = '兼容所有Android版本'
            recommendation = '可启用重定位压缩减小文件大小'
            link_flag = '建议添加 -Wl,--pack-dyn-relocs=android'
        else:
            packing_status = 'no_relocations'
            description = '未检测到动态重定位表'
            compatibility = '所有Android版本'
            recommendation = '无需配置重定位压缩'
            link_flag = 'N/A'
        
        # 生成验证命令
        readelf_cmd = get_readelf_command()
        verify_command = f"{readelf_cmd} -S {os.path.basename(file_path)} | grep rel"
        
        return {
            'relocation_packing': packing_status,
            'relocation_sections': relocation_sections,
            'total_size': total_size,
            'total_count': total_count,
            'has_relr': has_relr,
            'has_android_rel': has_android_rel,
            'has_traditional_rel': has_traditional_rel,
            'description': description,
            'compatibility': compatibility,
            'recommendation': recommendation,
            'link_flag': link_flag,
            'verify_command': verify_command
        }
    except Exception as e:
        return {'error': f'Error checking relocation packing: {str(e)}'}

def analyze_clang_ndk_version(file_path):
    """分析SO文件中的Clang版本信息并推断NDK版本"""
    # NDK版本与Clang版本的映射关系
    NDK_CLANG_MAPPING = {
        "r27": "18.1.8",
        "r26": "17.0.6",
        "r25": "14.0.7",
        "r24": "14.0.6",
        "r23": "12.0.8",
        "r22": "11.0.5",
        "r21": "9.0.9",
        "r20": "8.0.7",
    }
    
    try:
        # 使用strings提取SO文件中的字符串
        result = subprocess.run(['strings', file_path], capture_output=True, text=True)
        if result.returncode != 0:
            return {'error': f'strings command failed: {result.stderr}'}
        
        content = result.stdout
        
        # 查找Clang版本
        clang_version = None
        clang_version_full = None
        
        # 查找clang版本模式
        clang_patterns = [
            r'clang version ([0-9]+\.[0-9]+\.[0-9]+)',
            r'Clang ([0-9]+\.[0-9]+\.[0-9]+)'
        ]
        
        for pattern in clang_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                clang_version = matches[0]
                # 查找完整版本行
                for line in content.splitlines():
                    if clang_version in line and ('clang' in line.lower()):
                        clang_version_full = line.strip()
                        break
                break
        
        # 推断NDK版本
        ndk_version = 'unknown'
        certainty = 'unknown'
        
        if clang_version:
            # 寻找最匹配的NDK版本
            for ndk, clang_ref in NDK_CLANG_MAPPING.items():
                if clang_version.startswith(clang_ref.rsplit('.', 1)[0]):  # 比较主要版本
                    ndk_version = ndk
                    if clang_version == clang_ref:
                        certainty = 'high'
                    else:
                        certainty = 'medium'
                    break
        
        # 查找直接的NDK标识
        ndk_patterns = [
            r'Android NDK ([a-z][0-9]+[a-z]?)',
            r'NDK ([a-z][0-9]+[a-z]?)'
        ]
        
        for pattern in ndk_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                ndk_version = matches[0]
                certainty = 'high'
                break
        
        return {
            'clang_version': clang_version or 'unknown',
            'clang_version_full': clang_version_full or 'unknown',
            'ndk_version': ndk_version,
            'ndk_certainty': certainty,
            'detection_method': 'strings_analysis',
            'recommendation': f'检测到NDK {ndk_version}，建议使用最新的NDK r27' if ndk_version != 'unknown' else '无法确定NDK版本'
        }
    except Exception as e:
        return {'error': f'Error analyzing Clang/NDK version: {str(e)}'}

def analyze_so_file(file_path):
    """全面分析SO文件，包含增强的哈希表和重定位表分析"""
    if not os.path.exists(file_path):
        print_error(f'文件不存在: {file_path}')
        return {'error': f'文件不存在: {file_path}'}
    
    print_header(f"Android SO文件分析报告")
    print_info("文件路径", file_path)
    print_info("分析时间", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    # 使用的工具信息
    readelf_cmd = get_readelf_command()
    print_info("使用工具", readelf_cmd, "0;36")
    
    # 基础信息
    file_size = os.path.getsize(file_path)
    print_info("文件大小", f"{file_size:,} 字节 ({format_size(file_size)})", "0;32")
    
    # 1. 16KB页面对齐检查
    print_subheader("16KB页面对齐检查")
    alignment_result = check_16kb_alignment(file_path)
    if 'error' in alignment_result:
        print_error(f"分析失败: {alignment_result['error']}")
    else:
        supports_16kb = alignment_result['supports_16kb']
        if supports_16kb:
            print_success(f"支持16KB页面对齐 (Android 15+兼容)")
        else:
            print_warning(f"不支持16KB页面对齐")
        
        print_info("总段数", str(alignment_result['total_segments']))
        print_info("偏移对齐段数", f"{alignment_result['offset_aligned_count']}/{alignment_result['total_segments']}")
        print_info("虚拟地址对齐段数", f"{alignment_result['vaddr_aligned_count']}/{alignment_result['total_segments']}")
        print_info("对齐属性16KB段数", f"{alignment_result['alignment_ok_count']}/{alignment_result['total_segments']}")
        print_info("使用工具", alignment_result.get('objdump_command', 'objdump'), "0;36")
        
        # 显示段详情
        if alignment_result['segments']:
            print("\n  " + colorize("LOAD段详情:", "1;37"))
            headers = ["段号", "文件偏移", "虚拟地址", "对齐属性", "16KB对齐"]
            rows = []
            for i, seg in enumerate(alignment_result['segments'], 1):
                offset_aligned = "✅" if seg['offset_16kb_aligned'] else "❌"
                vaddr_aligned = "✅" if seg['vaddr_16kb_aligned'] else "❌"
                alignment_ok = "✅" if seg['alignment_16kb'] else "❌"
                overall_ok = "✅" if seg['alignment_16kb'] else "❌"  # 主要看对齐属性
                
                rows.append([
                    str(i),
                    f"0x{seg['offset']:08x} {offset_aligned}",
                    f"0x{seg['vaddr']:08x} {vaddr_aligned}",
                    f"2^{seg['align_power']} ({seg['alignment']}) {alignment_ok}",
                    overall_ok
                ])
            print_table(headers, rows)
        
        print_info("建议", alignment_result['recommendation'], "1;33")
    
    # 2. 哈希样式分析
    print_subheader("哈希表样式分析")
    hash_result = check_enhanced_hash_style(file_path)
    if 'error' in hash_result:
        print_error(f"分析失败: {hash_result['error']}")
    else:
        hash_style = hash_result['hash_style'].upper()
        if hash_style == 'GNU':
            print_success(f"使用GNU Hash格式 (推荐)")
        elif hash_style == 'SYSV':
            print_warning(f"使用传统SysV Hash格式")
        else:
            print_error(f"未检测到哈希表")
        
        # 显示详细大小信息
        if hash_result['hash_size'] is not None:
            print_info(".hash 大小", f"{hash_result['hash_size']} bytes")
        if hash_result['gnu_hash_size'] is not None:
            print_info(".gnu.hash 大小", f"{hash_result['gnu_hash_size']} bytes")
        if hash_result['size_diff'] is not None:
            diff_str = f"{hash_result['size_diff']:+d}" if hash_result['size_diff'] != 0 else "0"
            print_info("大小差值", f"{diff_str} bytes", "0;36")
        
        print_info("兼容性", hash_result['compatibility'])
        print_info("建议", hash_result['recommendation'], "1;33")
        print_info("验证命令", hash_result['verify_command'], "0;35")
    
    # 3. 重定位表压缩分析
    print_subheader("重定位表压缩分析")
    reloc_result = check_enhanced_relocation_packing(file_path)
    if 'error' in reloc_result:
        print_error(f"分析失败: {reloc_result['error']}")
    else:
        packing_status = reloc_result['relocation_packing']
        if packing_status == 'android':
            print_success(f"已启用Android重定位表压缩")
        elif packing_status == 'none':
            print_warning(f"使用传统重定位表格式")
        else:
            print_info("状态", "未检测到重定位表")
        
        # 显示重定位表节详情
        if reloc_result['relocation_sections']:
            print("\n  " + colorize("检测到的重定位表节:", "1;37"))
            headers = ["节名称", "节类型", "大小", "条目大小", "条目数"]
            rows = []
            for sec in reloc_result['relocation_sections']:
                rows.append([
                    sec['name'],
                    sec.get('type', 'UNKNOWN'),
                    f"{sec['size']} bytes",
                    f"{sec['entry_size']} bytes",
                    str(sec['count'])
                ])
            print_table(headers, rows)
            
            print_info("总计大小", f"{reloc_result['total_size']} bytes ({format_size(reloc_result['total_size'])})")
            print_info("总条目数", str(reloc_result['total_count']))
        
        print_info("兼容性", reloc_result['compatibility'])
        print_info("建议", reloc_result['recommendation'], "1;33")
        if reloc_result['link_flag'] != 'N/A':
            print_info("链接标志", reloc_result['link_flag'], "0;35")
        print_info("验证命令", reloc_result['verify_command'], "0;35")
    
    # 4. NDK版本分析
    print_subheader("NDK版本分析")
    ndk_result = analyze_clang_ndk_version(file_path)
    if 'error' in ndk_result:
        print_error(f"分析失败: {ndk_result['error']}")
    else:
        if ndk_result['clang_version'] != 'unknown':
            print_info("Clang版本", ndk_result['clang_version'])
            if ndk_result['clang_version_full'] != 'unknown':
                print_info("完整版本", ndk_result['clang_version_full'], "0;37")
        
        if ndk_result['ndk_version'] != 'unknown':
            print_info("NDK版本", ndk_result['ndk_version'])
            certainty_color = "0;32" if ndk_result['ndk_certainty'] == 'high' else "1;33"
            print_info("可信度", ndk_result['ndk_certainty'], certainty_color)
        else:
            print_warning("无法确定NDK版本")
        
        print_info("建议", ndk_result['recommendation'], "1;33")
    
    # 总结和建议
    print_header("分析总结")
    
    issues = []
    recommendations = []
    
    # 收集问题和建议
    if not alignment_result.get('error') and not alignment_result.get('supports_16kb'):
        issues.append("不支持16KB页面对齐")
        recommendations.append("添加链接参数: -Wl,-z,max-page-size=16384")
    
    if not hash_result.get('error') and hash_result.get('hash_style') == 'sysv':
        issues.append("使用传统SysV Hash")
        recommendations.append("启用GNU Hash: -Wl,--hash-style=gnu")
    
    if not reloc_result.get('error') and reloc_result.get('relocation_packing') == 'none':
        issues.append("未启用重定位表压缩")
        recommendations.append("启用重定位压缩: -Wl,--pack-dyn-relocs=android")
    
    if issues:
        print_subheader("发现的问题")
        for i, issue in enumerate(issues, 1):
            print(f"  {colorize(f'{i}.', '1;31')} {issue}")
        
        print_subheader("推荐的修复方案")
        for i, rec in enumerate(recommendations, 1):
            print(f"  {colorize(f'{i}.', '1;32')} {rec}")
    else:
        print_success("所有检查项目都已优化！文件已经过良好的优化配置。")
    
    # 验证命令
    print_subheader("验证命令 (可直接复制运行)")
    verification_commands = []
    
    if not hash_result.get('error'):
        verification_commands.append(f"# 确认哈希表类型\n{hash_result.get('verify_command')}")
    
    if not reloc_result.get('error'):
        verification_commands.append(f"# 确认重定位表压缩\n{reloc_result.get('verify_command')}")
    
    if verification_commands:
        for cmd in verification_commands:
            print(f"  {colorize(cmd, '0;35')}")
        print_info("提示", "将命令中的文件名替换为实际的SO文件路径", "1;37")
    
    return {
        '16kb_alignment': alignment_result,
        'hash_style': hash_result,
        'relocation_packing': reloc_result,
        'ndk_version': ndk_result
    }

def main():
    """主函数"""
    import sys
    
    if len(sys.argv) != 2:
        print("用法: python android_so_analyzer.py <SO文件路径>")
        print("\n示例:")
        print("  python android_so_analyzer.py /path/to/library.so")
        sys.exit(1)
    
    so_file = sys.argv[1]
    
    try:
        result = analyze_so_file(so_file)
        if 'error' in result:
            print_error(f"分析失败: {result['error']}")
            sys.exit(1)
    except KeyboardInterrupt:
        print(colorize("\n\n分析被用户中断", "1;33"))
        sys.exit(0)
    except Exception as e:
        print_error(f"分析过程中发生错误: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()