import os
import re
import requests
import argparse
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse, unquote

def sanitize_filename(filename):
    # 替换空格和特殊字符，但保留中文字符
    invalid_chars = r'<>:"/\\|?*'
    filename = filename.replace(' ', '_')
    for char in invalid_chars:
        filename = filename.replace(char, '')
    return filename

def download_image(url, output_path):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        with open(output_path, 'wb') as img_file:
            img_file.write(response.content)
        return True
    except requests.RequestException as e:
        print(f'下载失败：{url}，错误：{e}')
        return False

def process_markdown(markdown_file, output_dir, output_md_dir):
    # 读取Markdown文件内容
    with open(markdown_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # 移除复制代码的链接
    content = re.sub(r'^.*\[!\[复制代码\].*$\n?', '', content, flags=re.MULTILINE)
    content = re.sub(r'^.*\[复制代码\].*$\n?', '', content, flags=re.MULTILINE)

    # 创建必要的目录
    os.makedirs(output_md_dir, exist_ok=True)
    archive_dir = os.path.join(output_md_dir, 'archive')
    os.makedirs(archive_dir, exist_ok=True)

    # 归档原始Markdown文件
    md_basename = os.path.basename(markdown_file)
    archived_markdown_file = os.path.join(archive_dir, md_basename)
    shutil.copy2(markdown_file, archived_markdown_file)
    print(f'已将原始Markdown文件复制到归档目录：{archived_markdown_file}')

    # 生成Markdown文件的安全名称和图片子目录
    md_name, _ = os.path.splitext(md_basename)
    sanitized_md_name = sanitize_filename(md_name)
    images_subdir = os.path.join(output_dir, sanitized_md_name)
    images_output_dir = os.path.join(output_md_dir, images_subdir)
    os.makedirs(images_output_dir, exist_ok=True)

    # 匹配Markdown中的图片链接
    pattern = r'!\[.*?\]\((https?://[^\s\)]+)\)'
    urls = re.findall(pattern, content)

    # 使用线程池并发下载图片
    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_url = {}
        for idx, url in enumerate(urls):
            parsed_url = urlparse(url)
            filename = os.path.basename(unquote(parsed_url.path))
            if not filename or '.' not in filename:
                filename = f'image_{idx}.png'
            sanitized_filename = sanitize_filename(filename)
            image_path = os.path.join(images_output_dir, sanitized_filename)
            future = executor.submit(download_image, url, image_path)
            future_to_url[future] = (url, sanitized_filename)

        for future in as_completed(future_to_url):
            url, sanitized_filename = future_to_url[future]
            if future.result():
                relative_image_path = os.path.join(images_subdir, sanitized_filename).replace('\\', '/')
                content = content.replace(url, relative_image_path)
                print(f'已下载并替换：{url} -> {relative_image_path}')

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
    process_markdown(args.markdown_file, args.output_dir, args.output_md_dir)
