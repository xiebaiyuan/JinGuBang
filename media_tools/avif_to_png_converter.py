#!/usr/bin/env python3
"""
Batch convert AVIF images to PNG format in a specified directory.
"""

import os
import sys
import argparse
from pathlib import Path

try:
    from PIL import Image
    import pillow_avif
except ImportError as e:
    print("Error: Required libraries not found.")
    print("Please install them with: pip3 install Pillow pillow-avif-plugin")
    sys.exit(1)

def convert_avif_to_png(input_dir, output_dir=None, recursive=False):
    """
    Convert all AVIF images in the input directory to PNG format.
    
    Args:
        input_dir (str): Path to the directory containing AVIF images
        output_dir (str): Path to the output directory (optional)
        recursive (bool): Whether to search subdirectories recursively
    """
    input_path = Path(input_dir)
    
    # Use input directory as output if no output directory specified
    if output_dir is None:
        output_path = input_path
    else:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
    
    # Find all AVIF files
    if recursive:
        avif_files = list(input_path.rglob("*.avif"))
    else:
        avif_files = list(input_path.glob("*.avif"))
    
    if not avif_files:
        print(f"No AVIF files found in {input_dir}")
        return
    
    print(f"Found {len(avif_files)} AVIF file(s) to convert")
    
    success_count = 0
    error_count = 0
    
    for avif_file in avif_files:
        try:
            # Determine output path
            if output_dir is None:
                png_file = avif_file.with_suffix('.png')
            else:
                # Preserve relative path structure when using separate output directory
                relative_path = avif_file.relative_to(input_path)
                png_file = output_path / relative_path.with_suffix('.png')
                png_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Open and convert image
            with Image.open(avif_file) as img:
                img.save(png_file, 'PNG')
            
            print(f"Converted: {avif_file} -> {png_file}")
            success_count += 1
            
        except Exception as e:
            print(f"Error converting {avif_file}: {e}")
            error_count += 1
    
    print(f"\nConversion complete: {success_count} successful, {error_count} errors")

def main():
    parser = argparse.ArgumentParser(description="Batch convert AVIF images to PNG format")
    parser.add_argument("input_dir", help="Input directory containing AVIF images")
    parser.add_argument("-o", "--output-dir", help="Output directory for PNG images (optional)")
    parser.add_argument("-r", "--recursive", action="store_true", 
                        help="Recursively search subdirectories")
    
    args = parser.parse_args()
    
    if not os.path.isdir(args.input_dir):
        print(f"Error: {args.input_dir} is not a valid directory")
        sys.exit(1)
    
    convert_avif_to_png(args.input_dir, args.output_dir, args.recursive)

if __name__ == "__main__":
    main()