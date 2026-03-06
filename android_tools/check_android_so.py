#!/usr/bin/env python3
"""
Android SO 链接器选项验证脚本
用于检查 -Wl,--hash-style=gnu 和 -Wl,--pack-dyn-relocs=android 是否生效

用法: python3 check_android_so.py <path_to_so_file> [ndk_path]
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

def find_llvm_readelf(ndk_path=None):
    """查找 llvm-readelf 工具路径"""
    if ndk_path:
        candidate = Path(ndk_path) / "toolchains" / "llvm" / "prebuilt" / "darwin-x86_64" / "bin" / "llvm-readelf"
        if candidate.exists():
            return str(candidate)
    
    # 尝试常见的NDK路径
    common_paths = [
        "/opt/android-ndk-r27d",
        "/opt/android-ndk",
        "/Users/$USER/Library/Android/sdk/ndk",
        os.path.expanduser("~/Library/Android/sdk/ndk"),
        "/usr/local/android-ndk",
    ]
    
    for base_path in common_paths:
        if "$USER" in base_path:
            base_path = base_path.replace("$USER", os.getenv("USER", ""))
        
        tool_path = Path(base_path) / "toolchains" / "llvm" / "prebuilt" / "darwin-x86_64" / "bin" / "llvm-readelf"
        if tool_path.exists():
            return str(tool_path)
    
    return None

def run_readelf_command(readelf_path, so_file, section_type):
    """运行 readelf 命令并返回结果"""
    try:
        cmd = [readelf_path, "-S", so_file]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ 运行 readelf 命令失败: {e}")
        return None
    except FileNotFoundError:
        print(f"❌ 找不到 llvm-readelf 工具: {readelf_path}")
        return None

def analyze_hash_sections(output):
    """分析哈希表节区"""
    lines = output.split('\n')
    gnu_hash_found = False
    trad_hash_found = False
    
    for line in lines:
        if '.gnu.hash' in line:
            gnu_hash_found = True
            print(f"✅ 找到 .gnu.hash 节区: {line.strip()}")
        elif '.hash' in line and not line.strip().startswith('['):
            trad_hash_found = True
            print(f"📝 找到 .hash 节区: {line.strip()}")
    
    return gnu_hash_found, trad_hash_found

def analyze_relocation_sections(output):
    """分析重定位节区"""
    lines = output.split('\n')
    android_rela_found = False
    traditional_rela_found = False
    
    for line in lines:
        if 'rela.dyn' in line.lower():
            if 'ANDROID_RELA' in line:
                android_rela_found = True
                print(f"✅ 找到 ANDROID_RELA 类型的 .rela.dyn 节区: {line.strip()}")
            elif 'RELA' in line and not traditional_rela_found:
                traditional_rela_found = True
                print(f"❌ 找到传统 RELA 类型的 .rela.dyn 节区: {line.strip()}")
    
    return android_rela_found, traditional_rela_found

def main():
    parser = argparse.ArgumentParser(description='验证Android SO文件的链接器选项')
    parser.add_argument('so_file', help='要检查的SO文件路径')
    parser.add_argument('--ndk-path', help='NDK路径（可选）', default=None)
    
    args = parser.parse_args()
    
    so_file = args.so_file
    ndk_path = args.ndk_path
    
    # 检查SO文件是否存在
    if not os.path.exists(so_file):
        print(f"❌ 错误: 文件 '{so_file}' 不存在")
        sys.exit(1)
    
    print(f"🔍 开始分析文件: {so_file}")
    print("=" * 60)
    
    # 查找 llvm-readelf
    readelf_path = find_llvm_readelf(ndk_path)
    if not readelf_path:
        print("❌ 找不到 llvm-readelf 工具，请指定NDK路径或安装Android NDK")
        sys.exit(1)
    
    print(f"📦 使用工具: {readelf_path}")
    print("=" * 60)
    
    # 运行readelf命令
    output = run_readelf_command(readelf_path, so_file, "-S")
    if output is None:
        sys.exit(1)
    
    # 分析哈希表选项
    print("1. 检查 -Wl,--hash-style=gnu 选项:")
    gnu_hash_found, trad_hash_found = analyze_hash_sections(output)
    
    if gnu_hash_found and not trad_hash_found:
        print("✅ 结论: -Wl,--hash-style=gnu 选项已生效 (仅使用 .gnu.hash)")
    elif gnu_hash_found and trad_hash_found:
        print("⚠️  结论: 同时存在 .gnu.hash 和 .hash，可能未使用 --hash-style=gnu")
    else:
        print("❌ 结论: 未找到 .gnu.hash，-Wl,--hash-style=gnu 选项未生效")
    
    print("")
    
    # 分析重定位压缩选项
    print("2. 检查 -Wl,--pack-dyn-relocs=android 选项:")
    android_rela_found, traditional_rela_found = analyze_relocation_sections(output)
    
    if android_rela_found:
        print("✅ 结论: -Wl,--pack-dyn-relocs=android 选项已生效 (使用 ANDROID_RELA 格式)")
    elif traditional_rela_found:
        print("❌ 结论: -Wl,--pack-dyn-relocs=android 选项未生效 (使用传统 RELA 格式)")
    else:
        print("⚠️  结论: 未找到 .rela.dyn 节区，无法确定重定位压缩状态")
    
    print("=" * 60)
    
    # 最终总结
    print("📊 最终总结:")
    if gnu_hash_found and not trad_hash_found:
        print("   ✅ -Wl,--hash-style=gnu: 已生效")
    else:
        print("   ❌ -Wl,--hash-style=gnu: 未生效")
    
    if android_rela_found:
        print("   ✅ -Wl,--pack-dyn-relocs=android: 已生效")
    else:
        print("   ❌ -Wl,--pack-dyn-relocs=android: 未生效")

if __name__ == "__main__":
    main()
