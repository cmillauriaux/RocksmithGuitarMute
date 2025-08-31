# RockSmithGuitarMute

A tool for processing Rocksmith 2014 PSARC files to remove guitar tracks from audio using AI-powered source separation.

## Overview

This project automates the process of unpacking Rocksmith 2014 PSARC files, extracting audio tracks, removing guitar parts using AI source separation, and repacking the modified files. This is useful for creating backing tracks or practicing with different instrumental arrangements.

## Features

### ✨ **Performance Optimizations**
- **Automatic Output Checking**: Skips files that have already been processed (unless `--force` is used)
- **Parallel Processing**: Utilizes all CPU cores for maximum performance (one file per core)
- **Configurable Workers**: Control the number of parallel workers with `--workers` option

### Processing Pipeline

The workflow consists of four main steps with parallel execution support:

```
                     ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
         File 1  ->  │   Unpack PSARC  │ -> │  Extract Audio  │ -> │ Remove Guitar   │ -> │  Repack PSARC   │
                     └─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
                     
                     ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
         File 2  ->  │   Unpack PSARC  │ -> │  Extract Audio  │ -> │ Remove Guitar   │ -> │  Repack PSARC   │
                     └─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
                     
                     ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
         File N  ->  │   Unpack PSARC  │ -> │  Extract Audio  │ -> │ Remove Guitar   │ -> │  Repack PSARC   │
                     └─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
                               ↑
                    Parallel processing (up to number of CPU cores)
```

### 1. Unpack PSARC Files
Extract the contents of Rocksmith 2014 PSARC archives:
- Reading and writing PSARC archives
- Handling Rocksmith 2014 file formats (SNG, XML, audio files)
- Managing DLC project structures

### 2. Extract Audio
Audio conversion and extraction:
- Supports various audio formats (WAV, OGG, WEM)
- Handles Wwise audio conversion
- Maintains audio quality and metadata

### 3. Remove Guitar Track
Using **Demucs** (v4) - a state-of-the-art AI music source separation model:
- Separates audio into stems: drums, bass, vocals, and other instruments
- Uses Hybrid Transformer architecture for high-quality separation
- Achieves 9.00+ dB SDR (Signal-to-Distortion Ratio) on test sets
- Removes guitar/lead instrument while preserving other musical elements

### 4. Repack PSARC
Reconstruct the PSARC file with the modified audio:
- Replace original audio with processed backing track
- Maintain file structure and metadata integrity
- Ensure compatibility with Rocksmith 2014

## Components

This project uses several external libraries as Git submodules:

