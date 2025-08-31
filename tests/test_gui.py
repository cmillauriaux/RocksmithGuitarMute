#!/usr/bin/env python3
"""
Test script for RockSmith Guitar Mute GUI
"""

import sys
import tkinter as tk
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_gui_import():
    """Test GUI import."""
    print("🔍 Testing GUI import...")
    
    try:
        from gui.gui_main import RocksmithGuitarMuteGUI
        print("✅ GUI imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_tkinter():
    """Test tkinter availability."""
    print("🔍 Testing tkinter...")
    
    try:
        import tkinter as tk
        print(f"✅ Tkinter available (version {tk.TkVersion})")
        return True
    except ImportError:
        print("❌ Tkinter not available")
        return False

def test_dependencies():
    """Test main dependencies."""
    print("🔍 Testing dependencies...")
    
    dependencies = [
        ('torch', 'PyTorch'),
        ('torchaudio', 'TorchAudio'),
        ('demucs', 'Demucs'),
        ('soundfile', 'SoundFile'),
        ('numpy', 'NumPy')
    ]
    
    all_ok = True
    for module, name in dependencies:
        try:
            __import__(module)
            print(f"✅ {name}")
        except ImportError:
            print(f"❌ {name} (missing)")
            all_ok = False
    
    return all_ok

def test_gui_creation():
    """Test GUI creation (without displaying)."""
    print("🔍 Testing GUI creation...")
    
    try:
        from gui.gui_main import RocksmithGuitarMuteGUI
        
        # Create temporary root window
        root = tk.Tk()
        root.withdraw()  # Hide window
        
        # Test GUI creation
        app = RocksmithGuitarMuteGUI()
        app.root.withdraw()  # Hide GUI
        
        print("✅ GUI created successfully")
        
        # Cleanup
        app.root.destroy()
        root.destroy()
        
        return True
        
    except Exception as e:
        print(f"❌ Creation error: {e}")
        return False

def test_config():
    """Test configuration system."""
    print("🔍 Testing configuration system...")
    
    try:
        from gui.gui_config import GUIConfig
        
        config = GUIConfig()
        
        # Test read/write
        config.set("test_key", "test_value")
        value = config.get("test_key")
        
        if value == "test_value":
            print("✅ Configuration works")
            return True
        else:
            print("❌ Configuration problem")
            return False
            
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False

def main():
    """Main test function."""
    print("🧪 RockSmith Guitar Mute GUI Tests")
    print("=" * 60)
    
    tests = [
        ("Tkinter", test_tkinter),
        ("Dependencies", test_dependencies),
        ("GUI Import", test_gui_import),
        ("Configuration", test_config),
        ("GUI Creation", test_gui_creation),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}:")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary:")
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 Result: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! GUI is ready.")
        return True
    else:
        print("⚠️  Some tests failed. Check dependencies.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
