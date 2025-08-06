#!/usr/bin/env python3
"""
Working PSARC handler using the correct rocksmith.psarc API.
"""

import logging
import tempfile
import zlib
from pathlib import Path
from typing import Dict, List, Optional
from io import BytesIO

from rocksmith import psarc

class WorkingPSARCHandler:
    """PSARC handler using the correct rocksmith.psarc API."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def extract_psarc(self, psarc_path: Path, output_dir: Path) -> bool:
        """
        Extract PSARC file using rocksmith.psarc.
        
        Args:
            psarc_path: Path to the PSARC file
            output_dir: Directory to extract files to
            
        Returns:
            True if extraction was successful
        """
        try:
            self.logger.info(f"Extracting PSARC: {psarc_path}")
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Read the PSARC file
            with open(psarc_path, 'rb') as f:
                psarc_data = f.read()
            
            self.logger.info(f"PSARC file size: {len(psarc_data)} bytes")
            
            # Decrypt the PSARC (Rocksmith PSARCs are encrypted)
            try:
                decrypted_data = psarc.decrypt_psarc(psarc_data)
                self.logger.info("✓ PSARC decrypted successfully")
            except Exception as e:
                self.logger.warning(f"Decryption failed, trying without decryption: {e}")
                decrypted_data = psarc_data
            
            # Parse the PSARC structure using BytesIO
            data_stream = BytesIO(decrypted_data)
            parsed_psarc = psarc.PSARC.parse_stream(data_stream)
            self.logger.info("✓ PSARC parsed successfully")
            
            # Extract entries
            file_count = 0
            audio_count = 0
            
            # The BOM (Bill of Materials) contains the file list
            if hasattr(parsed_psarc, 'bom') and parsed_psarc.bom:
                # Decrypt BOM if needed
                try:
                    bom_data = psarc.decrypt_bom(parsed_psarc.bom)
                    self.logger.info("✓ BOM decrypted")
                except:
                    bom_data = parsed_psarc.bom
                    self.logger.info("Using BOM without decryption")
                
                # Parse file names from BOM
                bom_str = bom_data.decode('utf-8', errors='ignore')
                file_names = [name.strip() for name in bom_str.split('\n') if name.strip()]
                self.logger.info(f"Found {len(file_names)} files in BOM")
                
                # Extract each entry
                for i, entry in enumerate(parsed_psarc.entries):
                    if i < len(file_names):
                        file_name = file_names[i]
                    else:
                        file_name = f"entry_{i:04d}.bin"
                    
                    # Read entry data
                    try:
                        entry_data = psarc.read_entry(decrypted_data, entry)
                        
                        # Create output path
                        output_file = output_dir / file_name.replace('\\', '/').strip('/')
                        output_file.parent.mkdir(parents=True, exist_ok=True)
                        
                        # Write file
                        with open(output_file, 'wb') as f:
                            f.write(entry_data)
                        
                        file_count += 1
                        
                        # Count audio files
                        if output_file.suffix.lower() in ['.ogg', '.wav', '.wem']:
                            audio_count += 1
                            self.logger.info(f"Extracted audio: {file_name} ({len(entry_data)} bytes)")
                        
                        self.logger.debug(f"Extracted: {file_name} ({len(entry_data)} bytes)")
                        
                    except Exception as e:
                        self.logger.warning(f"Failed to extract entry {i} ({file_name}): {e}")
            
            else:
                self.logger.warning("No BOM found, extracting entries by index")
                
                # Extract without file names
                for i, entry in enumerate(parsed_psarc.entries):
                    try:
                        entry_data = psarc.read_entry(decrypted_data, entry)
                        
                        # Try to determine file type from content
                        file_ext = ".bin"
                        if entry_data.startswith(b'OggS'):
                            file_ext = ".ogg"
                        elif entry_data.startswith(b'RIFF'):
                            file_ext = ".wav"
                        elif entry_data.startswith(b'<'):
                            file_ext = ".xml"
                        
                        file_name = f"entry_{i:04d}{file_ext}"
                        output_file = output_dir / file_name
                        
                        with open(output_file, 'wb') as f:
                            f.write(entry_data)
                        
                        file_count += 1
                        
                        if file_ext in ['.ogg', '.wav', '.wem']:
                            audio_count += 1
                            self.logger.info(f"Extracted audio: {file_name} ({len(entry_data)} bytes)")
                        
                    except Exception as e:
                        self.logger.warning(f"Failed to extract entry {i}: {e}")
            
            self.logger.info(f"Extraction completed: {file_count} files, {audio_count} audio files")
            return file_count > 0
            
        except Exception as e:
            self.logger.error(f"PSARC extraction failed: {e}")
            return False
    
    def create_psarc(self, source_dir: Path, output_psarc: Path) -> bool:
        """
        Create PSARC file from directory (simplified version).
        
        Args:
            source_dir: Directory containing files to pack
            output_psarc: Output PSARC file path
            
        Returns:
            True if creation was successful
        """
        try:
            self.logger.info(f"Creating PSARC: {output_psarc}")
            
            # For now, create a simple archive
            # A full PSARC implementation would be more complex
            
            # Collect files
            files = []
            bom_lines = []
            
            for file_path in source_dir.rglob("*"):
                if file_path.is_file():
                    rel_path = file_path.relative_to(source_dir)
                    file_name = str(rel_path).replace('\\', '/')
                    
                    with open(file_path, 'rb') as f:
                        data = f.read()
                    
                    files.append((file_name, data))
                    bom_lines.append(file_name)
            
            # Create BOM
            bom = '\n'.join(bom_lines).encode('utf-8')
            
            # For simplicity, create a basic structure
            # This is not a complete PSARC implementation
            with open(output_psarc, 'wb') as f:
                # Write simple header
                f.write(b'PSAR')  # Magic
                f.write(b'\x00\x01\x00\x04')  # Version
                f.write(b'zlib')  # Compression
                
                # Write placeholder data
                f.write(len(files).to_bytes(4, 'big'))
                
                # Write files (simplified)
                for file_name, data in files:
                    f.write(len(data).to_bytes(4, 'big'))
                    f.write(data)
            
            self.logger.info(f"PSARC created: {output_psarc} ({len(files)} files)")
            self.logger.warning("Note: This is a simplified PSARC format, may not be fully compatible")
            return True
            
        except Exception as e:
            self.logger.error(f"PSARC creation failed: {e}")
            return False

def test_working_psarc():
    """Test the working PSARC handler."""
    print("Testing working PSARC handler...")
    
    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    psarc_file = Path("sample/2minutes_p.psarc")
    if not psarc_file.exists():
        print(f"✗ PSARC file not found: {psarc_file}")
        return False
    
    handler = WorkingPSARCHandler()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        extract_dir = temp_path / "extracted"
        
        # Test extraction
        print("Testing PSARC extraction...")
        success = handler.extract_psarc(psarc_file, extract_dir)
        
        if success:
            print("✓ PSARC extraction successful!")
            
            # Count extracted files
            extracted_files = list(extract_dir.rglob("*"))
            extracted_file_count = len([f for f in extracted_files if f.is_file()])
            extracted_audio = [f for f in extracted_files if f.is_file() and f.suffix.lower() in ['.ogg', '.wav', '.wem']]
            
            print(f"  - Total files extracted: {extracted_file_count}")
            print(f"  - Audio files found: {len(extracted_audio)}")
            
            for audio_file in extracted_audio:
                size = audio_file.stat().st_size / (1024 * 1024)  # MB
                print(f"    📄 {audio_file.name}: {size:.2f} MB")
            
            # List some other files
            other_files = [f for f in extracted_files if f.is_file() and f.suffix.lower() not in ['.ogg', '.wav', '.wem']]
            if other_files:
                print(f"  - Other files: {len(other_files)}")
                for other_file in other_files[:5]:  # Show first 5
                    size = other_file.stat().st_size / 1024  # KB
                    print(f"    📄 {other_file.name}: {size:.1f} KB")
                if len(other_files) > 5:
                    print(f"    ... and {len(other_files) - 5} more")
            
            return True
        else:
            print("✗ PSARC extraction failed")
            return False

if __name__ == "__main__":
    success = test_working_psarc()
    if success:
        print("\n🎉 PSARC extraction working successfully!")
        print("We can now extract audio files from Rocksmith PSARC archives!")
    else:
        print("\n❌ PSARC extraction failed")