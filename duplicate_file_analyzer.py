#!/usr/bin/env python3
"""
Duplicate File Analyzer

This script analyzes a directory and identifies duplicate files based on their MD5 hash values.
"""

import os
import hashlib
import argparse
from collections import defaultdict


def calculate_md5(file_path):
    """Calculate MD5 hash of a file."""
    hash_md5 = hashlib.md5()
    try:
        with open(file_path, "rb") as f:
            # Read the file in chunks to handle large files efficiently
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except Exception as e:
        print(f"Error calculating hash for {file_path}: {e}")
        return None


def find_duplicates(directory):
    """Find duplicate files in the given directory."""
    # Dictionary to store file hashes and their paths
    hashes = defaultdict(list)
    
    # Walk through the directory
    for root, _, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            
            # Skip directories and special files
            if not os.path.isfile(file_path):
                continue
                
            # Calculate hash
            file_hash = calculate_md5(file_path)
            if file_hash:
                hashes[file_hash].append(file_path)
    
    # Filter out unique files (only keep entries with more than one file)
    duplicates = {hash_val: paths for hash_val, paths in hashes.items() if len(paths) > 1}
    
    return duplicates


def format_size(size_bytes):
    """Convert bytes to human readable format."""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"


def main():
    parser = argparse.ArgumentParser(description="Find duplicate files in a directory")
    parser.add_argument("directory", help="Directory to analyze for duplicates")
    parser.add_argument("--size", action="store_true", help="Show file sizes in output")
    
    args = parser.parse_args()
    
    # Check if directory exists
    if not os.path.isdir(args.directory):
        print(f"Error: {args.directory} is not a valid directory")
        return
    
    print(f"Analyzing directory: {args.directory}")
    print("=" * 50)
    
    # Find duplicates
    duplicates = find_duplicates(args.directory)
    
    if not duplicates:
        print("No duplicate files found.")
        return
    
    # Display results
    print(f"Found {len(duplicates)} group(s) of duplicate files:\n")
    
    total_saved = 0
    
    for i, (file_hash, file_paths) in enumerate(duplicates.items(), 1):
        print(f"Group {i} (Hash: {file_hash[:16]}...):")
        
        # Get file size for the first file in the group (all should be the same)
        first_file_size = 0
        if args.size:
            try:
                first_file_size = os.path.getsize(file_paths[0])
                print(f"  File size: {format_size(first_file_size)}")
            except OSError:
                pass
        
        # Calculate potential space savings (all duplicates except one)
        total_saved += first_file_size * (len(file_paths) - 1)
        
        # List all files in this group
        for j, file_path in enumerate(file_paths, 1):
            if args.size and first_file_size > 0:
                print(f"  {j}. {file_path}")
            else:
                print(f"  {j}. {file_path}")
        print()
    
    if args.size:
        print(f"Total potential space savings: {format_size(total_saved)}")


if __name__ == "__main__":
    main()