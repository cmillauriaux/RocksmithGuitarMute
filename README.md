# RockSmithGuitarMute

A tool for processing Rocksmith 2014 PSARC files to create multiple stem-mix variants using AI-powered source separation.

## Overview

This project automates the process of unpacking Rocksmith 2014 PSARC files, extracting audio tracks, separating instruments using AI source separation, and repacking modified files with different stem combinations. Produce up to 7 variants per song — no guitar, no vocals, drums only, and more — each with unique identifiers so they can all coexist in Rocksmith simultaneously.

## Features

### Multi-Variant Output
Produce multiple versions of each song in a single run:

| Variant | Description | Included Stems |
|---------|-------------|---------------|
| `no_guitar` | Backing track without guitar (default) | drums, bass, vocals, piano, other |
| `no_vocals` | Instrumental without vocals | drums, bass, piano, other, guitar |
| `no_bass` | Mix without bass | drums, vocals, piano, other, guitar |
| `no_guitar_no_bass` | Mix without guitar or bass | drums, vocals, piano, other |
| `no_guitar_no_bass_no_vocals` | Drums + keys backing only | drums, piano, other |
| `drums_only` | Isolated drums | drums |
| `vocals_and_drums` | Only vocals and drums | vocals, drums |

- **Unique Identifiers**: Each variant gets its own DLCKey, PersistentID, and SongName so all variants can be loaded in Rocksmith at the same time without collisions
- **Efficient Processing**: Demucs AI separation runs only **once** per input file — stems are then remixed cheaply for each variant

### Performance Optimizations
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

### 3. Separate & Remix Stems
Using **Demucs** (v4) - a state-of-the-art AI music source separation model:
- Separates audio into 6 stems: drums, bass, vocals, piano, guitar, and other
- Uses Hybrid Transformer architecture (htdemucs_6s) for high-quality separation
- Achieves 9.00+ dB SDR (Signal-to-Distortion Ratio) on test sets
- Remixes stems into one or more variants based on `--variants` selection

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
- **Wwise v2013.2.10 build 4884** - Required for audio conversion (newer versions are not compatible)
  - Download from: https://ignition4.customsforge.com/tools/wwise
- **FFmpeg** - Required for audio format conversion
  - Install via Chocolatey: `choco install ffmpeg`
- **Python 3.10–3.12** — Python 3.12 is recommended. Python 3.13+ is not yet supported due to incompatibilities with torch and diffq. Python 3.8/3.9 are end-of-life.
- CUDA-compatible GPU (recommended for faster processing)
- Git (for cloning with submodules)

### Python Dependencies
```bash
pip install -r requirements.txt
# Or manually (note: torch/torchaudio must be pinned — see note below):
pip install torch==2.6.0 torchaudio==2.6.0 demucs soundfile numpy
```

> **Note on torch/torchaudio versions:** `torch` and `torchaudio` are pinned to `2.6.0`. torchaudio 2.7+ switched its default audio backend to `torchcodec`, which is not available on Windows. Do not upgrade these without testing.

## Installation

### Prerequisites

1. **Python 3.12** (recommended) — download from [python.org](https://python.org). During install, check **"Add Python to PATH"**. Python 3.13+ is not supported.
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

2. **Create and activate a virtual environment** (strongly recommended):
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```
   You should see `(venv)` in your prompt. All subsequent commands should be run inside this environment.

3. **Install PyTorch with CUDA** (if you have an NVIDIA GPU):
   ```bash
   pip install torch==2.6.0 torchaudio==2.6.0 --index-url https://download.pytorch.org/whl/cu124
   ```
   Skip this step if you don't have an NVIDIA GPU — the next step will install CPU-only PyTorch.

4. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

5. **Install the package** (optional, for development):
   ```bash
   pip install -e .
   ```

6. **Test the installation**:
   ```bash
   python tests/test_import.py
   ```

## Usage

### Graphical Interface (GUI)

A dark-themed GUI is available for users who prefer a visual interface over the command line.

**Launch the GUI:**
```bash
python gui/launch_gui.py
```

**Features:**
- File/folder browser for selecting input PSARC files and output directory
- Checkbox selection for all 7 built-in stem mix variants (with Select All / Deselect All)
- Custom variant builder: name your own mix and pick which stems to include
- Demucs model and device (CPU/GPU) selection
- Vocals volume reduction slider (0-100%)
- Real-time progress bar tracking per-variant output
- Activity log with live processing updates
- Pause and cancel support during processing

**Additional dependency for GUI:**
```bash
pip install Pillow
```

### Command Line Interface

Basic usage:
```bash
python rocksmith_guitar_mute.py <input_path> <output_dir> [options]
```

### Examples

**Process a single PSARC file** (default: no guitar):
```bash
python rocksmith_guitar_mute.py song.psarc output/
```

**Generate all 7 variants**:
```bash
python rocksmith_guitar_mute.py song.psarc output/ --variants all
```

**Generate specific variants**:
```bash
python rocksmith_guitar_mute.py song.psarc output/ --variants no_vocals drums_only
```

**Process all PSARC files in a directory**:
```bash
python rocksmith_guitar_mute.py input_directory/ output/ --variants all
```

**Use specific Demucs model and GPU**:
```bash
python rocksmith_guitar_mute.py song.psarc output/ --model htdemucs --device cuda
```

**Create a custom variant** (only drums and vocals):
```bash
python rocksmith_guitar_mute.py song.psarc output/ --custom "my_mix:drums,vocals"
```

**Mix built-in and custom variants**:
```bash
python rocksmith_guitar_mute.py song.psarc output/ --variants no_guitar --custom "rhythm_section:drums,bass" --custom "keys_only:piano,other"
```

**Enable verbose logging**:
```bash
python rocksmith_guitar_mute.py song.psarc output/ --verbose
```

### Command Line Options

- `input_path`: Path to PSARC file or directory containing PSARC files
- `output_dir`: Directory where processed files will be saved
- `--variants`: Stem mix variants to produce (default: `no_guitar`)
  - Options: `no_guitar`, `no_vocals`, `no_bass`, `no_guitar_no_bass`, `drums_only`, `vocals_and_drums`, `all`
- `--model`: Demucs model to use (default: htdemucs_6s)
  - Options: `htdemucs_6s`, `htdemucs`, `htdemucs_ft`, `mdx_extra`, `mdx_extra_q`
- `--device`: Processing device (default: auto)
  - Options: `auto`, `cpu`, `cuda`
- `--custom`: Custom variant as `name:stem1,stem2,...` (can be repeated)
  - Valid stems: `drums`, `bass`, `vocals`, `piano`, `guitar`, `other`
- `--reduce-vocals`: Vocals volume percentage, 0-100 (default: 100)
- `--workers`: Number of parallel workers (default: number of CPU cores)
- `--force`: Process files even if output already exists
- `--verbose`: Enable detailed logging

### Processing Pipeline

The tool automatically performs these steps:

1. **Unpack PSARC**: Extracts all files from the Rocksmith 2014 archive
2. **Find Audio**: Locates WEM, OGG, and WAV audio files
3. **Convert Format**: Converts WEM files to WAV for processing
4. **Separate Sources**: Uses Demucs AI to separate into 6 stems (drums, bass, vocals, piano, guitar, other)
5. **Remix Variants**: For each requested variant, combines the appropriate stems
6. **Unique Metadata**: Updates DLCKey, PersistentID, and SongName per variant
7. **Replace Audio**: Converts processed audio back to original format
8. **Repack PSARC**: Creates new archive(s) with modified audio

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