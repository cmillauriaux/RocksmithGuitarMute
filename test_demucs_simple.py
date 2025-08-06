#!/usr/bin/env python3
"""
Simple test to verify Demucs integration works correctly.
"""

import logging
import sys
import tempfile
from pathlib import Path

import torch
import torchaudio

# Test if our main script works
try:
    from rocksmith_guitar_mute import RocksmithGuitarMute
except ImportError as e:
    print(f"Error importing main script: {e}")
    sys.exit(1)

def create_test_audio(output_path: Path, duration: float = 5.0, sample_rate: int = 44100):
    """Create a simple test audio file with multiple frequency components."""
    print(f"Creating test audio: {output_path}")
    
    # Create a simple multi-tone audio (simulating a mix)
    t = torch.linspace(0, duration, int(sample_rate * duration))
    
    # Different frequency components (simulating different instruments)
    drums = 0.3 * torch.sin(2 * torch.pi * 80 * t)  # Low frequency (bass drum)
    bass = 0.4 * torch.sin(2 * torch.pi * 110 * t)  # Bass line
    vocals = 0.3 * torch.sin(2 * torch.pi * 440 * t)  # Mid frequency (vocals)
    guitar = 0.2 * torch.sin(2 * torch.pi * 660 * t)  # Higher frequency (guitar)
    
    # Mix all components (stereo)
    mix = drums + bass + vocals + guitar
    stereo_mix = torch.stack([mix, mix])  # Create stereo from mono
    
    # Save the test audio
    torchaudio.save(str(output_path), stereo_mix, sample_rate)
    print(f"Test audio created: {output_path} ({duration}s, {sample_rate}Hz)")

def test_demucs_separation():
    """Test Demucs separation with a simple audio file."""
    print("Testing Demucs separation...")
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create test audio
        test_audio = temp_path / "test_audio.wav"
        create_test_audio(test_audio, duration=5.0)
        
        # Create processor
        processor = RocksmithGuitarMute(demucs_model="htdemucs", device="cpu")
        
        # Test audio processing
        output_audio = temp_path / "backing_track.wav"
        
        try:
            processor.remove_guitar_track(test_audio, output_audio)
            
            if output_audio.exists():
                print("✓ Demucs separation successful!")
                
                # Load and check the output
                audio, sr = torchaudio.load(str(output_audio))
                print(f"  - Output shape: {audio.shape}")
                print(f"  - Sample rate: {sr}")
                print(f"  - Duration: {audio.shape[1] / sr:.2f}s")
                
                return True
            else:
                print("✗ Output file was not created")
                return False
                
        except Exception as e:
            print(f"✗ Demucs separation failed: {e}")
            return False

def main():
    """Run the simple Demucs test."""
    print("RockSmith Guitar Mute - Simple Demucs Test")
    print("=" * 45)
    
    try:
        success = test_demucs_separation()
        
        if success:
            print("\n✓ Simple Demucs test passed!")
            print("The Demucs integration is working correctly.")
        else:
            print("\n✗ Simple Demucs test failed!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()