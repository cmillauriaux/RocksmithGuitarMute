#!/usr/bin/env python3
"""
Test script for guitar extraction from offegalo_p.psarc
This script will:
1. Extract WEM files from the PSARC
2. Convert WEM to WAV
3. Use Demucs htdemucs_6s to separate sources
4. Extract and save the guitar track as WAV
"""

import logging
import shutil
import tempfile
from pathlib import Path
import sys

# Add current directory to path for imports
sys.path.insert(0, str(Path.cwd()))

from rocksmith_guitar_mute import RocksmithGuitarMute

def setup_logging():
    """Setup logging for the test script."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('test_guitar_extraction.log')
        ]
    )

def test_guitar_extraction():
    """Test guitar extraction from offegalo_p.psarc."""
    logger = logging.getLogger(__name__)
    
    # Input and output paths
    input_psarc = Path("input/offegalo_p.psarc")
    test_output_dir = Path("test_output")
    guitar_output_dir = Path("test_output_guitar")
    
    # Verify input file exists
    if not input_psarc.exists():
        logger.error(f"Input file not found: {input_psarc}")
        return False
    
    # Create output directories
    test_output_dir.mkdir(exist_ok=True)
    guitar_output_dir.mkdir(exist_ok=True)
    
    logger.info(f"Starting guitar extraction test with {input_psarc}")
    
    try:
        # Initialize processor with htdemucs_6s model
        processor = RocksmithGuitarMute(demucs_model="htdemucs_6s", device="auto")
        
        # Create temporary directory for extraction
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            extract_dir = temp_path / "extracted"
            
            logger.info("Step 1: Unpacking PSARC...")
            processor.unpack_psarc(input_psarc, extract_dir)
            
            logger.info("Step 2: Finding audio files...")
            audio_files = processor.find_audio_files(extract_dir)
            
            if not audio_files:
                logger.error("No audio files found in PSARC")
                return False
            
            # Process each audio file
            for i, audio_file in enumerate(audio_files):
                logger.info(f"Step 3.{i+1}: Processing {audio_file.name}")
                
                if audio_file.suffix.lower() == '.wem':
                    # Convert WEM to WAV
                    wav_file = guitar_output_dir / f"{audio_file.stem}.wav"
                    logger.info(f"Converting WEM to WAV: {wav_file.name}")
                    processor.convert_wem_to_wav(audio_file, wav_file)
                    
                    # Apply Demucs separation and save guitar track
                    logger.info(f"Extracting guitar track with htdemucs_6s...")
                    backing_track_path = guitar_output_dir / f"{audio_file.stem}_backing.wav"
                    processor.remove_guitar_track(wav_file, backing_track_path, save_guitar=True)
                    
                    logger.info(f"Guitar extraction completed for {audio_file.name}")
                    logger.info(f"  - Original: {wav_file}")
                    logger.info(f"  - Backing track: {backing_track_path}")
                    logger.info(f"  - Guitar track: {backing_track_path.with_name(f'{backing_track_path.stem}_guitar.wav')}")
                    
                elif audio_file.suffix.lower() in ['.ogg', '.wav']:
                    # Copy to output directory and process
                    output_audio = guitar_output_dir / audio_file.name
                    shutil.copy2(audio_file, output_audio)
                    
                    # Apply Demucs separation and save guitar track
                    logger.info(f"Extracting guitar track with htdemucs_6s...")
                    backing_track_path = guitar_output_dir / f"{audio_file.stem}_backing{audio_file.suffix}"
                    processor.remove_guitar_track(output_audio, backing_track_path, save_guitar=True)
                    
                    logger.info(f"Guitar extraction completed for {audio_file.name}")
                    logger.info(f"  - Original: {output_audio}")
                    logger.info(f"  - Backing track: {backing_track_path}")
                    logger.info(f"  - Guitar track: {backing_track_path.with_name(f'{backing_track_path.stem}_guitar{audio_file.suffix}')}")
        
        # List all output files
        logger.info("\n=== Guitar Extraction Test Results ===")
        logger.info(f"Output directory: {guitar_output_dir}")
        output_files = list(guitar_output_dir.glob("*"))
        
        if output_files:
            logger.info("Generated files:")
            for file_path in sorted(output_files):
                file_size = file_path.stat().st_size / (1024 * 1024)  # MB
                logger.info(f"  - {file_path.name} ({file_size:.2f} MB)")
        else:
            logger.warning("No output files generated")
            return False
        
        logger.info("\n=== Test completed successfully! ===")
        logger.info(f"You can find the extracted guitar tracks in: {guitar_output_dir}")
        return True
        
    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main entry point for the test script."""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("Starting Rocksmith Guitar Extraction Test")
    logger.info("This will extract guitar tracks from offegalo_p.psarc using htdemucs_6s")
    
    success = test_guitar_extraction()
    
    if success:
        print("\n✅ Guitar extraction test completed successfully!")
        print("Check the test_output_guitar/ directory for the extracted files.")
    else:
        print("\n❌ Guitar extraction test failed!")
        print("Check the test_guitar_extraction.log file for details.")
        sys.exit(1)

if __name__ == "__main__":
    main()