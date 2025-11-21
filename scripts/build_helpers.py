#!/usr/bin/env python3
"""
Helper functions for building MATLAB package (.mhl) files.
"""
import os
import json


def collect_exposed_symbols_top_level(package_dir, base_path="."):
    """
    Collect exposed symbols from the top level of a directory.
    
    Finds:
    - All .m files at the top level
    - All directories starting with '+' (packages)
    - All directories starting with '@' (classes)
    
    Args:
        package_dir: The directory to scan
        base_path: The base path to prepend to symbol names (default: ".")
    
    Returns:
        List of relative paths to exposed symbols
    """
    symbols = []
    
    if not os.path.exists(package_dir):
        return symbols
    
    items = os.listdir(package_dir)
    
    for item in sorted(items):
        item_path = os.path.join(package_dir, item)
        
        if item.endswith('.m') and os.path.isfile(item_path):
            # Add .m file
            symbols.append(os.path.join(base_path, item))
        elif os.path.isdir(item_path) and (item.startswith('+') or item.startswith('@')):
            # Add package or class directory
            symbols.append(os.path.join(base_path, item))
    
    return symbols


def collect_exposed_symbols_recursive(package_dir, base_path="."):
    """
    Recursively collect exposed symbols from a directory tree.
    
    Finds:
    - All .m files at any depth
    - All directories starting with '+' (packages) at any depth
    - All directories starting with '@' (classes) at any depth
    
    Args:
        package_dir: The root directory to scan recursively
        base_path: The base path to prepend to symbol names (default: ".")
    
    Returns:
        List of relative paths to exposed symbols
    """
    symbols = []
    
    if not os.path.exists(package_dir):
        return symbols
    
    for root, dirs, files in os.walk(package_dir):
        # Calculate the relative path from package_dir
        rel_root = os.path.relpath(root, package_dir)
        if rel_root == '.':
            current_base = base_path
        else:
            current_base = os.path.join(base_path, rel_root)
        
        # Add .m files
        for file in sorted(files):
            if file.endswith('.m'):
                symbols.append(os.path.join(current_base, file))
        
        # Add package and class directories
        for dir_name in sorted(dirs):
            if dir_name.startswith('+') or dir_name.startswith('@'):
                symbols.append(os.path.join(current_base, dir_name))
    
    return sorted(symbols)


def collect_exposed_symbols_multiple_paths(package_dirs, base_paths):
    """
    Collect exposed symbols from multiple top-level directories.
    
    Args:
        package_dirs: List of directories to scan (each scanned at top level only)
        base_paths: List of base paths corresponding to each directory
    
    Returns:
        List of relative paths to exposed symbols
    """
    symbols = []
    
    for package_dir, base_path in zip(package_dirs, base_paths):
        symbols.extend(collect_exposed_symbols_top_level(package_dir, base_path))
    
    return sorted(symbols)


def create_mip_json(mip_json_path, dependencies=None, exposed_symbols=None):
    """
    Create a mip.json file with dependencies and exposed_symbols.
    
    Args:
        mip_json_path: Path where the mip.json file should be created
        dependencies: List of package dependencies (default: [])
        exposed_symbols: List of exposed symbol paths (default: [])
    """
    if dependencies is None:
        dependencies = []
    if exposed_symbols is None:
        exposed_symbols = []
    
    mip_config = {
        "dependencies": dependencies,
        "exposed_symbols": exposed_symbols
    }
    
    with open(mip_json_path, 'w') as f:
        json.dump(mip_config, f, indent=2)