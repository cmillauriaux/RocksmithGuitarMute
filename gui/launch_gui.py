#!/usr/bin/env python3
"""
Simple launch script for RockSmith Guitar Mute graphical interface
"""

import sys
import os
from pathlib import Path

def main():
    """Main launch function."""
    print("Launching RockSmith Guitar Mute GUI...")

    # Add current directory to path for imports
    current_dir = Path(__file__).parent
    sys.path.insert(0, str(current_dir))

    # Check that tkinter is available
    try:
        import tkinter as tk
        print("[OK] Tkinter available")
    except ImportError:
        print("[ERROR] Tkinter is not available")
        print("Tkinter is normally included with Python. Reinstall Python if needed.")
        input("Press Enter to close...")
        sys.exit(1)

    # Check that Pillow is available for images
    try:
        from PIL import Image, ImageTk
        print("[OK] Pillow available for images")
    except ImportError:
        print("[WARN] Pillow is not installed")
        print("The logo may not display. Install Pillow with:")
        print("pip install Pillow")
        print("The interface will continue without images...")

    # Clean .pyc files that could cause conflicts
    try:
        import glob
        pyc_files = glob.glob("**/*.pyc", recursive=True)
        for pyc_file in pyc_files:
            try:
                os.remove(pyc_file)
            except:
                pass  # Ignore deletion errors
    except:
        pass  # Ignore cleanup errors

    # Import and launch interface
    try:
        from gui_main import main as gui_main
        print("[OK] GUI loaded")
        gui_main()

    except ImportError as e:
        print(f"[ERROR] Import error: {e}")
        print("\nPossible solutions:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Install Pillow for images: pip install Pillow")
        print("3. Clean temporary files: clean.bat")
        print("4. Verify all files are present")
        input("\nPress Enter to close...")
        sys.exit(1)

    except Exception as e:
        print(f"[ERROR] Launch error: {e}")
        print(f"Error type: {type(e).__name__}")
        print("\nTry:")
        print("1. Clean temporary files: clean.bat")
        print("2. Restart your computer")
        print("3. Check logs for more details")
        input("\nPress Enter to close...")
        sys.exit(1)

if __name__ == "__main__":
    main()
