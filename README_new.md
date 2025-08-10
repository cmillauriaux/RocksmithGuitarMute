# Rocksmith Guitar Mute

🎸 **Automated tool for removing guitar tracks from Rocksmith 2014 Custom DLC (CDLC) files using AI-powered source separation.**

## Overview

This tool processes Rocksmith 2014 PSARC files to remove guitar tracks, creating backing tracks perfect for practice or jamming. The output PSARC file retains the same filename and structure as the original.

### Workflow

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Unpack PSARC  │ -> │ Extract & Convert│ -> │ Remove Guitar   │ -> │  Repack PSARC   │
│   (rsrtools)    │    │ WEM→WAV (rs-utils)│   │   (Demucs AI)   │    │   (rsrtools)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Features

✅ **Complete automation** - Single command processing  
✅ **Preserves original structure** - Same filename and PSARC format  
✅ **High-quality AI separation** - Uses Demucs hybrid transformer model  
✅ **Real WEM conversion** - Proper Wwise audio format handling  
✅ **Cross-platform** - Windows, macOS, Linux support  

## Requirements

### System Requirements
- **Python 3.8+**
- **FFmpeg** (for audio conversion)
- **Wwise Authoring Tool** (for WEM conversion)

### Python Dependencies
```bash
pip install -r requirements.txt
```

### External Tools
This project uses:
- **rsrtools** - PSARC file handling (included)
- **rs-utils** - Audio conversion tools (included)

## Installation

1. **Clone the repository:**
```bash
git clone https://github.com/your-username/rocksmith-guitar-mute.git
cd rocksmith-guitar-mute
```

2. **Install Python dependencies:**
```bash
pip install -r requirements.txt
```

3. **Install FFmpeg:**
   - **Windows:** Download from [ffmpeg.org](https://ffmpeg.org/download.html)
   - **macOS:** `brew install ffmpeg`
   - **Linux:** `sudo apt install ffmpeg`

4. **Install Wwise Authoring Tool:**
   - Download from [Audiokinetic Wwise](https://www.audiokinetic.com/products/wwise/)
   - Required for WEM audio format conversion

## Usage

### Basic Usage
```bash
python rocksmith_guitar_mute.py input.psarc output_directory/
```

### Process Multiple Files
```bash
python rocksmith_guitar_mute.py input_folder/ output_directory/
```

### Options
```bash
python rocksmith_guitar_mute.py input.psarc output/ --device cuda --verbose
```

**Parameters:**
- `input_path`: Path to PSARC file or directory containing PSARC files
- `output_directory`: Directory where processed files will be saved
- `--device`: Processing device (`cpu`, `cuda`, `mps`) - default: auto-detect
- `--verbose`: Enable detailed logging

## Examples

**Process single CDLC:**
```bash
python rocksmith_guitar_mute.py "My Song_p.psarc" "./output/"
# Creates: ./output/My Song_p.psarc (without guitar)
```

**Process multiple CDLCs:**
```bash
python rocksmith_guitar_mute.py "./cdlc_folder/" "./backing_tracks/"
# Processes all PSARC files in cdlc_folder/
```

## How It Works

1. **PSARC Extraction**: Uses `rsrtools` to extract all files from the Rocksmith PSARC archive
2. **Audio Conversion**: Converts WEM audio files to WAV using `rs-utils` and FFmpeg
3. **AI Source Separation**: Demucs AI separates the audio into stems (drums, bass, vocals, other)
4. **Guitar Removal**: Combines all stems except "other" (which contains guitar/lead instruments)
5. **WEM Conversion**: Converts processed WAV back to WEM using Wwise authoring tools
6. **PSARC Repacking**: Creates new PSARC with modified audio using `rsrtools`

## Technical Details

### Audio Processing
- **Input formats**: WEM, OGG, WAV
- **AI Model**: Demucs `htdemucs` (hybrid transformer)
- **Separation quality**: Professional-grade source separation
- **Output format**: WEM (Wwise Encoded Media)

### File Handling
- **PSARC extraction/creation**: rsrtools welder
- **Audio conversion**: rs-utils ww2ogg/revorb, FFmpeg
- **WEM generation**: Wwise authoring tools

## Troubleshooting

### Common Issues

**"FFmpeg not found"**
- Install FFmpeg and ensure it's in your system PATH

**"WwiseCLI.exe not found"**
- Install Wwise Authoring Tool from Audiokinetic

**"PSARC extraction failed"**
- Ensure the input file is a valid Rocksmith 2014 PSARC
- Check file permissions

**"Out of memory"**
- Use `--device cpu` for large files
- Ensure sufficient RAM (4GB+ recommended)

## License

This project is for educational and personal use. Ensure you have the right to modify any CDLC files you process.

## Contributing

Contributions welcome! Please read the contribution guidelines and submit pull requests for any improvements.

## Credits

- **Demucs**: Facebook Research - AI source separation
- **rsrtools**: PSARC file handling
- **rs-utils**: Rocksmith audio tools
- **Rocksmith 2014**: Ubisoft