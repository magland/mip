"""Platform detection and compatibility utilities"""

import platform
import sys


def get_current_platform_tag():
    """Detect the current platform and return the corresponding MIP platform tag
    
    Returns:
        str: Platform tag (e.g., 'linux_x86_64', 'macosx_11_0_arm64', 'win_amd64')
    """
    system = platform.system()
    machine = platform.machine().lower()
    
    # Normalize machine architecture names
    if machine in ('x86_64', 'amd64'):
        machine = 'x86_64'
    elif machine in ('aarch64', 'arm64'):
        machine = 'aarch64' if system == 'Linux' else 'arm64'
    elif machine in ('i386', 'i686'):
        machine = 'i686'
    
    if system == 'Linux':
        if machine == 'x86_64':
            return 'linux_x86_64'
        elif machine == 'aarch64':
            return 'linux_aarch64'
        elif machine == 'i686':
            return 'linux_i686'
        else:
            return f'linux_{machine}'
    
    elif system == 'Darwin':  # macOS
        if machine == 'x86_64':
            return 'macosx_10_9_x86_64'
        elif machine == 'arm64':
            return 'macosx_11_0_arm64'
        else:
            return f'macosx_10_9_{machine}'
    
    elif system == 'Windows':
        if machine == 'x86_64':
            return 'win_amd64'
        elif machine == 'arm64':
            return 'win_arm64'
        elif machine == 'i686':
            return 'win32'
        else:
            return f'win_{machine}'
    
    else:
        # Unknown platform - return a generic tag
        return f'{system.lower()}_{machine}'


def is_platform_compatible(package_platform_tag, current_platform_tag=None):
    """Check if a package's platform tag is compatible with the current platform
    
    Args:
        package_platform_tag: The platform tag from the package metadata
        current_platform_tag: The current platform tag (detected if not provided)
    
    Returns:
        bool: True if compatible, False otherwise
    """
    if current_platform_tag is None:
        current_platform_tag = get_current_platform_tag()
    
    # Universal packages work on any platform
    if package_platform_tag == 'any':
        return True
    
    # Exact match
    if package_platform_tag == current_platform_tag:
        return True
    
    # Special case: macOS universal2 binaries work on both Intel and Apple Silicon
    if package_platform_tag == 'macosx_10_9_universal2':
        if current_platform_tag in ('macosx_10_9_x86_64', 'macosx_11_0_arm64'):
            return True
    
    return False


def select_best_package_variant(variants, current_platform_tag=None):
    """Select the best package variant for the current platform
    
    When multiple variants of a package exist (e.g., platform-specific and 'any'),
    prefer the platform-specific version.
    
    Args:
        variants: List of package info dictionaries with 'platform_tag' field
        current_platform_tag: The current platform tag (detected if not provided)
    
    Returns:
        dict or None: The best matching package variant, or None if no compatible variant
    """
    if current_platform_tag is None:
        current_platform_tag = get_current_platform_tag()
    
    if not variants:
        return None
    
    # Filter to compatible variants only
    compatible = [v for v in variants if is_platform_compatible(v['platform_tag'], current_platform_tag)]
    
    if not compatible:
        return None
    
    # Prefer exact platform matches over 'any'
    exact_matches = [v for v in compatible if v['platform_tag'] == current_platform_tag]
    if exact_matches:
        # If multiple exact matches, prefer the one with highest version/build
        return exact_matches[0]
    
    # Check for universal2 on macOS
    if current_platform_tag.startswith('macosx_'):
        universal2 = [v for v in compatible if v['platform_tag'] == 'macosx_10_9_universal2']
        if universal2:
            return universal2[0]
    
    # Fall back to 'any' platform
    any_platform = [v for v in compatible if v['platform_tag'] == 'any']
    if any_platform:
        return any_platform[0]
    
    # Should not reach here if is_platform_compatible is working correctly
    return compatible[0] if compatible else None


def get_available_platforms_for_package(variants):
    """Get a list of available platforms for a package
    
    Args:
        variants: List of package info dictionaries with 'platform_tag' field
    
    Returns:
        list: Sorted list of unique platform tags
    """
    platforms = set(v['platform_tag'] for v in variants)
    return sorted(platforms)

def print_platform():
    """Print the current platform tag"""
    platform_tag = get_current_platform_tag()
    print(f"{platform_tag}")
    return platform_tag