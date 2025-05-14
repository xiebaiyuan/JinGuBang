#!/usr/bin/env python3
# filepath: /Users/xiebaiyuan/tools/parseminecrash.py

import re
import subprocess
import argparse
import os
from typing import List, Dict, Tuple, Optional
import sys
import tempfile


# ANSI 颜色代码
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class CrashInfo:
    def __init__(self):
        self.abi = ""
        self.timestamp = ""
        self.app_version = ""
        self.process_info = ""
        self.signal_info = ""
        self.registers = []
        self.backtrace = []


def parse_crash_log(log_content: str) -> CrashInfo:
    """解析崩溃日志内容"""
    crash_info = CrashInfo()
    
    # 解析基本信息
    abi_match = re.search(r"ABI: '([^']+)'", log_content)
    if abi_match:
        crash_info.abi = abi_match.group(1)
    
    timestamp_match = re.search(r"Timestamp: ([^\n]+)", log_content)
    if timestamp_match:
        crash_info.timestamp = timestamp_match.group(1)
    
    app_version_match = re.search(r"AppVersion: ([^\n]+)", log_content)
    if app_version_match:
        crash_info.app_version = app_version_match.group(1)
    
    process_match = re.search(r"pid: (\d+), tid: (\d+), name: ([^\n]+)", log_content)
    if process_match:
        crash_info.process_info = process_match.group(0)
    
    signal_match = re.search(r"signal \d+ \([^)]+\), code \d+ \([^)]+\), fault addr [^\n]+", log_content)
    if signal_match:
        crash_info.signal_info = signal_match.group(0)
    
    # 解析寄存器信息
    register_pattern = r"x\d+\s+[0-9a-fA-F]+"
    crash_info.registers = re.findall(register_pattern, log_content)
    
    # 解析堆栈回溯
    backtrace_pattern = r"#(\d+)\s+pc\s+([0-9a-fA-F]+)\s+([^\n]+)"
    crash_info.backtrace = re.findall(backtrace_pattern, log_content)
    
    return crash_info


def parse_library_path(lib_path: str) -> str:
    """规范化库的路径"""
    return os.path.abspath(os.path.expanduser(lib_path))


def extract_lib_info(backtrace_item: str) -> Tuple[str, str, str, Optional[str]]:
    """从堆栈回溯项中提取库信息"""
    # 格式: #00 pc 0000000000591e28 /path/to/lib.so (可能有附加信息) (BuildId: xxx)
    parts = backtrace_item.strip().split()
    frame_num = parts[0]
    pc_offset = parts[2]
    
    # 提取库路径
    lib_path_match = re.search(r"(/[^ ]+\.so)", backtrace_item)
    lib_path = lib_path_match.group(1) if lib_path_match else ""
    
    # 提取函数名 (如果有)
    function_match = re.search(r"\((.*?)\)", backtrace_item)
    function = function_match.group(1) if function_match and not function_match.group(1).startswith("BuildId") else None
    
    # 从路径中提取库名
    lib_name = os.path.basename(lib_path) if lib_path else "unknown"
    
    return frame_num, pc_offset, lib_name, function


def addr2line(addr2line_path: str, lib_path: str, offset: str) -> List[str]:
    """使用addr2line工具解析地址"""
    if not os.path.exists(lib_path):
        return [f"Unable to locate library: {lib_path}"]
    
    try:
        cmd = [addr2line_path, "-e", lib_path, "-f", "-C", "-p", offset]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout.strip().split('\n')
    except subprocess.CalledProcessError as e:
        return [f"addr2line failed: {e.stderr}"]
    except Exception as e:
        return [f"Error: {str(e)}"]


def is_target_lib(lib_name: str, target_lib: str) -> bool:
    """检查是否是目标库"""
    if not target_lib:
        return False
    return os.path.basename(lib_name) == os.path.basename(target_lib)


def print_crash_info(crash_info: CrashInfo, target_lib: str, lib_path: str, addr2line_path: str):
    """打印格式化的崩溃信息"""
    print(f"{Colors.HEADER}{Colors.BOLD}崩溃信息摘要:{Colors.ENDC}")
    print(f"{Colors.BLUE}ABI:{Colors.ENDC} {crash_info.abi}")
    print(f"{Colors.BLUE}Timestamp:{Colors.ENDC} {crash_info.timestamp}")
    print(f"{Colors.BLUE}AppVersion:{Colors.ENDC} {crash_info.app_version}")
    print(f"{Colors.BLUE}Process Info:{Colors.ENDC} {crash_info.process_info}")
    print(f"{Colors.RED}{crash_info.signal_info}{Colors.ENDC}")
    
    print(f"\n{Colors.HEADER}{Colors.BOLD}寄存器状态:{Colors.ENDC}")
    for i, reg in enumerate(crash_info.registers):
        if i % 4 == 0 and i > 0:
            print()
        print(f"{Colors.CYAN}{reg}{Colors.ENDC}", end="  ")
    print("\n")
    
    print(f"{Colors.HEADER}{Colors.BOLD}堆栈回溯:{Colors.ENDC}")
    for item in crash_info.backtrace:
        frame_num, pc_offset, lib_name, function = extract_lib_info(item[2])
        
        # 如果是目标库，解析地址
        if is_target_lib(lib_name, target_lib) and lib_path:
            print(f"{Colors.GREEN}#{item[0]} {Colors.YELLOW}pc {item[1]} {Colors.CYAN}{lib_name}{Colors.ENDC}")
            
            symbol_info = addr2line(addr2line_path, lib_path, item[1])
            for line in symbol_info:
                print(f"    {Colors.BOLD}{Colors.BLUE}↪ {line}{Colors.ENDC}")
            
            if function:
                print(f"    {Colors.YELLOW}Function: {function}{Colors.ENDC}")
        else:
            function_info = f" ({function})" if function else ""
            print(f"{Colors.GREEN}#{item[0]} {Colors.YELLOW}pc {item[1]} {Colors.CYAN}{lib_name}{Colors.YELLOW}{function_info}{Colors.ENDC}")


def main():
    parser = argparse.ArgumentParser(description='解析Android崩溃堆栈')
    parser.add_argument('-i', '--input', help='崩溃日志文件路径 (默认从标准输入读取)')
    parser.add_argument('-l', '--library', help='符号库路径', default='')
    parser.add_argument('-a', '--addr2line', 
                       help='addr2line工具路径',
                       default='/android-ndk-r25b/toolchains/llvm/prebuilt/darwin-x86_64/bin/llvm-addr2line')
    parser.add_argument('-t', '--target', help='要解析的目标库名称', default='libmml_framework.so')
    
    args = parser.parse_args()
    
    # 读取崩溃日志
    if args.input:
        try:
            with open(args.input, 'r') as f:
                crash_content = f.read()
        except Exception as e:
            print(f"无法读取文件 {args.input}: {str(e)}")
            return
    else:
        # 从标准输入读取或显示帮助
        if sys.stdin.isatty():
            parser.print_help()
            print("\n请通过管道或--input参数提供崩溃日志。")
            return
        crash_content = sys.stdin.read()
    
    # 解析崩溃日志
    crash_info = parse_crash_log(crash_content)
    
    # 处理符号库路径
    lib_path = parse_library_path(args.library) if args.library else ""
    
    # 处理addr2line路径
    addr2line_path = parse_library_path(args.addr2line)
    
    # 打印解析结果
    print_crash_info(crash_info, args.target, lib_path, addr2line_path)


if __name__ == '__main__':
    main()