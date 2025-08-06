#!/usr/bin/env python3
"""
Convert OGG file to WAV for testing purposes.
"""

import sys
from pathlib import Path

def convert_ogg_to_wav():
    """Convert the OGG file to WAV."""
    ogg_file = Path("sample/2minutes.ogg")
    wav_file = Path("sample/2minutes.wav")
    
    if not ogg_file.exists():
        print(f"Error: OGG file not found: {ogg_file}")
        return False
    
    print(f"Converting {ogg_file} to {wav_file}...")
    
    try:
        # Try using soundfile first
        import soundfile as sf
        
        data, samplerate = sf.read(str(ogg_file))
        sf.write(str(wav_file), data, samplerate)
        
        print(f"✓ Conversion successful!")
        print(f"  - Input: {ogg_file} ({ogg_file.stat().st_size / 1024 / 1024:.2f} MB)")
        print(f"  - Output: {wav_file} ({wav_file.stat().st_size / 1024 / 1024:.2f} MB)")
        print(f"  - Sample rate: {samplerate} Hz")
        print(f"  - Channels: {data.shape[1] if len(data.shape) > 1 else 1}")
        print(f"  - Duration: {len(data) / samplerate:.2f} seconds")
        
        return True
        
    except ImportError:
        print("soundfile not available, trying alternative method...")
        
        try:
            # Try using torchaudio with different approach
            import torch
            import torchaudio
            
            # Try setting backend explicitly
            torchaudio.set_audio_backend("soundfile")
            
            waveform, sample_rate = torchaudio.load(str(ogg_file))
            torchaudio.save(str(wav_file), waveform, sample_rate)
            
            print(f"✓ Conversion successful with torchaudio!")
            return True
            
        except Exception as e:
            print(f"✗ Conversion failed: {e}")
            print("\nTrying FFmpeg approach...")
            
            # Try using subprocess with ffmpeg if available
            import subprocess
            
            try:
                result = subprocess.run([
                    "ffmpeg", "-i", str(ogg_file), "-acodec", "pcm_s16le", str(wav_file), "-y"
                ], capture_output=True, text=True, check=True)
                
                print(f"✓ Conversion successful with FFmpeg!")
                return True
                
            except (subprocess.CalledProcessError, FileNotFoundError) as e:
                print(f"✗ FFmpeg conversion failed: {e}")
                return False
    
    except Exception as e:
        print(f"✗ Conversion failed: {e}")
        return False

if __name__ == "__main__":
    success = convert_ogg_to_wav()
    sys.exit(0 if success else 1)