### Demucs
Located in `./demucs/` (submodule from [adefossez/demucs](https://github.com/adefossez/demucs))

Facebook Research's advanced music source separation model:

- **Version 4**: Hybrid Transformer-based architecture
- **Multi-source separation**: Drums, bass, vocals, and other instruments
- **High quality**: State-of-the-art separation performance
- **Flexible**: Supports various audio formats and processing options

### RSRTools
Located in `./rsrtools/` (submodule from [BuongiornoTexas/rsrtools](https://github.com/BuongiornoTexas/rsrtools))

Tools for creating Rocksmith 2014 songlists and managing Rocksmith save files:

- **PSARC handling**: Extract, list, pack, unpack, and verify PSARC files
- **Profile management**: Manage Rocksmith save files and profiles
- **Song lists**: Create and manage custom song lists

### RS-Utils
Located in `./rs-utils/` (submodule from [0x0L/rs-utils](https://github.com/0x0L/rs-utils))

A collection of Python scripts for Rocksmith 2014:

- **audio2wem**: Convert audio files to Wwise WEM format
- **psarc.py**: Pack, unpack and convert PSARC archives
- **tones.py**: Extract tones from profile and PSARC files
- **Additional tools**: Various utilities for Rocksmith 2014 file manipulation

## Requirements

### System Requirements
- **Windows** (this tool only works on Windows)
- **Wwise v2013.2.10 build 4884** - Required for audio conversion
  - Download from: https://ignition4.customsforge.com/tools/wwise
- Python 3.8+ (for Demucs and main application)
- CUDA-compatible GPU (recommended for faster processing)
- Git (for cloning with submodules)

### Python Dependencies
```bash
pip install -r requirements.txt
# Or manually:
pip install torch torchaudio demucs soundfile numpy
```

## Installation

### Prerequisites

1. **Python 3.8+** with pip
2. **Git** (to clone the repository with submodules)

### Setup

1. **Clone the repository with submodules**:
   ```bash
   git clone --recursive <repository-url>
   cd RockSmithGuitarMute
   ```
   
   Or if you already cloned without `--recursive`:
   ```bash
   git clone <repository-url>
   cd RockSmithGuitarMute
   git submodule update --init --recursive
   ```

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Install the package** (optional, for development):
   ```bash
   pip install -e .
   ```

4. **Test the installation**:
   ```bash
   python tests/test_import.py
   ```

## Usage

### Command Line Interface

Basic usage:
```bash
python rocksmith_guitar_mute.py <input_path> <output_dir> [options]
```

### Examples

**Process a single PSARC file**:
```bash
python rocksmith_guitar_mute.py sample/2minutes_p.psarc output/
```

**Process all PSARC files in a directory**:
```bash
python rocksmith_guitar_mute.py input_directory/ output/
```

**Use specific Demucs model and GPU**:
```bash
python rocksmith_guitar_mute.py song.psarc output/ --model htdemucs --device cuda
```

**Enable verbose logging**:
```bash
python rocksmith_guitar_mute.py song.psarc output/ --verbose
```

### Command Line Options

- `input_path`: Path to PSARC file or directory containing PSARC files
- `output_dir`: Directory where processed files will be saved
- `--model`: Demucs model to use (default: htdemucs)
  - Options: `htdemucs`, `htdemucs_ft`, `mdx_extra`, `mdx_extra_q`, `mdx_q`, `hdemucs_mmi`
- `--device`: Processing device (default: auto)
  - Options: `auto`, `cpu`, `cuda`
- `--verbose`: Enable detailed logging

### Processing Pipeline

The tool automatically performs these steps:

1. **Unpack PSARC**: Extracts all files from the Rocksmith 2014 archive
2. **Find Audio**: Locates WEM, OGG, and WAV audio files
3. **Convert Format**: Converts WEM files to WAV for processing
4. **Separate Sources**: Uses Demucs AI to separate instruments:
   - Drums
   - Bass  
   - Vocals
   - Other (typically guitar/lead instruments)
5. **Create Backing Track**: Combines all stems except guitar
6. **Replace Audio**: Converts processed audio back to original format
7. **Repack PSARC**: Creates new archive with modified audio

### Configuration

You can customize processing settings by editing `config.yaml`:

```yaml
demucs:
  model: "htdemucs"
  device: "auto"
  shifts: 1

audio:
  exclude_stems: ["other"]  # Stems to remove (guitar)
  fallback_stems: ["drums", "bass", "vocals"]
```

## Sample Data

The `sample/` directory contains example PSARC files for testing:
- `2minutes_p.psarc`: Sample Rocksmith 2014 DLC file

## Development

### Running Tests
```bash
python tests/test_import.py
python tests/test_gui.py
python tests/test_guitar_extraction.py
python tests/test_parallel_processing.py
```

## Audio Quality Considerations

- **Source separation quality**: Demucs v4 provides excellent separation but may have artifacts
- **Processing time**: GPU acceleration significantly reduces processing time
- **File size**: Processed files maintain original quality and file size
- **Compatibility**: Output maintains full Rocksmith 2014 compatibility

## Limitations

- Guitar separation quality depends on the complexity of the mix
- Processing time varies with song length and hardware capabilities
- Some audio artifacts may be introduced during source separation
- Works best with standard rock/pop arrangements

## Dependencies and Acknowledgments

This project relies on several excellent open-source libraries. We are grateful to their authors and contributors:

### Core Dependencies
- **[Demucs](https://github.com/facebookresearch/demucs)** by Facebook Research - State-of-the-art AI music source separation
- **[RSRTools](https://github.com/BuongiornoTexas/rsrtools)** by BuongiornoTexas - Rocksmith 2014 PSARC handling and utilities
- **[RS-Utils](https://github.com/0x0L/rs-utils)** by 0x0L - Collection of Python scripts for Rocksmith 2014

### License

This project combines multiple components with different licenses:
- **Demucs**: MIT License
- **RSRTools**: Check repository for license terms
- **RS-Utils**: Check repository for license terms

Please refer to individual component directories for specific license terms.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test with sample PSARC files
5. Submit a pull request

---

**Note**: This tool is for educational and personal use. Respect copyright laws and the terms of service of Rocksmith 2014 when processing audio content.