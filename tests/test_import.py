#!/usr/bin/env python3
"""Test script to verify import works"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from rocksmith_guitar_mute import RocksmithGuitarMute
    print("✓ Import successful!")
    
    # Test basic initialization
    processor = RocksmithGuitarMute()
    print("✓ Processor initialized successfully!")
    
    # Test that process_input method exists
    if hasattr(processor, 'process_input'):
        print("✓ process_input method exists!")
    else:
        print("✗ process_input method missing!")
        
    # List all available methods
    methods = [m for m in dir(processor) if not m.startswith('_') and callable(getattr(processor, m))]
    print(f"Available methods: {methods}")
        
except Exception as e:
    print(f"✗ Import failed: {e}")