#!/usr/bin/env python3
"""
Setup script for RockSmith Guitar Mute

This script prepares the environment for running the RockSmith Guitar Mute tool.
It checks dependencies and builds the necessary .NET components.
"""

import subprocess
import sys
from pathlib import Path

def check_python_requirements():
    """Check if required Python packages are installed."""
    print("Checking Python requirements...")
    
    required_packages = ['torch', 'torchaudio', 'demucs']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"  ✓ {package}")
        except ImportError:
            print(f"  ✗ {package} (missing)")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\nMissing packages: {', '.join(missing_packages)}")
        print("Install them with: pip install -r requirements.txt")
        return False
    
    return True

def check_dotnet():
    """Check if .NET is available."""
    print("Checking .NET installation...")
    
    try:
        result = subprocess.run(['dotnet', '--version'], 
                              capture_output=True, text=True, check=True)
        version = result.stdout.strip()
        print(f"  ✓ .NET {version}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("  ✗ .NET not found")
        print("Please install .NET 8.0 or later from https://dotnet.microsoft.com/download")
        return False

def build_rocksmith_net():
    """Build the Rocksmith2014.NET projects."""
    print("Building Rocksmith2014.NET...")
    
    rocksmith_dir = Path("Rocksmith2014.NET")
    if not rocksmith_dir.exists():
        print(f"  ✗ Rocksmith2014.NET directory not found")
        return False
    
    try:
        # Build the main solution
        result = subprocess.run(['dotnet', 'build', '--configuration', 'Release'],
                              cwd=rocksmith_dir, capture_output=True, text=True, check=True)
        print("  ✓ Rocksmith2014.NET built successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"  ✗ Build failed: {e.stderr}")
        return False

def check_demucs_models():
    """Check if Demucs models are available."""
    print("Checking Demucs models...")
    
    try:
        import demucs.api
        separator = demucs.api.Separator(model="htdemucs")
        print("  ✓ Demucs htdemucs model available")
        return True
    except Exception as e:
        print(f"  ✗ Demucs model check failed: {e}")
        print("The model will be downloaded automatically on first use")
        return True  # This is not a critical error

def check_audio_tools():
    """Check if required audio conversion tools are available."""
    print("Checking audio conversion tools...")
    
    tools_dir = Path("Rocksmith2014.NET/src/Rocksmith2014.Audio/Tools")
    
    if sys.platform == "win32":
        tools_subdir = tools_dir / "win"
        required_tools = ["ww2ogg.exe", "revorb.exe"]
    elif sys.platform == "darwin":
        tools_subdir = tools_dir / "mac"
        required_tools = ["ww2ogg", "revorb"]
    else:  # Linux
        tools_subdir = tools_dir / "linux"
        required_tools = ["ww2ogg", "revorb"]
    
    all_present = True
    for tool in required_tools:
        tool_path = tools_subdir / tool
        if tool_path.exists():
            print(f"  ✓ {tool}")
        else:
            print(f"  ✗ {tool} (missing)")
            all_present = False
    
    if not all_present:
        print("Some audio conversion tools are missing.")
        print("They should be included with the Rocksmith2014.NET project.")
    
    return all_present

def main():
    """Main setup function."""
    print("RockSmith Guitar Mute Setup")
    print("=" * 40)
    
    checks = [
        ("Python Requirements", check_python_requirements),
        (".NET Runtime", check_dotnet),
        ("Rocksmith2014.NET Build", build_rocksmith_net),
        ("Audio Tools", check_audio_tools),
        ("Demucs Models", check_demucs_models),
    ]
    
    results = []
    for name, check_func in checks:
        print(f"\n{name}:")
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"  ✗ Error: {e}")
            results.append((name, False))
    
    print("\n" + "=" * 40)
    print("Setup Summary:")
    
    all_good = True
    for name, result in results:
        status = "✓" if result else "✗"
        print(f"  {status} {name}")
        if not result:
            all_good = False
    
    if all_good:
        print(f"\n✓ Setup complete! You can now run:")
        print(f"  python rocksmith_guitar_mute.py sample/2minutes_p.psarc output/")
    else:
        print(f"\n✗ Setup incomplete. Please fix the issues above and run setup again.")
        sys.exit(1)

if __name__ == "__main__":
    main()