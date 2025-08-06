#!/bin/bash

# Bash script to run RockSmith Guitar Mute example on Linux/macOS

echo "RockSmith Guitar Mute - Example Run (Linux/macOS)"
echo "================================================="

# Check if Python is available
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "✗ Python not found. Please install Python 3.8+"
    exit 1
fi

PYTHON_VERSION=$($PYTHON_CMD --version)
echo "✓ Python found: $PYTHON_VERSION"

# Check if sample file exists
SAMPLE_FILE="sample/2minutes_p.psarc"
if [ ! -f "$SAMPLE_FILE" ]; then
    echo "✗ Sample file not found: $SAMPLE_FILE"
    echo "Please ensure the sample file is in the correct location."
    exit 1
fi

# Create output directory
OUTPUT_DIR="output"
mkdir -p "$OUTPUT_DIR"

# Run the main script
CMD="$PYTHON_CMD rocksmith_guitar_mute.py $SAMPLE_FILE $OUTPUT_DIR --verbose"
echo "Running command: $CMD"
echo ""

if $PYTHON_CMD rocksmith_guitar_mute.py "$SAMPLE_FILE" "$OUTPUT_DIR" --verbose; then
    echo ""
    echo "================================================="
    echo "✓ Example run completed successfully!"
    echo "Check the '$OUTPUT_DIR' directory for the processed file."
else
    echo "✗ Example run failed with exit code $?"
    exit 1
fi