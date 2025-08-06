#!/usr/bin/env python3
"""Test the rsrtools welder module for PSARC extraction."""

import sys
import tempfile
from pathlib import Path

# Add the rsrtools source to path
sys.path.insert(0, str(Path("rsrtools/src").resolve()))

from rsrtools.files.welder import Welder

def test_welder_extraction():
    """Test PSARC extraction using rsrtools welder."""
    print("=== Testing rsrtools Welder ===")
    
    psarc_file = Path("sample/2minutes_p.psarc")
    if not psarc_file.exists():
        print(f"✗ PSARC file not found: {psarc_file}")
        return False
    
    print(f"Testing with: {psarc_file}")
    print(f"File size: {psarc_file.stat().st_size / (1024*1024):.2f} MB")
    
    try:
        # Open PSARC file for reading
        with Welder(psarc_file, mode="r") as psarc:
            print("✓ PSARC opened successfully")
            
            # List all files in the archive
            print(f"\n=== Archive Contents ===")
            file_count = 0
            audio_files = []
            other_files = []
            
            for index in psarc:
                file_name = psarc.arc_name(index)
                file_count += 1
                
                # Check if it's an audio file
                if any(file_name.lower().endswith(ext) for ext in ['.ogg', '.wav', '.wem']):
                    audio_files.append((index, file_name))
                else:
                    other_files.append((index, file_name))
            
            print(f"Total files: {file_count}")
            print(f"Audio files: {len(audio_files)}")
            print(f"Other files: {len(other_files)}")
            
            # Show audio files
            if audio_files:
                print(f"\n📄 Audio files:")
                for index, file_name in audio_files:
                    try:
                        # Get file data to check size
                        data = psarc.arc_data(index)
                        size = len(data) / (1024 * 1024)  # MB
                        print(f"  {file_name}: {size:.2f} MB")
                    except Exception as e:
                        print(f"  {file_name}: Error reading - {e}")
            
            # Show some other files
            if other_files:
                print(f"\n📄 Other files (first 10):")
                for index, file_name in other_files[:10]:
                    try:
                        data = psarc.arc_data(index)
                        size = len(data) / 1024  # KB
                        print(f"  {file_name}: {size:.1f} KB")
                    except Exception as e:
                        print(f"  {file_name}: Error reading - {e}")
                
                if len(other_files) > 10:
                    print(f"  ... and {len(other_files) - 10} more")
            
            # Test extraction to temp directory
            print(f"\n=== Testing Extraction ===")
            
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                # Change to temp directory for extraction
                original_cwd = Path.cwd()
                try:
                    import os
                    os.chdir(temp_path)
                    
                    # Extract the archive
                    psarc.unpack()
                    
                    # Check extracted files
                    extracted_dir = temp_path / psarc_file.stem
                    if extracted_dir.exists():
                        print(f"✓ Archive extracted to: {extracted_dir}")
                        
                        # Count extracted files
                        extracted_files = list(extracted_dir.rglob("*"))
                        extracted_file_count = len([f for f in extracted_files if f.is_file()])
                        
                        print(f"  - Extracted {extracted_file_count} files")
                        
                        # Find audio files
                        extracted_audio = [f for f in extracted_files 
                                         if f.is_file() and f.suffix.lower() in ['.ogg', '.wav', '.wem']]
                        
                        print(f"  - Audio files: {len(extracted_audio)}")
                        for audio_file in extracted_audio:
                            size = audio_file.stat().st_size / (1024 * 1024)  # MB
                            print(f"    🎵 {audio_file.name}: {size:.2f} MB")
                        
                        return True
                    else:
                        print(f"✗ Extraction directory not found: {extracted_dir}")
                        return False
                        
                finally:
                    os.chdir(original_cwd)
    
    except Exception as e:
        print(f"✗ Error testing welder: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_welder_extraction()
    if success:
        print("\n🎉 rsrtools Welder works perfectly!")
        print("We can now extract PSARC files properly!")
    else:
        print("\n❌ rsrtools Welder test failed")