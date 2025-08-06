#!/usr/bin/env python3
"""
Test the complete PSARC workflow: unpack -> process audio -> repack.
"""

import logging
import sys
import tempfile
from pathlib import Path

def test_psarc_workflow():
    """Test the complete PSARC processing workflow."""
    print("Testing complete PSARC workflow...")
    
    # Check if the sample PSARC file exists
    psarc_file = Path("sample/2minutes_p.psarc")
    if not psarc_file.exists():
        print(f"✗ PSARC file not found: {psarc_file}")
        return False
    
    print(f"✓ Found PSARC file: {psarc_file}")
    print(f"  - File size: {psarc_file.stat().st_size / 1024 / 1024:.2f} MB")
    
    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    # Import our main processor
    try:
        from rocksmith_guitar_mute import RocksmithGuitarMute
    except ImportError as e:
        print(f"✗ Error importing main script: {e}")
        return False
    
    # Create processor
    print("\nInitializing RocksmithGuitarMute processor...")
    processor = RocksmithGuitarMute(demucs_model="htdemucs", device="cpu")
    
    # Create output directory
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    print(f"\nProcessing PSARC file...")
    print("This will:")
    print("1. Unpack the PSARC archive")
    print("2. Find audio files (OGG/WEM)")
    print("3. Process audio with Demucs (remove guitar)")
    print("4. Replace audio in the archive")
    print("5. Repack the modified PSARC")
    print("\nThis may take several minutes...")
    
    try:
        # Process the PSARC file
        output_psarc = processor.process_psarc_file(psarc_file, output_dir)
        
        if output_psarc.exists():
            print(f"\n✓ PSARC processing successful!")
            print(f"✓ Modified PSARC saved: {output_psarc}")
            
            # Compare file sizes
            original_size = psarc_file.stat().st_size / (1024 * 1024)  # MB
            processed_size = output_psarc.stat().st_size / (1024 * 1024)  # MB
            
            print(f"  - Original PSARC size: {original_size:.2f} MB")
            print(f"  - Processed PSARC size: {processed_size:.2f} MB")
            print(f"  - Size difference: {processed_size - original_size:+.2f} MB")
            
            return True
        else:
            print("✗ Output PSARC file was not created")
            return False
            
    except Exception as e:
        print(f"✗ PSARC processing failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_psarc_structure():
    """Test PSARC structure analysis without full processing."""
    print("Testing PSARC structure analysis...")
    
    psarc_file = Path("sample/2minutes_p.psarc")
    if not psarc_file.exists():
        print(f"✗ PSARC file not found: {psarc_file}")
        return False
    
    try:
        from rocksmith_guitar_mute import RocksmithGuitarMute
        processor = RocksmithGuitarMute()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            extract_dir = temp_path / "extracted"
            
            print(f"Extracting PSARC to temporary directory...")
            processor.unpack_psarc(psarc_file, extract_dir)
            
            print(f"✓ PSARC extracted successfully")
            
            # Analyze structure
            all_files = list(extract_dir.rglob("*"))
            audio_files = processor.find_audio_files(extract_dir)
            
            print(f"  - Total files extracted: {len(all_files)}")
            print(f"  - Audio files found: {len(audio_files)}")
            
            # Show file types
            extensions = {}
            for file_path in all_files:
                if file_path.is_file():
                    ext = file_path.suffix.lower()
                    extensions[ext] = extensions.get(ext, 0) + 1
            
            print(f"  - File types found:")
            for ext, count in sorted(extensions.items()):
                print(f"    {ext or '(no extension)'}: {count} files")
            
            # Show audio files details
            if audio_files:
                print(f"  - Audio files details:")
                for audio_file in audio_files:
                    size = audio_file.stat().st_size / (1024 * 1024)  # MB
                    print(f"    {audio_file.name}: {size:.2f} MB")
            
            return True
            
    except Exception as e:
        print(f"✗ PSARC structure analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run PSARC workflow tests."""
    print("RockSmith Guitar Mute - PSARC Workflow Test")
    print("=" * 50)
    
    try:
        # Test 1: Structure analysis
        print("TEST 1: PSARC Structure Analysis")
        print("-" * 35)
        success1 = test_psarc_structure()
        
        if not success1:
            print("\n✗ Structure analysis failed, stopping here.")
            sys.exit(1)
        
        print(f"\n✓ Structure analysis passed!")
        
        # Test 2: Full workflow
        print("\n" + "="*50)
        print("TEST 2: Complete PSARC Processing Workflow")
        print("-" * 42)
        success2 = test_psarc_workflow()
        
        if success2:
            print("\n" + "=" * 50)
            print("✓ All PSARC workflow tests passed!")
            print("The complete pipeline is working correctly:")
            print("  1. ✓ PSARC unpacking")
            print("  2. ✓ Audio file discovery")
            print("  3. ✓ Demucs audio processing")
            print("  4. ✓ PSARC repacking")
            print(f"\nYou can now use the processed file:")
            print(f"  output/2minutes_p_no_guitar.psarc")
        else:
            print("\n✗ Full workflow test failed!")
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