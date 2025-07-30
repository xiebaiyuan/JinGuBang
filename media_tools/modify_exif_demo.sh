#!/bin/bash
# modify_exif.py 使用演示脚本

echo "=== modify_exif.py 使用演示 ==="
echo

# 创建演示目录
DEMO_DIR="./exif_demo"
mkdir -p "$DEMO_DIR"
mkdir -p "$DEMO_DIR/subfolder"

echo "1. 创建演示目录: $DEMO_DIR"
echo

# 检查当前目录是否有图片文件
echo "2. 查找当前目录中的图片文件..."
IMAGE_FILES=$(find . -maxdepth 1 -type f \( -iname "*.jpg" -o -iname "*.jpeg" -o -iname "*.tiff" -o -iname "*.tif" \) | head -3)

if [ -z "$IMAGE_FILES" ]; then
    echo "   没有找到图片文件，将创建示例说明"
    echo "   请将一些 .jpg 或 .jpeg 图片文件放在当前目录中进行测试"
    echo
else
    echo "   找到以下图片文件:"
    echo "$IMAGE_FILES"
    echo
    
    # 复制图片到演示目录
    echo "3. 复制图片到演示目录..."
    for img in $IMAGE_FILES; do
        cp "$img" "$DEMO_DIR/"
        echo "   复制 $img 到 $DEMO_DIR/"
    done
    echo
fi

echo "=== 使用示例 ==="
echo

echo "4. 显示帮助信息:"
echo "   python3 modify_exif.py -h"
echo

echo "5. 查看图片当前的GPS信息:"
echo "   python3 modify_exif.py $DEMO_DIR --show"
echo "   # 递归查看子目录:"
echo "   python3 modify_exif.py $DEMO_DIR --show --recursive"
echo

echo "6. 修改所有图片的GPS位置信息为北京天安门 (39.9042, 116.4074):"
echo "   python3 modify_exif.py $DEMO_DIR --latitude 39.9042 --longitude 116.4074"
echo

echo "7. 修改所有图片的GPS位置信息为上海外滩 (31.2397, 121.4994):"
echo "   python3 modify_exif.py $DEMO_DIR --latitude 31.2397 --longitude 121.4994"
echo

echo "8. 删除所有图片的GPS位置信息:"
echo "   python3 modify_exif.py $DEMO_DIR --remove"
echo

echo "9. 递归处理子目录中的图片:"
echo "   python3 modify_exif.py $DEMO_DIR --latitude 40.7128 --longitude -74.0060 --recursive"
echo

echo "=== 实际演示 ==="
echo

if [ -n "$IMAGE_FILES" ]; then
    echo "现在开始实际演示..."
    echo
    
    # 显示当前GPS信息
    echo "步骤1: 显示图片当前的GPS信息"
    echo "执行: python3 modify_exif.py $DEMO_DIR --show"
    python3 modify_exif.py "$DEMO_DIR" --show
    echo
    
    # 修改GPS信息为北京
    echo "步骤2: 修改GPS位置为北京天安门"
    echo "执行: python3 modify_exif.py $DEMO_DIR --latitude 39.9042 --longitude 116.4074"
    echo "y" | python3 modify_exif.py "$DEMO_DIR" --latitude 39.9042 --longitude 116.4074
    echo
    
    # 再次显示GPS信息
    echo "步骤3: 验证修改结果"
    echo "执行: python3 modify_exif.py $DEMO_DIR --show"
    python3 modify_exif.py "$DEMO_DIR" --show
    echo
    
    # 删除GPS信息
    echo "步骤4: 删除GPS位置信息"
    echo "执行: python3 modify_exif.py $DEMO_DIR --remove"
    echo "y" | python3 modify_exif.py "$DEMO_DIR" --remove
    echo
    
    # 最后验证
    echo "步骤5: 验证删除结果"
    echo "执行: python3 modify_exif.py $DEMO_DIR --show"
    python3 modify_exif.py "$DEMO_DIR" --show
    echo
    
else
    echo "由于没有图片文件，跳过实际演示"
    echo "请将一些图片文件放入当前目录后重新运行此脚本"
    echo
fi

echo "=== 常用地点坐标参考 ==="
echo "北京天安门:     39.9042,  116.4074"
echo "上海外滩:       31.2397,  121.4994"
echo "广州小蛮腰:     23.1086,  113.3245"
echo "深圳市民中心:   22.5522,  114.1203"
echo "杭州西湖:       30.2444,  120.1419"
echo "成都宽窄巷子:   30.6722,  104.0581"
echo "西安钟楼:       34.2658,  108.9420"
echo "纽约时代广场:   40.7580,  -73.9855"
echo "伦敦大本钟:     51.4994,  -0.1245"
echo "巴黎埃菲尔铁塔: 48.8584,   2.2945"
echo

echo "=== 注意事项 ==="
echo "1. 修改操作会直接覆盖原始文件，建议先备份重要图片"
echo "2. 支持的格式: .jpg, .jpeg, .tiff, .tif"
echo "3. 坐标格式: 十进制度数 (正数为北纬/东经，负数为南纬/西经)"
echo "4. 使用 --recursive 参数可以处理子目录中的图片"
echo "5. 使用 --show 参数可以查看现有GPS信息而不修改"
echo

echo "演示完成!"
