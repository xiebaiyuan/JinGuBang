#!/usr/bin/env python3
"""
测试Android SO分析器的增强功能
"""

import subprocess
import sys
import os

def test_analyzer():
    """测试SO分析器的各项功能"""
    test_file = "test_hash_both.so"
    
    if not os.path.exists(test_file):
        print(f"❌ 测试文件 {test_file} 不存在")
        return False
    
    print("🧪 测试Android SO分析器增强功能...")
    print("=" * 50)
    
    # 运行分析器
    try:
        result = subprocess.run([sys.executable, "android_so_analyzer.py", test_file], 
                              capture_output=True, text=True, timeout=30)
        
        if result.returncode != 0:
            print(f"❌ 分析器运行失败: {result.stderr}")
            return False
        
        output = result.stdout
        
        # 检查各个功能是否正常输出
        checks = [
            ("文件基本信息", "文件基本信息"),
            ("哈希值计算", "文件哈希值:"),
            ("ELF头信息", "ELF文件头信息"),
            ("依赖库分析", "依赖库分析"),
            ("符号分析", "导出符号分析"),
            ("节信息统计", "节信息统计"),
            ("16KB对齐检查", "16KB页面对齐检查"),
            ("哈希表分析", "哈希表样式分析"),
            ("重定位分析", "重定位表压缩分析"),
            ("NDK版本检测", "NDK版本分析"),
            ("配置状态汇总", "配置状态汇总"),
        ]
        
        print("检查功能模块:")
        all_passed = True
        
        for name, pattern in checks:
            if pattern in output:
                print(f"  ✅ {name}: 正常")
            else:
                print(f"  ❌ {name}: 缺失")
                all_passed = False
        
        # 检查关键数据是否存在
        data_checks = [
            ("MD5哈希", "MD5:"),
            ("SHA1哈希", "SHA1:"),
            ("SHA256哈希", "SHA256:"),
            ("文件大小", "文件大小:"),
            ("目标架构", "目标架构:"),
            ("依赖库数量", "依赖库数量:"),
            ("总符号数", "总符号数:"),
            ("总节数", "总节数:"),
        ]
        
        print("\n检查关键数据:")
        for name, pattern in data_checks:
            if pattern in output:
                print(f"  ✅ {name}: 存在")
            else:
                print(f"  ❌ {name}: 缺失")
                all_passed = False
        
        print(f"\n{'=' * 50}")
        if all_passed:
            print("🎉 所有功能测试通过！")
            print("\n主要增强功能:")
            print("  • 文件基本信息分析 (大小、时间、哈希值)")
            print("  • ELF文件头详细信息")
            print("  • 依赖库和符号表分析")
            print("  • 节信息统计和分类")
            print("  • 保持原有的优化检查功能")
            return True
        else:
            print("❌ 部分功能测试失败")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ 分析器运行超时")
        return False
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        return False

if __name__ == "__main__":
    success = test_analyzer()
    sys.exit(0 if success else 1)