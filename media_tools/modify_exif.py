#!/usr/bin/env python3
"""
批量修改目录中所有图片EXIF中的位置信息
支持删除位置信息或修改为指定位置
"""

import os
import argparse
from pathlib import Path
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import piexif
from fractions import Fraction

# 支持的图片格式
SUPPORTED_FORMATS = {'.jpg', '.jpeg', '.tiff', '.tif'}

def decimal_to_dms(decimal_degrees):
    """将十进制度数转换为度分秒格式"""
    degrees = int(abs(decimal_degrees))
    minutes_float = (abs(decimal_degrees) - degrees) * 60
    minutes = int(minutes_float)
    seconds = (minutes_float - minutes) * 60
    
    # 转换为有理数形式
    degrees_rational = (degrees, 1)
    minutes_rational = (minutes, 1)
    seconds_rational = (int(seconds * 10000), 10000)
    
    return (degrees_rational, minutes_rational, seconds_rational)

def modify_gps_exif(image_path, latitude=None, longitude=None, remove_gps=False):
    """修改或删除图片的GPS EXIF信息"""
    try:
        # 加载图片
        img = Image.open(image_path)
        
        # 获取现有的EXIF数据
        if 'exif' in img.info:
            exif_dict = piexif.load(img.info['exif'])
        else:
            exif_dict = {'0th': {}, '1st': {}, 'Exif': {}, 'GPS': {}, 'Interop': {}}
        
        if remove_gps:
            # 删除GPS信息
            exif_dict['GPS'] = {}
            print(f"已删除 {image_path} 的GPS位置信息")
        elif latitude is not None and longitude is not None:
            # 添加或修改GPS信息
            gps_ifd = {}
            
            # 纬度
            lat_dms = decimal_to_dms(latitude)
            gps_ifd[piexif.GPSIFD.GPSLatitude] = lat_dms
            gps_ifd[piexif.GPSIFD.GPSLatitudeRef] = 'N' if latitude >= 0 else 'S'
            
            # 经度
            lon_dms = decimal_to_dms(longitude)
            gps_ifd[piexif.GPSIFD.GPSLongitude] = lon_dms
            gps_ifd[piexif.GPSIFD.GPSLongitudeRef] = 'E' if longitude >= 0 else 'W'
            
            exif_dict['GPS'] = gps_ifd
            print(f"已修改 {image_path} 的GPS位置信息为: {latitude}, {longitude}")
        
        # 生成新的EXIF数据
        exif_bytes = piexif.dump(exif_dict)
        
        # 保存图片
        img.save(image_path, exif=exif_bytes)
        
        return True
        
    except Exception as e:
        print(f"处理 {image_path} 时出错: {str(e)}")
        return False

def get_current_gps_info(image_path):
    """获取图片当前的GPS信息"""
    try:
        img = Image.open(image_path)
        if 'exif' in img.info:
            exif_dict = piexif.load(img.info['exif'])
            gps_info = exif_dict.get('GPS', {})
            
            if gps_info:
                # 解析纬度
                if piexif.GPSIFD.GPSLatitude in gps_info:
                    lat_dms = gps_info[piexif.GPSIFD.GPSLatitude]
                    lat_ref = gps_info.get(piexif.GPSIFD.GPSLatitudeRef, b'N').decode()
                    latitude = lat_dms[0][0]/lat_dms[0][1] + lat_dms[1][0]/lat_dms[1][1]/60 + lat_dms[2][0]/lat_dms[2][1]/3600
                    if lat_ref == 'S':
                        latitude = -latitude
                else:
                    latitude = None
                
                # 解析经度
                if piexif.GPSIFD.GPSLongitude in gps_info:
                    lon_dms = gps_info[piexif.GPSIFD.GPSLongitude]
                    lon_ref = gps_info.get(piexif.GPSIFD.GPSLongitudeRef, b'E').decode()
                    longitude = lon_dms[0][0]/lon_dms[0][1] + lon_dms[1][0]/lon_dms[1][1]/60 + lon_dms[2][0]/lon_dms[2][1]/3600
                    if lon_ref == 'W':
                        longitude = -longitude
                else:
                    longitude = None
                
                return latitude, longitude
            
    except Exception as e:
        print(f"读取 {image_path} GPS信息时出错: {str(e)}")
    
    return None, None

def process_directory(directory, latitude=None, longitude=None, remove_gps=False, show_current=False, recursive=False):
    """处理目录中的所有图片"""
    directory = Path(directory)
    
    if not directory.exists():
        print(f"错误: 目录 {directory} 不存在")
        return
    
    # 根据是否递归处理选择文件搜索方式
    if recursive:
        pattern = '**/*'
        files = directory.glob(pattern)
    else:
        files = directory.iterdir()
    
    processed_count = 0
    total_count = 0
    
    for file_path in files:
        if file_path.is_file() and file_path.suffix.lower() in SUPPORTED_FORMATS:
            total_count += 1
            
            if show_current:
                # 显示当前GPS信息
                lat, lon = get_current_gps_info(file_path)
                if lat is not None and lon is not None:
                    print(f"{file_path.name}: 纬度={lat:.6f}, 经度={lon:.6f}")
                else:
                    print(f"{file_path.name}: 无GPS信息")
            else:
                # 修改GPS信息
                if modify_gps_exif(file_path, latitude, longitude, remove_gps):
                    processed_count += 1
    
    if not show_current:
        print(f"\n处理完成! 共处理 {processed_count}/{total_count} 张图片")

def main():
    parser = argparse.ArgumentParser(description='批量修改图片EXIF中的GPS位置信息')
    parser.add_argument('directory', help='要处理的图片目录')
    parser.add_argument('--latitude', '-lat', type=float, help='新的纬度 (十进制度数)')
    parser.add_argument('--longitude', '-lon', type=float, help='新的经度 (十进制度数)')
    parser.add_argument('--remove', '-r', action='store_true', help='删除所有GPS位置信息')
    parser.add_argument('--show', '-s', action='store_true', help='显示当前的GPS信息而不修改')
    parser.add_argument('--recursive', action='store_true', help='递归处理子目录')
    
    args = parser.parse_args()
    
    # 参数验证
    if not args.remove and not args.show and (args.latitude is None or args.longitude is None):
        print("错误: 必须提供 --latitude 和 --longitude 参数，或使用 --remove 删除GPS信息，或使用 --show 显示当前信息")
        return
    
    if args.remove and (args.latitude is not None or args.longitude is not None):
        print("错误: --remove 选项不能与 --latitude 或 --longitude 同时使用")
        return
    
    # 显示操作信息
    if args.show:
        print(f"显示目录 {args.directory} 中图片的当前GPS信息:")
    elif args.remove:
        print(f"将删除目录 {args.directory} 中所有图片的GPS位置信息")
    else:
        print(f"将目录 {args.directory} 中所有图片的GPS位置信息修改为: {args.latitude}, {args.longitude}")
    
    if args.recursive:
        print("(包括子目录)")
    
    # 确认操作
    if not args.show:
        confirm = input("确认继续? (y/N): ")
        if confirm.lower() != 'y':
            print("操作已取消")
            return
    
    # 处理图片
    process_directory(
        args.directory, 
        args.latitude, 
        args.longitude, 
        args.remove, 
        args.show,
        args.recursive
    )

if __name__ == '__main__':
    main()
