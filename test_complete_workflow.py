#!/usr/bin/env python3
"""Test the complete PSARC workflow with rsrtools integration."""

import sys
import tempfile
from pathlib import Path

# Add rsrtools to path
sys.path.insert(0, str(Path("rsrtools/src").resolve()))

from rocksmith_guitar_mute import RocksmithGuitarMute

def test_complete_workflow():
    """Test the complete workflow: unpack -> process -> repack."""
    print("=== Testing Complete Workflow ===")
    
    # Input and output paths
    input_psarc = Path("sample/2minutes_p.psarc")
    output_dir = Path("test_output")
    
    if not input_psarc.exists():
        print(f"✗ Input PSARC not found: {input_psarc}")
        return False
    
    # Clean up previous test
    if output_dir.exists():
        import shutil
        shutil.rmtree(output_dir)
    
    try:
        # Initialize the processor
        processor = RocksmithGuitarMute(
            demucs_model="htdemucs_6s",
            device="cpu"  # Use CPU for reliable testing
        )
        
        print(f"📁 Input: {input_psarc}")
        print(f"📁 Output: {output_dir}")
        print(f"📊 Original size: {input_psarc.stat().st_size / (1024*1024):.2f} MB")
        
        # Process the PSARC file
        print("\n🚀 Starting processing...")
        result_psarc = processor.process_psarc_file(input_psarc, output_dir)
        
        if result_psarc.exists():
            print(f"✅ Success! Processed PSARC created: {result_psarc}")
            print(f"📊 Processed size: {result_psarc.stat().st_size / (1024*1024):.2f} MB")
            
            # Verify the result is a valid PSARC
            print("\n🔍 Verifying result...")
            try:
                from rsrtools.files.welder import Welder
                with Welder(result_psarc, mode="r") as verify_psarc:
                    file_count = sum(1 for _ in verify_psarc)
                    print(f"✅ Result verification passed: {file_count} files in output PSARC")
                    
                    # List audio files in result
                    audio_files = []
                    for index in verify_psarc:
                        file_name = verify_psarc.arc_name(index)
                        if any(file_name.lower().endswith(ext) for ext in ['.ogg', '.wav', '.wem']):
                            data = verify_psarc.arc_data(index)
                            size = len(data) / (1024 * 1024)  # MB
                            audio_files.append((file_name, size))
                    
                    print(f"🎵 Audio files in result: {len(audio_files)}")
                    for file_name, size in audio_files:
                        print(f"  - {file_name}: {size:.2f} MB")
                    
                    return True
                    
            except Exception as e:
                print(f"✗ Result verification failed: {e}")
                return False
        else:
            print(f"✗ Processing failed - no output file created")
            return False
            
    except Exception as e:
        print(f"✗ Workflow failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_complete_workflow()
    if success:
        print("\n🎉 Complete workflow test PASSED!")
        print("The rsrtools integration is working perfectly!")
    else:
        print("\n❌ Complete workflow test FAILED")
        print("There are still issues to resolve.")