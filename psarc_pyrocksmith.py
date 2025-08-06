#!/usr/bin/env python3
"""
PSARC Handler using pyrocksmith library for proper PSARC manipulation.
"""

import logging
import tempfile
from pathlib import Path
from typing import Dict, List, Optional

try:
    from rocksmith import psarc
    PYROCKSMITH_AVAILABLE = True
except ImportError:
    PYROCKSMITH_AVAILABLE = False
    print("pyrocksmith not available, falling back to simple extraction")

class PyRocksmithPSARCHandler:
    """PSARC handler using the pyrocksmith library."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        if not PYROCKSMITH_AVAILABLE:
            raise ImportError("pyrocksmith library is required but not available")
    
    def extract_psarc(self, psarc_path: Path, output_dir: Path) -> bool:
        """
        Extract PSARC file using pyrocksmith.
        
        Args:
            psarc_path: Path to the PSARC file
            output_dir: Directory to extract files to
            
        Returns:
            True if extraction was successful
        """
        try:
            self.logger.info(f"Extracting PSARC with pyrocksmith: {psarc_path}")
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Open the PSARC file
            with PSARC.from_file(str(psarc_path)) as psarc:
                # Extract all files
                file_count = 0
                audio_count = 0
                
                for entry in psarc.entries:
                    # Get the file data
                    data = psarc.get_entry_data(entry)
                    
                    # Create output path (sanitize the entry name)
                    entry_name = entry.name.replace('\\', '/').strip('/')
                    output_file = output_dir / entry_name
                    
                    # Create parent directories
                    output_file.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Write the file
                    with open(output_file, 'wb') as f:
                        f.write(data)
                    
                    file_count += 1
                    
                    # Count audio files
                    if output_file.suffix.lower() in ['.ogg', '.wav', '.wem']:
                        audio_count += 1
                        self.logger.info(f"Extracted audio: {entry_name} ({len(data)} bytes)")
                    
                    self.logger.debug(f"Extracted: {entry_name} ({len(data)} bytes)")
                
                self.logger.info(f"Extraction completed: {file_count} files, {audio_count} audio files")
                return True
                
        except Exception as e:
            self.logger.error(f"PSARC extraction failed: {e}")
            return False
    
    def create_psarc(self, source_dir: Path, output_psarc: Path) -> bool:
        """
        Create PSARC file from directory.
        
        Args:
            source_dir: Directory containing files to pack
            output_psarc: Output PSARC file path
            
        Returns:
            True if creation was successful
        """
        try:
            self.logger.info(f"Creating PSARC: {output_psarc}")
            
            # Collect all files
            entries = []
            for file_path in source_dir.rglob("*"):
                if file_path.is_file():
                    # Get relative path from source_dir
                    rel_path = file_path.relative_to(source_dir)
                    entry_name = str(rel_path).replace('\\', '/')
                    
                    # Read file data
                    with open(file_path, 'rb') as f:
                        data = f.read()
                    
                    entries.append((entry_name, data))
                    self.logger.debug(f"Added: {entry_name} ({len(data)} bytes)")
            
            # Create PSARC
            with PSARC.create(str(output_psarc)) as psarc:
                for entry_name, data in entries:
                    psarc.add_entry(entry_name, data)
            
            self.logger.info(f"PSARC created: {output_psarc} ({len(entries)} files)")
            return True
            
        except Exception as e:
            self.logger.error(f"PSARC creation failed: {e}")
            return False
    
    def list_psarc_contents(self, psarc_path: Path) -> List[str]:
        """
        List contents of a PSARC file.
        
        Args:
            psarc_path: Path to the PSARC file
            
        Returns:
            List of file names in the archive
        """
        try:
            with PSARC.from_file(str(psarc_path)) as psarc:
                return [entry.name for entry in psarc.entries]
        except Exception as e:
            self.logger.error(f"Failed to list PSARC contents: {e}")
            return []

def test_pyrocksmith_psarc():
    """Test PSARC operations using pyrocksmith."""
    print("Testing PSARC operations with pyrocksmith...")
    
    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    if not PYROCKSMITH_AVAILABLE:
        print("✗ pyrocksmith library not available")
        return False
    
    psarc_file = Path("sample/2minutes_p.psarc")
    if not psarc_file.exists():
        print(f"✗ PSARC file not found: {psarc_file}")
        return False
    
    handler = PyRocksmithPSARCHandler()
    
    # Test listing contents first
    print("1. Listing PSARC contents...")
    contents = handler.list_psarc_contents(psarc_file)
    print(f"✓ Found {len(contents)} entries in PSARC")
    
    # Show some entries
    audio_files = [f for f in contents if any(f.lower().endswith(ext) for ext in ['.ogg', '.wav', '.wem'])]
    other_files = [f for f in contents if f not in audio_files]
    
    print(f"  - Audio files: {len(audio_files)}")
    for audio_file in audio_files[:5]:  # Show first 5
        print(f"    {audio_file}")
    if len(audio_files) > 5:
        print(f"    ... and {len(audio_files) - 5} more")
    
    print(f"  - Other files: {len(other_files)}")
    for other_file in other_files[:5]:  # Show first 5
        print(f"    {other_file}")
    if len(other_files) > 5:
        print(f"    ... and {len(other_files) - 5} more")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        extract_dir = temp_path / "extracted"
        
        # Test extraction
        print("\n2. Testing PSARC extraction...")
        success = handler.extract_psarc(psarc_file, extract_dir)
        
        if success:
            print("✓ PSARC extraction successful")
            
            # Count extracted files
            extracted_files = list(extract_dir.rglob("*"))
            extracted_file_count = len([f for f in extracted_files if f.is_file()])
            extracted_audio = [f for f in extracted_files if f.is_file() and f.suffix.lower() in ['.ogg', '.wav', '.wem']]
            
            print(f"  - Extracted {extracted_file_count} files")
            print(f"  - Audio files: {len(extracted_audio)}")
            
            for audio_file in extracted_audio:
                size = audio_file.stat().st_size / (1024 * 1024)  # MB
                print(f"    {audio_file.name}: {size:.2f} MB")
            
            # Test repacking
            print("\n3. Testing PSARC repacking...")
            output_psarc = temp_path / "repacked.psarc"
            repack_success = handler.create_psarc(extract_dir, output_psarc)
            
            if repack_success:
                print("✓ PSARC repacking successful")
                original_size = psarc_file.stat().st_size / (1024 * 1024)  # MB
                repacked_size = output_psarc.stat().st_size / (1024 * 1024)  # MB
                print(f"  - Original size: {original_size:.2f} MB")
                print(f"  - Repacked size: {repacked_size:.2f} MB")
                print(f"  - Size difference: {repacked_size - original_size:+.2f} MB")
                return True
            else:
                print("✗ PSARC repacking failed")
                return False
        else:
            print("✗ PSARC extraction failed")
            return False

if __name__ == "__main__":
    success = test_pyrocksmith_psarc()
    if success:
        print("\n✓ All PSARC operations completed successfully!")
        print("The pyrocksmith library is working correctly for PSARC manipulation.")
    else:
        print("\n✗ PSARC operations failed!")