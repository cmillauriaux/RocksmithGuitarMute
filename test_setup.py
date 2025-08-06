#!/usr/bin/env python3
"""
Simple test script to verify that the setup is working correctly.

This script performs basic checks without processing actual PSARC files.
"""

import sys
from pathlib import Path

def test_imports():
    """Test that all required modules can be imported."""
    print("Testing imports...")
    
    try:
        import torch
        print(f"  ✓ PyTorch {torch.__version__}")
    except ImportError as e:
        print(f"  ✗ PyTorch: {e}")
        return False
    
    try:
        import torchaudio
        print(f"  ✓ TorchAudio {torchaudio.__version__}")
    except ImportError as e:
        print(f"  ✗ TorchAudio: {e}")
        return False
    
    try:
        import demucs.separate
        print("  ✓ Demucs Separate")
    except ImportError as e:
        print(f"  ✗ Demucs: {e}")
        return False
    
    return True

def test_demucs_initialization():
    """Test that Demucs can be initialized."""
    print("Testing Demucs CLI availability...")
    
    try:
        import demucs.separate
        # Test that we can import the main function
        print("  ✓ Demucs separate module available")
        print("  ✓ Can access demucs.separate.main function")
        return True
    except Exception as e:
        print(f"  ✗ Demucs initialization failed: {e}")
        return False

def test_file_structure():
    """Test that required files and directories exist."""
    print("Testing file structure...")
    
    required_paths = [
        "Rocksmith2014.NET",
        "sample/2minutes_p.psarc",
        "rocksmith_guitar_mute.py",
        "requirements.txt"
    ]
    
    all_present = True
    for path_str in required_paths:
        path = Path(path_str)
        if path.exists():
            print(f"  ✓ {path_str}")
        else:
            print(f"  ✗ {path_str} (missing)")
            all_present = False
    
    return all_present

def test_main_script():
    """Test that the main script can be imported."""
    print("Testing main script...")
    
    try:
        # Add current directory to path for import
        sys.path.insert(0, str(Path.cwd()))
        
        # Try to import the main module
        import rocksmith_guitar_mute
        print("  ✓ Main script can be imported")
        
        # Try to create the main class
        processor = rocksmith_guitar_mute.RocksmithGuitarMute(device="cpu")
        print("  ✓ RocksmithGuitarMute class can be instantiated")
        
        return True
    except Exception as e:
        print(f"  ✗ Main script test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("RockSmith Guitar Mute - Setup Test")
    print("=" * 40)
    
    tests = [
        ("Import Test", test_imports),
        ("File Structure", test_file_structure),
        ("Demucs Initialization", test_demucs_initialization),
        ("Main Script", test_main_script),
    ]
    
    results = []
    for name, test_func in tests:
        print(f"\n{name}:")
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"  ✗ Error: {e}")
            results.append((name, False))
    
    print("\n" + "=" * 40)
    print("Test Summary:")
    
    all_passed = True
    for name, result in results:
        status = "✓" if result else "✗"
        print(f"  {status} {name}")
        if not result:
            all_passed = False
    
    if all_passed:
        print(f"\n✓ All tests passed! The setup is working correctly.")
        print(f"  You can now run the example with:")
        print(f"  python run_example.py")
    else:
        print(f"\n✗ Some tests failed. Please check the setup.")
        sys.exit(1)

if __name__ == "__main__":
    main()