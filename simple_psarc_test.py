#!/usr/bin/env python3
"""
Simple test to extract files from PSARC using available functions.
"""

import logging
from pathlib import Path
from rocksmith import psarc
import struct

def simple_psarc_extract():
    """Simple PSARC extraction test."""
    print("Simple PSARC extraction test...")
    
    psarc_file = Path("sample/2minutes_p.psarc")
    if not psarc_file.exists():
        print(f"✗ PSARC file not found: {psarc_file}")
        return False
    
    try:
        # Read the PSARC file
        with open(psarc_file, 'rb') as f:
            data = f.read()
        
        print(f"File size: {len(data)} bytes")
        print(f"First 16 bytes: {data[:16].hex()}")
        
        # Try to decrypt the PSARC
        try:
            print("Attempting decryption...")
            decrypted = psarc.decrypt_psarc(data)
            print(f"✓ Decryption successful, size: {len(decrypted)} bytes")
            working_data = decrypted
        except Exception as e:
            print(f"⚠ Decryption failed: {e}")
            print("Trying without decryption...")
            working_data = data
        
        # Parse header manually
        if working_data[:4] != b'PSAR':
            print("✗ Invalid PSARC header")
            return False
        
        print("✓ Valid PSARC header found")
        
        # Read header fields
        version_major, version_minor = struct.unpack('>HH', working_data[4:8])
        compression = working_data[8:12]
        toc_length = struct.unpack('>I', working_data[12:16])[0]
        
        print(f"Version: {version_major}.{version_minor}")
        print(f"Compression: {compression}")
        print(f"TOC Length: {toc_length}")
        
        # Try to read TOC
        toc_start = 32  # Header is 32 bytes
        toc_data = working_data[toc_start:toc_start + toc_length]
        
        print(f"TOC data length: {len(toc_data)} bytes")
        
        # Try to decrypt TOC
        try:
            print("Attempting TOC decryption...")
            decrypted_toc = psarc.decrypt_bom(toc_data)
            print(f"✓ TOC decryption successful")
            
            # Try to parse as text
            try:
                toc_text = decrypted_toc.decode('utf-8', errors='ignore')
                lines = [line.strip() for line in toc_text.split('\n') if line.strip()]
                print(f"✓ Found {len(lines)} file entries:")
                
                # Show audio files
                audio_files = [line for line in lines if any(line.lower().endswith(ext) for ext in ['.ogg', '.wav', '.wem'])]
                print(f"  Audio files ({len(audio_files)}):")
                for audio_file in audio_files:
                    print(f"    📄 {audio_file}")
                
                # Show other files (first 10)
                other_files = [line for line in lines if line not in audio_files]
                print(f"  Other files ({len(other_files)}):")
                for other_file in other_files[:10]:
                    print(f"    📄 {other_file}")
                if len(other_files) > 10:
                    print(f"    ... and {len(other_files) - 10} more")
                
                return True
                
            except Exception as e:
                print(f"✗ Failed to parse TOC as text: {e}")
                print(f"TOC starts with: {decrypted_toc[:50]}")
                return False
            
        except Exception as e:
            print(f"⚠ TOC decryption failed: {e}")
            
            # Try to parse without decryption
            try:
                toc_text = toc_data.decode('utf-8', errors='ignore')
                if toc_text.strip():
                    lines = [line.strip() for line in toc_text.split('\n') if line.strip()]
                    print(f"✓ Parsed TOC without decryption: {len(lines)} entries")
                    return True
                else:
                    print("✗ TOC doesn't appear to be text")
                    return False
            except:
                print("✗ Failed to parse TOC as text")
                return False
    
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

if __name__ == "__main__":
    success = simple_psarc_extract()
    if success:
        print("\n✅ Successfully analyzed PSARC structure!")
    else:
        print("\n❌ Failed to analyze PSARC structure")