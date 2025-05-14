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
    abi_match = re.search(r"ABI: '?([^'\n]+)'?", log_content)
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
    
    # 解析堆栈回溯 - 支持多种格式
    # 首先尝试标准格式
    backtrace_section = re.search(r"backtrace:(.+?)(?:\n\n|\Z)", log_content, re.DOTALL)
    if backtrace_section:
        backtrace_text = backtrace_section.group(1).strip()
        # 尝试匹配详细格式: #00 pc 00000000 /path/to/lib.so (function+offset)
        standard_pattern = r"#(\d+)\s+pc\s+([0-9a-fA-F]+)\s+([^\n]+)"
        backtrace = re.findall(standard_pattern, backtrace_text)
        
        # 如果没有匹配到标准格式，尝试简化格式: #00 pc 00000000 lib.so (function)
        if not backtrace:
            simple_pattern = r"#(\d+)\s+pc\s+([0-9a-fA-F]+)\s+([^\s\n]+)(?:\s+\(([^)]+)\))?"
            backtrace_matches = re.findall(simple_pattern, backtrace_text)
            # 转换简化格式匹配结果为标准格式
            backtrace = [(frame, offset, lib + (f" ({func})" if func else "")) 
                        for frame, offset, lib, func in backtrace_matches]
        
        crash_info.backtrace = backtrace
    
    # 如果堆栈回溯仍然为空，尝试其他格式
    if not crash_info.backtrace:
        # 尝试直接匹配堆栈行
        backtrace_alt_pattern = r"#(\d+)\s+pc\s+([0-9a-fA-F]+)\s+([^\n]+)"
        crash_info.backtrace = re.findall(backtrace_alt_pattern, log_content)
    
    return crash_info


def parse_library_path(lib_path: str) -> str:
    """规范化库的路径"""
    if not lib_path:
        return ""
    return os.path.abspath(os.path.expanduser(lib_path))


def extract_lib_info(backtrace_item: str) -> Tuple[str, str, str, Optional[str]]:
    """从堆栈回溯项中提取库信息"""
    # 处理多种输入格式
    try:
        # 尝试解析完整路径格式: /path/to/lib.so (function+offset)
        lib_path_match = re.search(r"(/[^ ]+\.so)", backtrace_item)
        if lib_path_match:
            lib_path = lib_path_match.group(1)
            lib_name = os.path.basename(lib_path)
        else:
            # 尝试解析简单格式: libname.so (function)
            lib_name_match = re.search(r"([^\s/]+\.so)", backtrace_item)
            if lib_name_match:
                lib_name = lib_name_match.group(1)
                lib_path = lib_name
            else:
                lib_name = "unknown"
                lib_path = ""
        
        # 获取PC偏移地址
        pc_offset_match = re.search(r"pc\s+([0-9a-fA-F]+)", backtrace_item)
        pc_offset = pc_offset_match.group(1) if pc_offset_match else "0"
        
        # 获取帧号
        frame_match = re.search(r"#(\d+)", backtrace_item)
        frame_num = frame_match.group(1) if frame_match else "?"
        
        # 提取函数名 (如果有)
        function_match = re.search(r"\((.*?(?:\+\d+)?)\)", backtrace_item)
        function = function_match.group(1) if function_match and not function_match.group(1).startswith("BuildId") else None
        
        return frame_num, pc_offset, lib_name, function
        
    except Exception as e:
        print(f"警告: 解析堆栈项时出错: {backtrace_item}, 错误: {str(e)}", file=sys.stderr)
        return "?", "0", "unknown", None


