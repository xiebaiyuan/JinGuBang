# Android SO 文件分析器

这是一个全面的Android SO文件分析工具，提供详细的文件信息、ELF结构分析、依赖库检查、符号表分析以及Android特定的优化建议。

## 主要功能

### 文件基本信息
- **文件属性**: 大小、修改时间、访问时间、创建时间、权限
- **文件哈希**: MD5、SHA1、SHA256哈希值计算
- **文件类型**: 自动识别ELF文件类型和架构

### ELF结构分析  
- **ELF文件头**: 架构、字节序、类型、版本、入口点等详细信息
- **程序段信息**: LOAD段的对齐方式和内存布局
- **节信息统计**: 代码节、数据节分类统计，大小排序显示

### 依赖和符号分析
- **依赖库列表**: 显示所有NEEDED库、SONAME、RPATH等
- **导出符号**: 函数、对象、弱符号的详细信息
- **依赖符号**: 外部符号依赖分析
- **符号统计**: 按大小排序，去重显示

### Android优化检查
- **16KB页面对齐**: Android 15+兼容性检查
- **哈希表优化**: GNU Hash vs SysV Hash分析
- **重定位压缩**: Android重定位表压缩检查
- **NDK版本检测**: 通过Clang版本推断NDK版本

## 使用方法

```bash
# 基本用法
python3 android_so_analyzer.py <SO文件路径>

# 示例
python3 android_so_analyzer.py libexample.so
python3 android_so_analyzer.py /path/to/your/library.so
```

## 输出说明

分析器会输出以下几个主要部分：

1. **文件基本信息** - 文件属性和哈希值
2. **ELF文件头信息** - 架构和基本结构信息  
3. **依赖库分析** - 外部库依赖
4. **导出符号分析** - 可用的函数和对象
5. **节信息统计** - 内存段分布
6. **Android优化检查** - 性能和兼容性分析
7. **分析总结** - 问题汇总和修复建议

## 性能优化建议

分析器会检查以下Android特定的优化项：

### 16KB页面对齐 (Android 15+)
```bash
-Wl,-z,max-page-size=16384
```

### GNU Hash优化 (性能提升)
```bash
-Wl,--hash-style=gnu
```

### 重定位表压缩 (减小文件大小)  
```bash
-Wl,--pack-dyn-relocs=android
```

## 系统要求

- Python 3.6+
- `readelf` 工具 (优先使用NDK中的llvm-readelf)
- `objdump` 工具 (优先使用NDK中的llvm-objdump)
- `strings` 工具
- `file` 工具

## 环境变量

设置 `NDK_ROOT` 环境变量以使用NDK工具链：

```bash
export NDK_ROOT=/path/to/android-ndk-r27
```

## 输出示例

```
=============================== Android SO文件分析报告 ===============================

▶ 文件基本信息
  文件大小: 5,568 字节 (5.4 KB)
  文件类型: ELF 64-bit LSB shared object, ARM aarch64
  MD5: 67fe9ca2bef9f01d84b2dafc1a782ddb

▶ 依赖库分析  
  依赖库数量: 2
  依赖的共享库:
     1. libdl.so
     2. libc.so

▶ 导出符号分析
  总符号数: 40
  导出函数: 11
  主要导出函数:
     1. add_numbers (68 bytes)
     2. test_function (50 bytes)

▶ 配置状态汇总
   ✅ NDK版本: r27 (较新)  
   ❌ 16KB页面对齐: 未支持
   ⚠️ 哈希样式: 部分优化
```

## 故障排除

1. **readelf命令未找到**: 安装binutils或设置NDK_ROOT
2. **权限错误**: 确保对SO文件有读取权限
3. **Python依赖**: 确保Python 3.6+和所需模块

## 许可证

本工具遵循与其他Android开发工具相同的开源许可证。