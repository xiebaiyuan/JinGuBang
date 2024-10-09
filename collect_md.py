# python collect_md.py /Users/xiebaiyuan/Downloads/一文读懂Cache一致性原理.md -o md_images -d  /Users/xiebaiyuan/Documents/md_collects/
import os
import re
import requests
import argparse
import hashlib

def download_images(markdown_file, output_dir, output_md_dir):
    # 读取Markdown文件内容
    with open(markdown_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # 确保输出目录存在
    if not os.path.exists(output_md_dir):
        os.makedirs(output_md_dir)

    # 生成Markdown文件的唯一标识（例如使用文件名或哈希值）
    md_basename = os.path.basename(markdown_file)
    md_name, _ = os.path.splitext(md_basename)
    # 如果有同名文件，可以使用哈希值
    # md_hash = hashlib.md5(markdown_file.encode('utf-8')).hexdigest()
    # images_subdir = os.path.join(output_dir, md_hash)

    # 为每个Markdown文件创建单独的图片目录
    images_subdir = os.path.join(output_dir, md_name)
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

        # 下载图片
        response = requests.get(url)
        if response.status_code == 200:
            image_path = os.path.join(images_output_dir, filename)
            with open(image_path, 'wb') as img_file:
                img_file.write(response.content)
            # 替换Markdown中的链接为新的相对路径
            relative_image_path = os.path.join(images_subdir, filename).replace('\\', '/')
            content = content.replace(url, relative_image_path)
            print(f'已下载并替换：{url} -> {image_path}')
        else:
            print(f'下载失败：{url}')

    # 将更新后的内容写入新的Markdown文件
    output_markdown_file = os.path.join(output_md_dir, md_basename)
    with open(output_markdown_file, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f'已生成修改后的Markdown文件：{output_markdown_file}')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='下载Markdown文件中的网络图片并替换为本地路径，同时将修改后的Markdown和图片放置到指定目录')
    parser.add_argument('markdown_file', help='Markdown文件的路径')
    parser.add_argument('-o', '--output_dir', default='images', help='保存图片的目录，默认为 images')
    parser.add_argument('-d', '--output_md_dir', default='.', help='保存修改后的Markdown文件和图片的目录，默认为当前目录')

    args = parser.parse_args()
    download_images(args.markdown_file, args.output_dir, args.output_md_dir)