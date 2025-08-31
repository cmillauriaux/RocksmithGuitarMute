#!/usr/bin/env python3
"""
Windows version of rs-utils audio2wem script.
Converts audio files to Wwise WEM files using Python instead of shell script.

Requires:
- FFmpeg (available in PATH)
- Wwise Authoring Tool + Data (or Wine + Wwise on Windows)
"""

import os
import sys
import shutil
import tarfile
import subprocess
import tempfile
from pathlib import Path


def convert_audio_to_wem(input_file: Path, output_file: Path) -> bool:
    """
    Convert an audio file to WEM format using Wwise template.
    
    Args:
        input_file: Path to input audio file
        output_file: Path for output WEM file
        
    Returns:
        True if conversion successful, False otherwise
    """
    # Get paths to rs-utils (should be in the project root directory)
    script_dir = Path(__file__).parent.resolve()
    
    # Find project root by looking for rs-utils directory
    project_root = script_dir
    while project_root != project_root.parent:
        if (project_root / "rs-utils").exists():
            break
        project_root = project_root.parent
    else:
        # Fallback to script directory
        project_root = script_dir
    
    rs_utils_bin = project_root / "rs-utils" / "bin"
    rs_utils_share = project_root / "rs-utils" / "share"
    
    wwise_template_tar = rs_utils_share / "Wwise_Template.tar.gz"
    
    # On Windows, look for Wwise installation
    if sys.platform == "win32":
        # Common Wwise installation paths
        possible_wwise_paths = [
            Path("C:/Program Files (x86)/Audiokinetic"),
            Path("C:/Program Files/Audiokinetic"),
            Path.home() / "AppData/Local/Audiokinetic"
        ]
        
        wwise_cli = None
        for base_path in possible_wwise_paths:
            if base_path.exists():
                # Look for Wwise installations
                for wwise_dir in base_path.glob("Wwise*"):
                    cli_path = wwise_dir / "Authoring" / "Win32" / "Release" / "bin" / "WwiseCLI.exe"
                    if cli_path.exists():
                        wwise_cli = cli_path
                        break
                if wwise_cli:
                    break
        
        if not wwise_cli:
            print("Error: WwiseCLI.exe not found in standard Wwise installation paths")
            print("Please ensure Wwise Authoring tool is installed")
            return False
    else:
        # Unix-like system, use the script from rs-utils
        wwise_cli = rs_utils_bin / "WwiseCLI"
    
    # Check required files
    if not wwise_template_tar.exists():
        print(f"Error: Wwise template not found at {wwise_template_tar}")
        return False
    
    if not wwise_cli.exists():
        print(f"Error: WwiseCLI not found at {wwise_cli}")
        return False
    
    # Check FFmpeg
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Error: FFmpeg not found. Please install FFmpeg and add it to PATH.")
        return False
    
    # Create temporary working directory
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        wwise_template_dir = temp_path / "Wwise_Template"
        
        try:
            # Extract Wwise template
            print(f"Extracting Wwise template...")
            with tarfile.open(wwise_template_tar, 'r:gz') as tar:
                tar.extractall(temp_path)
            
            # Convert input audio to WAV using FFmpeg
            song_wav = wwise_template_dir / "Originals" / "SFX" / "song.wav"
            song_wav.parent.mkdir(parents=True, exist_ok=True)
            
            print(f"Converting {input_file.name} to WAV...")
            ffmpeg_cmd = [
                "ffmpeg", 
                "-i", str(input_file),
                "-y",  # Overwrite output
                str(song_wav)
            ]
            
            result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"FFmpeg failed: {result.stderr}")
                return False
            
            # Change to template directory
            original_cwd = Path.cwd()
            os.chdir(wwise_template_dir)
            
            try:
                # Run WwiseCLI to generate soundbanks
                print(f"Generating WEM with WwiseCLI...")
                print(f"Using WwiseCLI at: {wwise_cli}")
                
                # Build command for WwiseCLI
                if sys.platform == "win32":
                    # Windows: run WwiseCLI.exe directly
                    wwise_cmd = [str(wwise_cli), "Template.wproj", "-GenerateSoundBanks"]
                else:
                    # Unix-like system
                    wwise_cmd = ["sh", str(wwise_cli), "Template.wproj", "-GenerateSoundBanks"]
                
                print(f"Running command: {' '.join(wwise_cmd)}")
                result = subprocess.run(wwise_cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    print(f"WwiseCLI failed: {result.stderr}")
                    return False
                
                # Find generated WEM file
                wem_cache_dir = wwise_template_dir / ".cache" / "Windows" / "SFX"
                if not wem_cache_dir.exists():
                    print(f"Error: WEM cache directory not found at {wem_cache_dir}")
                    return False
                
                wem_files = list(wem_cache_dir.glob("*.wem"))
                if not wem_files:
                    print(f"Error: No WEM files generated in {wem_cache_dir}")
                    return False
                
                # Copy the generated WEM to output location
                generated_wem = wem_files[0]  # Take the first one
                shutil.copy2(generated_wem, output_file)
                
                print(f"✅ Successfully converted to WEM: {output_file}")
                return True
                
            finally:
                os.chdir(original_cwd)
                
        except Exception as e:
            print(f"Error during conversion: {e}")
            return False


def main():
    """Main function for command line usage."""
    if len(sys.argv) < 2:
        print("Usage: python audio2wem_windows.py INPUT_FILE [OUTPUT_FILE]")
        print("If OUTPUT_FILE is not specified, uses INPUT_FILE.wem")
        sys.exit(1)
    
    input_file = Path(sys.argv[1])
    if not input_file.exists():
        print(f"Error: Input file not found: {input_file}")
        sys.exit(1)
    
    if len(sys.argv) >= 3:
        output_file = Path(sys.argv[2])
    else:
        output_file = input_file.with_suffix('.wem')
    
    print(f"Converting {input_file} to {output_file}")
    
    if convert_audio_to_wem(input_file, output_file):
        print("✅ Conversion completed successfully!")
        sys.exit(0)
    else:
        print("❌ Conversion failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()