def addr2line(addr2line_path: str, lib_path: str, offset: str) -> List[Dict[str, str]]:
    """使用addr2line工具解析地址，返回详细的源码位置信息"""
    if not os.path.exists(lib_path):
        return [{"symbol": f"无法找到库文件: {lib_path}", "source_path": ""}]
    
    try:
        # 使用完整参数调用addr2line以获取详细信息
        cmd = [addr2line_path, "-C", "-f", "-i", "-a", "-p", "-e", lib_path, offset]
        
        if os.path.exists(addr2line_path):
            print(f"{Colors.CYAN}执行命令: {' '.join(cmd)}{Colors.ENDC}")
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        output_lines = result.stdout.strip().split('\n')
        if output_lines:
            print(f"{Colors.CYAN}addr2line原始输出: {output_lines}{Colors.ENDC}")
        
        results = []
        
        # 直接处理整合格式: 0xXXXXXX: function at /path/to/file.cc:line
        for line in output_lines:
            line = line.strip()
            if "at" in line:
                # 匹配格式: 0xXXXXXX: function at /path/to/file.cc:line
                addr_and_func, source = line.split(" at ", 1)
                if ":" in addr_and_func:
                    addr, func = addr_and_func.split(":", 1)
                    results.append({
                        "address": addr.strip(),
                        "symbol": func.strip(),
                        "source_path": source.strip()
                    })
                else:
                    results.append({
                        "address": "",
                        "symbol": addr_and_func.strip(),
                        "source_path": source.strip()
                    })
            else:
                # 处理没有源文件信息的行
                results.append({
                    "address": "",
                    "symbol": line,
                    "source_path": ""
                })
        
        # 如果没有解析出结果，尝试使用原来的解析方法
        if not results:
            i = 0
            while i < len(output_lines):
                line = output_lines[i].strip()
                if line.startswith("0x"):
                    result_entry = {"address": line.split(':')[0].strip()}
                    
                    # 检查是否有下一行
                    if i + 1 < len(output_lines):
                        next_line = output_lines[i+1].strip()
                        
                        # 如果下一行包含 "at" 关键字，说明有源文件信息
                        if " at " in next_line:
                            function_part, source_part = next_line.split(" at ", 1)
                            result_entry["symbol"] = function_part.strip()
                            result_entry["source_path"] = source_part.strip()
                        else:
                            result_entry["symbol"] = next_line
                            result_entry["source_path"] = ""
                        
                        i += 2
                    else:
                        result_entry["symbol"] = "??"
                        result_entry["source_path"] = ""
                        i += 1
                    
                    results.append(result_entry)
                else:
                    # 如果格式不符合预期，直接添加整行
                    results.append({
                        "address": "",
                        "symbol": line,
                        "source_path": ""
                    })
                    i += 1
        
        return results
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr if e.stderr else str(e)
        print(f"{Colors.RED}addr2line 执行失败: {error_msg}{Colors.ENDC}")
        return [{"symbol": f"addr2line 执行失败: {error_msg}", "source_path": ""}]
    except Exception as e:
        print(f"{Colors.RED}addr2line 解析错误: {str(e)}{Colors.ENDC}")
        return [{"symbol": f"错误: {str(e)}", "source_path": ""}]

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
    if not crash_info.backtrace:
        print(f"{Colors.RED}未找到堆栈回溯信息{Colors.ENDC}")
        return
        
    # 显示符号解析选项
    if lib_path:
        print(f"{Colors.YELLOW}使用符号库: {lib_path}{Colors.ENDC}")
    if addr2line_path:
        print(f"{Colors.YELLOW}使用addr2line工具: {addr2line_path}{Colors.ENDC}")
    if target_lib:
        print(f"{Colors.YELLOW}解析目标库: {target_lib}{Colors.ENDC}")
    
    print()
    
    for item in crash_info.backtrace:
        try:
            frame_num, pc_offset, lib_name, function = extract_lib_info(item[2])
            
            # 如果是目标库，解析地址
            if is_target_lib(lib_name, target_lib) and lib_path and os.path.exists(lib_path):
                print(f"{Colors.GREEN}#{item[0]} {Colors.YELLOW}pc {item[1]} {Colors.CYAN}{lib_name}{Colors.ENDC}")
                
                symbol_info = addr2line(addr2line_path, lib_path, item[1])
                
                # 检查原始输出是否有内容
                raw_outputs = []
                for info in symbol_info:
                    if info.get("symbol") and info.get("symbol") != "??":
                        if info.get("source_path"):
                            addr_info = f"{info['address']}: " if info.get('address') else ""
                            raw_outputs.append(f"{addr_info}{info['symbol']} at {info['source_path']}")
                        else:
                            raw_outputs.append(info['symbol'])
                
                if raw_outputs:
                    for output in raw_outputs:
                        print(f"    {Colors.BOLD}{Colors.BLUE}↪ {output}{Colors.ENDC}")
                else:
                    print(f"    {Colors.RED}无法解析符号 (可能缺少调试信息){Colors.ENDC}")
                
                if function:
                    print(f"    {Colors.YELLOW}Function: {function}{Colors.ENDC}")
            else:
                function_info = f" ({function})" if function else ""
                print(f"{Colors.GREEN}#{item[0]} {Colors.YELLOW}pc {item[1]} {Colors.CYAN}{lib_name}{Colors.YELLOW}{function_info}{Colors.ENDC}")
        except Exception as e:
            print(f"{Colors.RED}解析堆栈项时出错 #{item[0]}: {str(e)}{Colors.ENDC}")
            import traceback
            traceback.print_exc()

def analyze_library_with_nm(nm_path: str, lib_path: str) -> List[Dict[str, str]]:
    """使用nm分析库中的符号"""
    if not os.path.exists(lib_path):
        return [{"error": f"无法找到库文件: {lib_path}"}]
    
    try:
        cmd = [nm_path, "-C", lib_path]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        output_lines = result.stdout.strip().split('\n')
        symbols = []
        
        for line in output_lines:
            if line.strip():
                parts = line.strip().split(' ', 2)
                if len(parts) >= 2:
                    symbol = {
                        "address": parts[0] if parts[0] != '' else "未定义地址",
                        "type": parts[1] if len(parts) > 1 else "",
                        "name": parts[2] if len(parts) > 2 else "未知符号"
                    }
                    symbols.append(symbol)
        
        return symbols
    except Exception as e:
        return [{"error": f"nm分析失败: {str(e)}"}]
