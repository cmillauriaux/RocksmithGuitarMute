#!/usr/bin/env python3
"""Explore the rocksmith module structure."""

import pkgutil
import sys

try:
    import rocksmith
    print("✓ rocksmith module imported successfully")
    print(f"Module path: {rocksmith.__file__}")
    print(f"Module dir: {dir(rocksmith)}")
    
    print("\nSubmodules:")
    for importer, modname, ispkg in pkgutil.iter_modules(rocksmith.__path__, rocksmith.__name__ + '.'):
        print(f"  {modname} (package: {ispkg})")
    
    # Try to import common submodules
    submodules_to_try = [
        'rocksmith.psarc',
        'rocksmith.archive', 
        'rocksmith.sng',
        'rocksmith.formats',
        'rocksmith.formats.psarc'
    ]
    
    print("\nTrying to import submodules:")
    for module_name in submodules_to_try:
        try:
            module = __import__(module_name, fromlist=[''])
            print(f"  ✓ {module_name}: {dir(module)}")
        except ImportError as e:
            print(f"  ✗ {module_name}: {e}")
    
    # Try some alternative imports
    print("\nTrying alternative imports:")
    alternatives = [
        ('from rocksmith import psarc', 'rocksmith.psarc'),
        ('from rocksmith.formats import psarc', 'rocksmith.formats.psarc'),
        ('import rocksmith.formats.psarc as psarc', 'rocksmith.formats.psarc'),
    ]
    
    for import_statement, module_path in alternatives:
        try:
            exec(import_statement)
            print(f"  ✓ {import_statement} - Success!")
        except Exception as e:
            print(f"  ✗ {import_statement} - {e}")

except ImportError as e:
    print(f"✗ Failed to import rocksmith: {e}")
    sys.exit(1)