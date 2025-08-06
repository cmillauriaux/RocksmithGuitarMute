# Development Guide

This document provides detailed information for developers working on the RockSmith Guitar Mute project.

## Architecture Overview

The project consists of three main components:

### 1. Main Python Application (`rocksmith_guitar_mute.py`)
- **Purpose**: Orchestrates the entire workflow
- **Dependencies**: PyTorch, TorchAudio, Demucs
- **Key Classes**:
  - `RocksmithGuitarMute`: Main processor class
  - Methods for PSARC handling, audio processing, and file management

### 2. Rocksmith2014.NET Integration
- **Location**: `Rocksmith2014.NET/` directory
- **Language**: F# and C#
- **Purpose**: Handles PSARC file format operations
- **Key Libraries**:
  - `Rocksmith2014.PSARC`: Archive manipulation
  - `Rocksmith2014.Audio`: Audio format conversion
  - `Rocksmith2014.Common`: Shared utilities

### 3. Demucs Integration
- **Location**: `demucs/` directory
- **Language**: Python
- **Purpose**: AI-powered music source separation
- **Key Components**:
  - Hybrid Transformer models for source separation
  - Support for multiple audio formats
  - GPU acceleration capabilities

## Workflow Details

### Step 1: PSARC Unpacking
```python
# Uses F# script to call Rocksmith2014.NET
use psarc = PSARC.OpenFile(psarcPath)
do! psarc.ExtractAll(extractPath, None)
```

### Step 2: Audio Processing
1. **File Discovery**: Scan for WEM, OGG, WAV files
2. **Format Conversion**: WEM → OGG → WAV using ww2ogg/revorb
3. **Source Separation**: Demucs AI processing
4. **Stem Combination**: Create backing track (exclude guitar)

### Step 3: PSARC Repacking
```python
# Rebuild archive with modified audio
do! PSARC.PackDirectory(extractPath, outputPath, true)
```

## File Processing Pipeline

```
Input PSARC
     ↓
Temporary Directory
     ↓
Extract All Files
     ↓
Locate Audio Files (.wem, .ogg, .wav)
     ↓
Convert to WAV (if needed)
     ↓
Process with Demucs
     ├── drums
     ├── bass
     ├── vocals
     └── other (guitar) ← excluded
     ↓
Combine Non-Guitar Stems
     ↓
Convert Back to Original Format
     ↓
Replace in Temporary Directory
     ↓
Repack PSARC
     ↓
Output Modified PSARC
```

## Key Dependencies

### Python Requirements
- **PyTorch**: Deep learning framework for Demucs
- **TorchAudio**: Audio processing utilities
- **Demucs**: Source separation models

### .NET Requirements
- **.NET 8.0+**: Runtime for Rocksmith2014.NET
- **F# Support**: For F# interactive scripts
- **Native Audio Tools**: ww2ogg, revorb for WEM conversion

## Configuration System

The application uses `config.yaml` for settings:

```yaml
demucs:
  model: "htdemucs"      # AI model selection
  device: "auto"         # Processing device
  shifts: 1              # Quality/speed tradeoff

audio:
  exclude_stems: ["other"]  # Which stems to remove
  intermediate_format: "wav"  # Processing format
```

## Error Handling

### Common Issues and Solutions

1. **PSARC Extraction Failures**
   - Corrupted archive files
   - Insufficient disk space
   - Permission issues

2. **Audio Processing Errors**
   - Unsupported audio formats
   - Memory limitations with large files
   - GPU/CUDA compatibility issues

3. **WEM Conversion Problems**
   - Missing conversion tools
   - Platform-specific tool variants
   - Codec compatibility

## Testing

### Unit Tests
Run individual component tests:
```bash
python test_setup.py  # Basic functionality
python -m pytest      # Full test suite (if implemented)
```

### Integration Tests
Test with sample files:
```bash
python run_example.py  # End-to-end test
```

### Manual Testing
```bash
# Test specific components
python -c "import demucs.api; print('Demucs OK')"
dotnet run --project Rocksmith2014.NET/samples/MiscTools
```

## Performance Considerations

### GPU Acceleration
- **CUDA**: Significantly faster processing with compatible GPUs
- **Memory**: Large audio files require substantial GPU memory
- **Batch Processing**: Process multiple files efficiently

### CPU Fallback
- **Threading**: Multi-core CPU utilization
- **Memory Management**: Efficient handling of large audio files
- **Disk I/O**: Temporary file management

### Optimization Tips
1. Use SSD storage for temporary files
2. Allocate sufficient RAM (8GB+ recommended)
3. Use GPU when available for Demucs processing
4. Process shorter segments for memory-constrained systems

## Extending the Project

### Adding New Audio Formats
1. Extend `find_audio_files()` method
2. Add conversion functions
3. Update format detection logic

### Supporting Additional Models
1. Modify Demucs model selection
2. Update configuration options
3. Test with different source separation approaches

### Custom Stem Processing
1. Modify `remove_guitar_track()` method
2. Implement custom stem combination logic
3. Add configuration options for stem selection

## Troubleshooting

### Debug Mode
Enable verbose logging:
```bash
python rocksmith_guitar_mute.py input.psarc output/ --verbose
```

### Log Analysis
Check log files:
- `rocksmith_guitar_mute.log`: Main application log
- Console output: Real-time progress and errors

### Common Solutions
1. **Permission Errors**: Run with appropriate privileges
2. **Missing Dependencies**: Run `python setup.py` to verify
3. **Memory Issues**: Reduce batch size or use CPU processing
4. **Compatibility**: Ensure .NET and Python versions match requirements

## Contributing

### Code Style
- Follow PEP 8 for Python code
- Use meaningful variable names
- Add docstrings for all functions
- Include type hints where possible

### Testing
- Add tests for new functionality
- Verify compatibility across platforms
- Test with various PSARC file types

### Documentation
- Update README.md for user-facing changes
- Update this DEVELOPMENT.md for technical changes
- Add inline comments for complex logic

## Release Process

1. **Version Updates**: Update version numbers in setup files
2. **Testing**: Run full test suite on multiple platforms
3. **Documentation**: Update changelog and documentation
4. **Packaging**: Create distribution packages
5. **Validation**: Test with fresh environment setup