def main():
    parser = argparse.ArgumentParser(description='解析Android崩溃堆栈')
    parser.add_argument('-i', '--input', help='崩溃日志文件路径 (默认从标准输入读取)')
    parser.add_argument('-l', '--library', help='符号库路径', default='')
    parser.add_argument('-a', '--addr2line', 
                       help='addr2line工具路径',
                       default='/opt/android-ndk-r25b/toolchains/llvm/prebuilt/darwin-x86_64/bin/llvm-addr2line')
    parser.add_argument('-t', '--target', help='要解析的目标库名称', default='libmml_framework.so')
    parser.add_argument('-v', '--verbose', help='输出详细信息', action='store_true')
    parser.add_argument('--nm', help='nm工具路径', 
                   default='/opt/android-ndk-r25b/toolchains/llvm/prebuilt/darwin-x86_64/bin/llvm-nm')
    parser.add_argument('--objdump', help='objdump工具路径',
                    default='/opt/android-ndk-r25b/toolchains/llvm/prebuilt/darwin-x86_64/bin/llvm-objdump')
    parser.add_argument('--analyze-full', action='store_true', 
                        help='使用所有可用工具进行全面分析')
    args = parser.parse_args()
    
    # 读取崩溃日志
    if args.input:
        try:
            with open(args.input, 'r') as f:
                crash_content = f.read()
        except Exception as e:
            print(f"{Colors.RED}无法读取文件 {args.input}: {str(e)}{Colors.ENDC}")
            return
    else:
        # 从标准输入读取或显示帮助
        if sys.stdin.isatty():
            parser.print_help()
            print(f"\n{Colors.YELLOW}请通过管道或--input参数提供崩溃日志。{Colors.ENDC}")
            print(f"\n{Colors.GREEN}示例用法:{Colors.ENDC}")
            print(f"  cat crash.txt | python {sys.argv[0]}")
            print(f"  python {sys.argv[0]} -i crash.txt -l /path/to/lib.so")
            print(f"  python {sys.argv[0]} -l /path/to/lib.so -a /path/to/addr2line -t libname.so < crash.txt")
            return
        crash_content = sys.stdin.read()
    
    if args.verbose:
        print(f"{Colors.BLUE}处理崩溃日志...{Colors.ENDC}")
    
    # 解析崩溃日志
    crash_info = parse_crash_log(crash_content)
    
    # 处理符号库路径
    lib_path = parse_library_path(args.library)
    
    if args.library and not os.path.exists(lib_path):
        print(f"{Colors.RED}警告: 找不到指定的库文件: {lib_path}{Colors.ENDC}")
        if args.analyze_full and os.path.exists(lib_path):
        print(f"\n{Colors.HEADER}{Colors.BOLD}库文件详细分析:{Colors.ENDC}")
        
        # 使用nm查看符号表
        if args.nm and os.path.exists(args.nm):
            print(f"\n{Colors.BLUE}符号表分析 (nm):{Colors.ENDC}")
            symbols = analyze_library_with_nm(args.nm, lib_path)
            # 显示与崩溃相关的符号
            for item in crash_info.backtrace:
                _, pc_offset, lib_name, _ = extract_lib_info(item[2])
                if is_target_lib(lib_name, target_lib):
                    related_symbols = find_related_symbols(symbols, pc_offset)
                    if related_symbols:
                        print(f"{Colors.YELLOW}与地址 {pc_offset} 相关的符号:{Colors.ENDC}")
                        for sym in related_symbols:
                            print(f"  {Colors.CYAN}{sym['address']} {sym['type']} {sym['name']}{Colors.ENDC}")

    # 处理addr2line路径
    addr2line_path = parse_library_path(args.addr2line)
    if not os.path.exists(addr2line_path):
        print(f"{Colors.RED}警告: 找不到addr2line工具: {addr2line_path}{Colors.ENDC}")
        print(f"{Colors.YELLOW}尝试在系统PATH中查找addr2line...{Colors.ENDC}")
        try:
            result = subprocess.run(["which", "addr2line"], capture_output=True, text=True)
            if result.returncode == 0 and result.stdout.strip():
                addr2line_path = result.stdout.strip()
                print(f"{Colors.GREEN}找到addr2line: {addr2line_path}{Colors.ENDC}")
            else:
                print(f"{Colors.RED}在系统PATH中未找到addr2line工具{Colors.ENDC}")
        except:
            print(f"{Colors.RED}无法在系统中查找addr2line工具{Colors.ENDC}")
    
    # 打印解析结果
    print_crash_info(crash_info, args.target, lib_path, addr2line_path)


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"{Colors.RED}发生错误: {str(e)}{Colors.ENDC}")
        import traceback
        traceback.print_exc()
        sys.exit(1)