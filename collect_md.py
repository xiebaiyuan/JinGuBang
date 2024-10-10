import os
import re
import requests
import argparse
import hashlib
import shutil

def sanitize_filename(filename):
    # 替换空格和特殊字符，但保留中文字符
    invalid_chars = r'<>:"/\\|?*'
    filename = filename.replace(' ', '_')
    for char in invalid_chars:
        filename = filename.replace(char, '')
    return filename

def download_images(markdown_file, output_dir, output_md_dir):
    # 读取Markdown文件内容
    with open(markdown_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # 确保输出目录存在
    if not os.path.exists(output_md_dir):
        os.makedirs(output_md_dir)

    # 创建输出目录下的 archive 子目录
    archive_dir = os.path.join(output_md_dir, 'archive')
    if not os.path.exists(archive_dir):
        os.makedirs(archive_dir)

    # 将原始Markdown文件复制到 archive 目录
    md_basename = os.path.basename(markdown_file)
    archived_markdown_file = os.path.join(archive_dir, md_basename)
    shutil.copy2(markdown_file, archived_markdown_file)
    print(f'已将原始Markdown文件复制到归档目录：{archived_markdown_file}')

    # 生成Markdown文件的安全名称
    md_name, md_ext = os.path.splitext(md_basename)
    sanitized_md_name = sanitize_filename(md_name)

    # 为每个Markdown文件创建独立的图片目录
    images_subdir = os.path.join(output_dir, sanitized_md_name)
    images_output_dir = os.path.join(output_md_dir, images_subdir)
    if not os.path.exists(images_output_dir):
        os.makedirs(images_output_dir)

    # 匹配Markdown中的图片链接 ![alt text](image_url)
    pattern = r'!\[.*?\]\((https?://[^\s\)]+)\)'
    urls = re.findall(pattern, content)

    for idx, url in enumerate(urls):
        # 获取图片的文件名，如果没有，则使用索引
        filename = os.path.basename(url)
        if not filename or '.' not in filename:
            filename = f'image_{idx}.png'
        else:
            # 移除查询参数
            filename = filename.split('?')[0]

        # 对图片文件名进行规范化处理
        sanitized_filename = sanitize_filename(filename)

        # 下载图片
        try:
            response = requests.get(url)
            response.raise_for_status()
            image_path = os.path.join(images_output_dir, sanitized_filename)
            with open(image_path, 'wb') as img_file:
                img_file.write(response.content)
            # 替换Markdown中的链接为新的相对路径
            relative_image_path = os.path.join(images_subdir, sanitized_filename).replace('\\', '/')
            content = content.replace(url, relative_image_path)
            print(f'已下载并替换：{url} -> {image_path}')
        except requests.RequestException as e:
            print(f'下载失败：{url}，错误：{e}')

    # 将更新后的内容写入新的Markdown文件
    output_markdown_file = os.path.join(output_md_dir, md_basename)
    with open(output_markdown_file, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f'已生成修改后的Markdown文件：{output_markdown_file}')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='下载Markdown文件中的网络图片并替换为本地路径，同时将修改后的Markdown和图片放置到指定目录，并将原始Markdown文件保存到输出目录的archive子目录中')
    parser.add_argument('markdown_file', help='Markdown文件的路径')
    parser.add_argument('-o', '--output_dir', default='images', help='保存图片的目录，默认为 images')
    parser.add_argument('-d', '--output_md_dir', default='.', help='保存修改后的Markdown文件和图片的目录，默认为当前目录')

    args = parser.parse_args()
    download_images(args.markdown_file, args.output_dir, args.output_md_dir)