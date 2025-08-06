#!/usr/bin/env python3
"""
Deep analysis of PSARC structure to understand the real format.
"""

import logging
import struct
import zlib
from pathlib import Path
from rocksmith import psarc

def analyze_psarc_structure():
    """Analyze PSARC structure in detail."""
    print("=== DEEP PSARC ANALYSIS ===")
    
    psarc_file = Path("sample/2minutes_p.psarc")
    if not psarc_file.exists():
        print(f"✗ PSARC file not found: {psarc_file}")
        return False
    
    with open(psarc_file, 'rb') as f:
        data = f.read()
    
    print(f"File size: {len(data)} bytes")
    
    # Parse header manually
    if data[:4] != b'PSAR':
        print("✗ Invalid PSARC header")
        return False
    
    # Header structure (32 bytes total)
    magic = data[0:4]           # 'PSAR'
    version_major = struct.unpack('>H', data[4:6])[0]
    version_minor = struct.unpack('>H', data[6:8])[0]
    compression = data[8:12]    # 'zlib'
    toc_length = struct.unpack('>I', data[12:16])[0]
    toc_entry_size = struct.unpack('>I', data[16:20])[0]
    toc_entry_count = struct.unpack('>I', data[20:24])[0]
    block_size = struct.unpack('>I', data[24:28])[0]
    archive_flags = struct.unpack('>I', data[28:32])[0]
    
    print(f"\n=== HEADER ===")
    print(f"Magic: {magic}")
    print(f"Version: {version_major}.{version_minor}")
    print(f"Compression: {compression}")
    print(f"TOC Length: {toc_length}")
    print(f"TOC Entry Size: {toc_entry_size}")
    print(f"TOC Entry Count: {toc_entry_count}")
    print(f"Block Size: {block_size}")
    print(f"Archive Flags: {archive_flags:08x}")
    
    # Check if encrypted
    is_encrypted = bool(archive_flags & 4)
    print(f"Is Encrypted: {is_encrypted}")
    
    # TOC starts at offset 32
    toc_data = data[32:32 + toc_length]
    print(f"\nTOC Data (first 64 bytes): {toc_data[:64].hex()}")
    
    # Try to decrypt TOC if encrypted
    if is_encrypted:
        try:
            print("\n=== DECRYPTING TOC ===")
            decrypted_toc = psarc.decrypt_bom(toc_data)
            print(f"✓ TOC decrypted successfully, size: {len(decrypted_toc)}")
            print(f"Decrypted TOC (first 64 bytes): {decrypted_toc[:64].hex()}")
            
            # The TOC contains entry table + BOM
            # Entry table: toc_entry_count * toc_entry_size bytes
            entries_size = toc_entry_count * toc_entry_size
            
            print(f"\nEntries table size: {entries_size} bytes")
            print(f"BOM size: {len(decrypted_toc) - entries_size} bytes")
            
            # Parse entries
            entries = []
            for i in range(toc_entry_count):
                offset = i * toc_entry_size
                entry_data = decrypted_toc[offset:offset + toc_entry_size]
                
                # Entry structure (30 bytes typically)
                if len(entry_data) >= 30:
                    # Parse entry fields
                    filename_hash = entry_data[0:16]  # MD5 hash of filename
                    zindex_begin = struct.unpack('>I', entry_data[16:20])[0]
                    length = struct.unpack('>Q', b'\x00\x00\x00\x00' + entry_data[20:24])[0]  # 40-bit length
                    offset_val = struct.unpack('>Q', b'\x00\x00\x00\x00' + entry_data[24:28])[0]  # 40-bit offset
                    
                    entries.append({
                        'hash': filename_hash.hex(),
                        'zindex_begin': zindex_begin,
                        'length': length,
                        'offset': offset_val,
                        'raw': entry_data.hex()
                    })
            
            print(f"\n=== ENTRIES ({len(entries)}) ===")
            for i, entry in enumerate(entries):
                print(f"Entry {i}:")
                print(f"  Hash: {entry['hash']}")
                print(f"  Z-Index: {entry['zindex_begin']}")
                print(f"  Length: {entry['length']}")
                print(f"  Offset: {entry['offset']}")
                print(f"  Raw: {entry['raw']}")
                print()
            
            # Extract BOM (Bill of Materials = filename list)
            bom_data = decrypted_toc[entries_size:]
            print(f"=== BOM DATA ===")
            print(f"BOM size: {len(bom_data)} bytes")
            print(f"BOM (hex): {bom_data.hex()}")
            
            # Try different ways to decode BOM
            print(f"\n=== BOM DECODING ATTEMPTS ===")
            
            # 1. Direct UTF-8
            try:
                bom_utf8 = bom_data.decode('utf-8', errors='replace')
                print(f"UTF-8: {repr(bom_utf8)}")
                lines = [line for line in bom_utf8.split('\n') if line.strip()]
                if lines:
                    print(f"Lines found: {len(lines)}")
                    for line in lines[:5]:
                        print(f"  '{line}'")
            except Exception as e:
                print(f"UTF-8 failed: {e}")
            
            # 2. Maybe it's compressed?
            try:
                decompressed = zlib.decompress(bom_data)
                print(f"\nDecompressed BOM size: {len(decompressed)}")
                bom_text = decompressed.decode('utf-8', errors='replace')
                print(f"Decompressed text: {repr(bom_text[:200])}")
                lines = [line for line in bom_text.split('\n') if line.strip()]
                print(f"Decompressed lines: {len(lines)}")
                for line in lines[:10]:
                    print(f"  '{line}'")
                
                return True
                
            except Exception as e:
                print(f"Decompression failed: {e}")
            
            # 3. Maybe there's a different encoding?
            encodings = ['latin-1', 'cp1252', 'utf-16', 'utf-16le', 'utf-16be']
            for encoding in encodings:
                try:
                    bom_text = bom_data.decode(encoding, errors='replace')
                    if bom_text.isprintable():
                        print(f"\n{encoding}: {repr(bom_text[:100])}")
                except:
                    pass
            
        except Exception as e:
            print(f"✗ TOC decryption failed: {e}")
            return False
    
    else:
        print("Archive is not encrypted, parsing directly...")
        # Handle unencrypted PSARC
    
    return False

if __name__ == "__main__":
    analyze_psarc_structure()