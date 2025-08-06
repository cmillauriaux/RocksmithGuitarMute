#!/usr/bin/env python3
"""
Test with real Rocksmith audio file extracted from PSARC.
"""

import logging
import sys
from pathlib import Path

import torch
import torchaudio

# Test if our main script works
try:
    from rocksmith_guitar_mute import RocksmithGuitarMute
except ImportError as e:
    print(f"Error importing main script: {e}")
    sys.exit(1)

def test_real_rocksmith_audio():
    """Test Demucs separation with real Rocksmith audio."""
    print("Testing with real Rocksmith audio...")
    
    # Check if the sample file exists
    sample_file = Path("sample/2minutes.ogg")
    if not sample_file.exists():
        print(f"✗ Sample file not found: {sample_file}")
        print("Please place the extracted OGG file in the sample directory.")
        return False
    
    print(f"✓ Found sample file: {sample_file}")
    
    # Check file info
    try:
        # Use soundfile for OGG files
        import soundfile as sf
        data, sr = sf.read(str(sample_file))
        
        # Convert to torch tensor for consistency
        if len(data.shape) == 1:
            # Mono to stereo
            audio = torch.from_numpy(data).float().unsqueeze(0)
        else:
            # Multi-channel, transpose to (channels, samples)
            audio = torch.from_numpy(data.T).float()
        
        duration = audio.shape[1] / sr
        print(f"  - Audio shape: {audio.shape}")
        print(f"  - Sample rate: {sr}Hz") 
        print(f"  - Duration: {duration:.2f}s")
        print(f"  - Channels: {audio.shape[0]}")
    except Exception as e:
        print(f"✗ Error loading audio file: {e}")
        return False
    
    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    # Create processor
    print("\nInitializing RocksmithGuitarMute processor...")
    processor = RocksmithGuitarMute(demucs_model="htdemucs", device="cpu")
    
    # Create output directory
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    # Test audio processing
    output_audio = output_dir / "2minutes_backing_track.wav"
    
    print(f"\nProcessing audio with Demucs...")
    print("This may take several minutes for the first run (model download + processing)...")
    
    try:
        processor.remove_guitar_track(sample_file, output_audio)
        
        if output_audio.exists():
            print(f"\n✓ Audio processing successful!")
            print(f"✓ Backing track saved: {output_audio}")
            
            # Load and check the output
            processed_audio, processed_sr = torchaudio.load(str(output_audio))
            processed_duration = processed_audio.shape[1] / processed_sr
            
            print(f"  - Processed shape: {processed_audio.shape}")
            print(f"  - Processed sample rate: {processed_sr}Hz")
            print(f"  - Processed duration: {processed_duration:.2f}s")
            
            # Calculate file sizes
            original_size = sample_file.stat().st_size / (1024 * 1024)  # MB
            processed_size = output_audio.stat().st_size / (1024 * 1024)  # MB
            
            print(f"  - Original file size: {original_size:.2f} MB")
            print(f"  - Processed file size: {processed_size:.2f} MB")
            
            return True
        else:
            print("✗ Output file was not created")
            return False
            
    except Exception as e:
        print(f"✗ Audio processing failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run the real audio test."""
    print("RockSmith Guitar Mute - Real Audio Test")
    print("=" * 45)
    
    try:
        success = test_real_rocksmith_audio()
        
        if success:
            print("\n" + "=" * 45)
            print("✓ Real audio test passed!")
            print("The guitar track has been removed from the Rocksmith audio.")
            print("You can now listen to both files to compare:")
            print("  - Original: sample/2minutes.ogg")
            print("  - Backing track: output/2minutes_backing_track.wav")
        else:
            print("\n✗ Real audio test failed!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()