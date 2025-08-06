#!/usr/bin/env python3
"""Test rsrtools capabilities for PSARC handling."""

import rsrtools

def test_rsrtools():
    """Test what's available in rsrtools."""
    print("Testing rsrtools modules...")
    
    modules_to_test = [
        'rsrtools.files',
        'rsrtools.utils',
        'rsrtools.songlists',
        'rsrtools.importrsm'
    ]
    
    for module_name in modules_to_test:
        try:
            module = __import__(module_name, fromlist=[''])
            print(f"\n✓ {module_name}:")
            attrs = [attr for attr in dir(module) if not attr.startswith('_')]
            for attr in attrs:
                obj = getattr(module, attr)
                if callable(obj):
                    print(f"  📋 {attr}() - function")
                elif hasattr(obj, '__doc__') and obj.__doc__:
                    print(f"  📄 {attr} - {type(obj).__name__}")
                else:
                    print(f"  📄 {attr} - {type(obj).__name__}")
        except Exception as e:
            print(f"✗ {module_name}: {e}")
    
    # Test specific PSARC functions
    print(f"\n=== Testing PSARC-specific functions ===")
    
    # Try to find PSARC-related functions
    potential_modules = [
        'rsrtools.files.psarc',
        'rsrtools.files.archives', 
        'rsrtools.utils.psarc'
    ]
    
    for module_name in potential_modules:
        try:
            module = __import__(module_name, fromlist=[''])
            print(f"✓ Found {module_name}")
            print(f"  Available: {dir(module)}")
        except Exception as e:
            print(f"✗ {module_name}: not found")
    
    # Test with sample file if any PSARC functions exist
    from pathlib import Path
    psarc_file = Path("sample/2minutes_p.psarc")
    
    if psarc_file.exists():
        print(f"\n=== Testing with sample file ===")
        print(f"Sample file: {psarc_file} ({psarc_file.stat().st_size} bytes)")
        
        # Try to use rsrtools.files
        try:
            from rsrtools import files
            print(f"rsrtools.files available: {dir(files)}")
            
            # Look for any file-related functions
            for attr_name in dir(files):
                if 'psarc' in attr_name.lower() or 'archive' in attr_name.lower():
                    print(f"  Found potential PSARC function: {attr_name}")
                    
        except Exception as e:
            print(f"Error testing files module: {e}")

if __name__ == "__main__":
    test_rsrtools()