#!/usr/bin/env python3
"""
Example script to run RockSmith Guitar Mute with the sample file.

This script demonstrates how to use the RockSmith Guitar Mute tool
with the provided sample PSARC file.
"""

import subprocess
import sys
from pathlib import Path

def main():
    """Run the example with the sample file."""
    print("RockSmith Guitar Mute - Example Run")
    print("=" * 40)
    
    # Check if sample file exists
    sample_file = Path("sample/2minutes_p.psarc")
    if not sample_file.exists():
        print(f"Error: Sample file not found: {sample_file}")
        print("Please ensure the sample file is in the correct location.")
        sys.exit(1)
    
    # Create output directory
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    # Run the main script
    cmd = [
        sys.executable, "rocksmith_guitar_mute.py",
        str(sample_file),
        str(output_dir),
        "--verbose"
    ]
    
    print(f"Running command: {' '.join(cmd)}")
    print()
    
    try:
        result = subprocess.run(cmd, check=True)
        print("\n" + "=" * 40)
        print("✓ Example run completed successfully!")
        print(f"Check the '{output_dir}' directory for the processed file.")
    except subprocess.CalledProcessError as e:
        print(f"\n✗ Example run failed with exit code {e.returncode}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n⚠ Example run interrupted by user")
        sys.exit(1)

if __name__ == "__main__":
    main()