# AVIF to PNG Converter

A Python script to batch convert AVIF images to PNG format.

## Features

- Convert all AVIF images in a directory to PNG format
- Option to recursively process subdirectories
- Option to specify a separate output directory
- Preserves directory structure when using separate output directory

## Requirements

- Python 3.x
- Pillow library
- pillow-avif-plugin

## Installation

Run the installation script:

```bash
./install_avif_deps.sh
```

Or manually install the required packages:

```bash
pip3 install Pillow pillow-avif-plugin
```

## Usage

Basic usage:
```bash
python3 avif_to_png_converter.py /path/to/avif/images
```

Options:
- `-o`, `--output-dir`: Specify a separate output directory for PNG files
- `-r`, `--recursive`: Recursively process subdirectories

Examples:
```bash
# Convert all AVIF files in the current directory
python3 avif_to_png_converter.py .

# Convert all AVIF files in a specific directory
python3 avif_to_png_converter.py /path/to/avif/images

# Convert with separate output directory
python3 avif_to_png_converter.py /path/to/avif/images -o /path/to/png/output

# Recursively convert files in subdirectories
python3 avif_to_png_converter.py /path/to/avif/images -r

# Combine options
python3 avif_to_png_converter.py /path/to/avif/images -o /path/to/png/output -r
```

## Notes

- If no output directory is specified, PNG files will be created in the same directory as the AVIF files
- When using a separate output directory, the script preserves the relative directory structure
- Existing PNG files with the same name will be overwritten