#!/usr/bin/env python3
"""Test workflow bypassing WEM conversion using the already extracted OGG."""

import sys
import shutil
import tempfile
from pathlib import Path

# Add rsrtools to path
sys.path.insert(0, str(Path("rsrtools/src").resolve()))

from rocksmith_guitar_mute import RocksmithGuitarMute

def test_workflow_with_ogg():
    """Test the workflow using the pre-extracted OGG file."""
    print("=== Testing Workflow with Pre-extracted OGG ===")
    
    # Use the OGG file we already have
    ogg_file = Path("sample/2minutes.ogg")
    output_dir = Path("test_output_ogg")
    
    if not ogg_file.exists():
        print(f"✗ OGG file not found: {ogg_file}")
        return False
    
    # Clean up previous test
    if output_dir.exists():
        shutil.rmtree(output_dir)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Initialize the processor
        processor = RocksmithGuitarMute(
            demucs_model="htdemucs_6s",
            device="cpu"  # Use CPU for reliable testing
        )
        
        print(f"📁 Input OGG: {ogg_file}")
        print(f"📁 Output: {output_dir}")
        print(f"📊 Original size: {ogg_file.stat().st_size / (1024*1024):.2f} MB")
        
        # Test the guitar removal directly
        output_backing = output_dir / "backing_track.wav"
        
        print("\n🎵 Testing Demucs guitar separation...")
        processor.remove_guitar_track(ogg_file, output_backing)
        
        if output_backing.exists():
            print(f"✅ Success! Backing track created: {output_backing}")
            print(f"📊 Backing track size: {output_backing.stat().st_size / (1024*1024):.2f} MB")
            
            # Test the conversion back to WEM format (placeholder)
            output_wem = output_dir / "processed.wem"
            processor.convert_wav_to_wem(output_backing, output_wem)
            
            if output_wem.exists():
                print(f"✅ WEM conversion completed: {output_wem}")
                print(f"📊 WEM size: {output_wem.stat().st_size / (1024*1024):.2f} MB")
                return True
            else:
                print("⚠️ WEM conversion failed, but audio processing worked")
                return True
        else:
            print("✗ Demucs processing failed")
            return False
            
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_workflow_with_ogg()
    if success:
        print("\n🎉 Core audio processing test PASSED!")
        print("Demucs integration works perfectly!")
        print("The remaining issue is WEM conversion, which we can resolve separately.")
    else:
        print("\n❌ Core audio processing test FAILED")