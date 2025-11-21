"""Command implementations for mip"""

import os
import shutil
import sys
import subprocess
import zipfile
import json
from pathlib import Path
from urllib import request
from urllib.error import URLError, HTTPError


def get_mip_dir():
    """Get the mip packages directory path"""
    home = Path.home()
    return home / '.mip' / 'packages'

def _ensure_mip_matlab_setup():
    """Ensure the +mip directory is set up in ~/.mip/matlab
    
    This is called automatically by install, uninstall, and setup commands
    to ensure users always have the latest version of mip.import()
    """
    try:
        # Get the source +mip directory
        source_mip = Path(__file__).parent / '+mip'
        if not source_mip.exists():
            print("Warning: +mip directory not found in package")
            return
        
        # Destination path in ~/.mip/matlab/+mip
        home = Path.home()
        dest_mip = home / '.mip' / 'matlab' / '+mip'
        
        # Create parent directory if it doesn't exist
        dest_mip.parent.mkdir(parents=True, exist_ok=True)
        
        # Copy the +mip directory (remove old one if it exists)
        if dest_mip.exists():
            shutil.rmtree(dest_mip)
        
        shutil.copytree(source_mip, dest_mip)
        
    except Exception as e:
        print(f"Warning: Failed to update MATLAB integration: {e}")


def _build_dependency_graph(package_name, manifest, visited=None, path=None):
    """Recursively build a dependency graph for a package
    
    Args:
        package_name: Name of the package
        manifest: The parsed packages.json manifest
        visited: Set of already visited packages (for cycle detection)
        path: Current path (for cycle detection)
    
    Returns:
        List of package names in dependency order (dependencies first)
    """
    if visited is None:
        visited = set()
    if path is None:
        path = []
    
    # Check for circular dependency
    if package_name in path:
        cycle = ' -> '.join(path + [package_name])
        print(f"Error: Circular dependency detected: {cycle}")
        sys.exit(1)
    
    # If already visited, skip
    if package_name in visited:
        return []
    
    # Find package in manifest
    package_info = None
    for pkg in manifest.get('packages', []):
        if pkg.get('name') == package_name:
            package_info = pkg
            break
    
    if not package_info:
        print(f"Error: Package '{package_name}' not found in repository")
        sys.exit(1)
    
    visited.add(package_name)
    path.append(package_name)
    
    # Collect all dependencies first
    result = []
    for dep in package_info.get('dependencies', []):
        result.extend(_build_dependency_graph(dep, manifest, visited, path[:]))
    
    # Then add this package
    result.append(package_name)
    
    return result


def _download_and_install(package_name, package_info, mip_dir):
    """Download and install a single package
    
    Args:
        package_name: Name of the package
        package_info: Package info from manifest
        mip_dir: The mip directory path
    """
    package_dir = mip_dir / package_name
    
    # Get filename
    mhl_filename = package_info['filename']
    
    # Download the .mhl file
    mhl_url = f"https://magland.github.io/mip/packages/{mhl_filename}"
    print(f"Downloading {package_name} v{package_info['version']}...")
    
    # Create temporary file for download
    mhl_path = mip_dir / f"{package_name}.mhl"
    request.urlretrieve(mhl_url, mhl_path)
    
    # Extract the .mhl file (which is a zip file)
    print(f"Extracting {package_name}...")
    with zipfile.ZipFile(mhl_path, 'r') as zip_ref:
        zip_ref.extractall(package_dir)
    
    # Clean up .mhl file
    mhl_path.unlink()
    
    print(f"Successfully installed '{package_name}'")


def install_package(package_name):
    """Install a package from the mip repository
    
    Args:
        package_name: Name of the package to install
    """
    # Ensure MATLAB integration is up to date
    _ensure_mip_matlab_setup()
    
    mip_dir = get_mip_dir()
    mip_dir.mkdir(parents=True, exist_ok=True)
    
    # Download and parse the packages.json manifest
    manifest_url = "https://magland.github.io/mip/packages.json"
    print(f"Fetching package manifest...")
    
    try:
        # Download manifest
        with request.urlopen(manifest_url) as response:
            manifest_content = response.read().decode('utf-8')
        
        # Parse JSON manifest
        manifest = json.loads(manifest_content)
        
        # Build dependency graph (returns packages in install order)
        print(f"Resolving dependencies for '{package_name}'...")
        install_order = _build_dependency_graph(package_name, manifest)
        
        # Filter out already installed packages
        to_install = []
        package_info_map = {pkg['name']: pkg for pkg in manifest.get('packages', [])}
        
        for pkg_name in install_order:
            package_dir = mip_dir / pkg_name
            if package_dir.exists():
                print(f"Package '{pkg_name}' is already installed")
            else:
                to_install.append(pkg_name)
        
        if not to_install:
            print(f"All packages already installed")
            return
        
        # Show installation plan
        if len(to_install) > 1:
            print(f"\nInstallation plan:")
            for pkg_name in to_install:
                pkg_info = package_info_map[pkg_name]
                print(f"  - {pkg_name} v{pkg_info['version']}")
            print()
        
        # Install each package in order
        for pkg_name in to_install:
            pkg_info = package_info_map[pkg_name]
            _download_and_install(pkg_name, pkg_info, mip_dir)
        
        print(f"\nSuccessfully installed {len(to_install)} package(s)")
        
    except HTTPError as e:
        print(f"Error: Could not download (HTTP {e.code})")
        sys.exit(1)
    except URLError as e:
        print(f"Error: Could not connect to package repository: {e.reason}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: Failed to install package '{package_name}': {e}")
        sys.exit(1)


def uninstall_package(package_name):
    """Uninstall a package"""
    # Ensure MATLAB integration is up to date
    _ensure_mip_matlab_setup()
    
    mip_dir = get_mip_dir()
    package_dir = mip_dir / package_name
    
    # Check if package is installed
    if not package_dir.exists():
        print(f"Package '{package_name}' is not installed")
        return
    
    # Confirm uninstallation
    response = input(f"Are you sure you want to uninstall '{package_name}'? (y/n): ")
    if response.lower() not in ['y', 'yes']:
        print("Uninstallation cancelled")
        return
    
    # Remove the package directory
    try:
        shutil.rmtree(package_dir)
        print(f"Successfully uninstalled '{package_name}'")
    except Exception as e:
        print(f"Error: Failed to uninstall package '{package_name}': {e}")
        sys.exit(1)


def list_packages():
    """List all installed packages"""
    mip_dir = get_mip_dir()
    
    if not mip_dir.exists():
        print("No packages installed yet")
        return
    
    packages = [d.name for d in mip_dir.iterdir() if d.is_dir()]
    
    if not packages:
        print("No packages installed yet")
    else:
        print("Installed packages:")
        for package in sorted(packages):
            print(f"  - {package}")


def setup_matlab():
    """Refresh the +mip directory in ~/.mip/matlab
    
    This ensures you have the latest version of mip.import() after upgrading mip.
    The MATLAB integration is also automatically updated when running install or uninstall commands.
    """
    # Ensure MATLAB integration is up to date
    _ensure_mip_matlab_setup()
    
    home = Path.home()
    mip_matlab_dir = home / '.mip' / 'matlab'
    
    print(f"MATLAB integration updated at: {mip_matlab_dir}")
    print(f"\nMake sure to add '{mip_matlab_dir}' to your MATLAB path.")
    print(f"You can do this by running in MATLAB:")
    print(f"  addpath('{mip_matlab_dir}')")
    print(f"  savepath")
