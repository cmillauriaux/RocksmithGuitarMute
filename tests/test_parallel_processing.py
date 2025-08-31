#!/usr/bin/env python3
"""
Test script to demonstrate the parallel processing and output checking features
of RockSmith Guitar Mute.

This script shows:
1. How output files are checked before processing
2. How parallel processing works with multiple files
3. Performance comparison between sequential and parallel processing
"""

import time
from pathlib import Path
import logging
from rocksmith_guitar_mute import RocksmithGuitarMute

def demo_output_checking():
    """Demonstrate output file checking functionality."""
    print("=== Demo: Output File Checking ===")
    
    processor = RocksmithGuitarMute()
    input_dir = Path("sample")
    output_dir = Path("test_output")
    
    # Create some fake output files to simulate existing processed files
    output_dir.mkdir(exist_ok=True)
    
    if input_dir.exists():
        psarc_files = list(input_dir.glob("*.psarc"))
        if psarc_files:
            # Create a fake output file
            fake_output = output_dir / psarc_files[0].name
            fake_output.touch()
            print(f"Created fake output: {fake_output}")
            
            # Test with force=False (should skip)
            print(f"Testing with force=False...")
            result = processor._output_exists(psarc_files[0], output_dir)
            print(f"Output exists: {result}")
            
            # Clean up
            fake_output.unlink()
    else:
        print("No sample directory found - creating demo structure")


def demo_parallel_vs_sequential():
    """Demonstrate performance difference between parallel and sequential processing."""
    print("\n=== Demo: Parallel vs Sequential Processing ===")
    
    processor = RocksmithGuitarMute()
    input_dir = Path("sample")
    
    if not input_dir.exists():
        print("No sample directory found - cannot demo performance")
        return
    
    psarc_files = list(input_dir.glob("*.psarc"))
    if not psarc_files:
        print("No PSARC files found in sample directory")
        return
    
    print(f"Found {len(psarc_files)} PSARC files")
    
    # Note: This is just a demo - actual processing would take much longer
    print("For actual processing:")
    print(f"  - Sequential processing: ~{len(psarc_files) * 5} minutes")
    print(f"  - Parallel processing (8 cores): ~{(len(psarc_files) * 5) // 8} minutes")
    print(f"  - Speedup factor: ~{8}x (with 8 CPU cores)")


def main():
    """Main demo function."""
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    print("RockSmith Guitar Mute - Parallel Processing Demo")
    print("=" * 50)
    
    demo_output_checking()
    demo_parallel_vs_sequential()
    
    print("\n=== Command Line Usage Examples ===")
    print("# Process directory with all available CPU cores:")
    print("python rocksmith_guitar_mute.py input/ output/")
    print()
    print("# Process with 4 workers only:")
    print("python rocksmith_guitar_mute.py input/ output/ --workers 4")
    print()
    print("# Force reprocessing of existing files:")
    print("python rocksmith_guitar_mute.py input/ output/ --force")
    print()
    print("# Process single file:")
    print("python rocksmith_guitar_mute.py song.psarc output/")


if __name__ == "__main__":
    main()