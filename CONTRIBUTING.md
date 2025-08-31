# Contributing to RockSmith Guitar Mute

Thank you for your interest in contributing to RockSmith Guitar Mute! This document provides guidelines and information for contributors.

## Getting Started

### Prerequisites

- Python 3.8+
- Git
- Basic knowledge of audio processing and AI/ML concepts

### Development Setup

1. **Fork and clone the repository**:
   ```bash
   git clone --recursive https://github.com/yourusername/RockSmithGuitarMute.git
   cd RockSmithGuitarMute
   ```

2. **Set up development environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   pip install -e .
   ```

3. **Initialize submodules** (if not done with `--recursive`):
   ```bash
   git submodule update --init --recursive
   ```

## Project Structure

```
RockSmithGuitarMute/
├── rocksmith_guitar_mute.py    # Main application
├── audio2wem_windows.py        # Audio conversion utilities
├── setup.py                    # Package setup
├── requirements.txt            # Python dependencies
├── tests/                      # Test suite
│   ├── test_import.py         # Import tests
│   ├── test_gui.py            # GUI tests
│   └── test_*.py              # Other tests
├── gui/                        # GUI components
│   ├── gui_main.py            # Main GUI application
│   ├── gui_config.py          # GUI configuration
│   └── launch_gui.py          # GUI launcher
├── build/                      # Build and packaging scripts
│   ├── build_windows.py       # Windows build script
│   ├── optimize_build.py      # Build optimization
│   └── *.bat                  # Batch scripts
├── demucs/                     # Demucs submodule (AI separation)
├── rsrtools/                   # RSRTools submodule (PSARC handling)
└── rs-utils/                   # RS-Utils submodule (utilities)
```

## Development Guidelines

### Code Style

- Follow PEP 8 for Python code
- Use meaningful variable and function names
- Add docstrings to all functions and classes
- Keep functions focused and small

### Testing

- Write tests for new functionality
- Run existing tests before submitting changes:
  ```bash
  python tests/test_import.py
  python tests/test_gui.py
  ```
- Ensure all tests pass before submitting a pull request

### Git Workflow

1. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** with clear, descriptive commits:
   ```bash
   git add .
   git commit -m "Add feature: clear description of what you added"
   ```

3. **Update submodules if needed**:
   ```bash
   git submodule update --remote
   ```

4. **Push and create a pull request**:
   ```bash
   git push origin feature/your-feature-name
   ```

## Working with Submodules

This project uses Git submodules for external dependencies:

- **demucs/**: AI music source separation
- **rsrtools/**: PSARC file handling
- **rs-utils/**: Utility functions

### Updating Submodules

```bash
# Update all submodules to latest
git submodule update --remote

# Update specific submodule
git submodule update --remote demucs
```

### Making Changes to Submodules

If you need to modify submodule code:

1. Fork the original repository
2. Make changes in your fork
3. Update the submodule reference in the main project
4. Submit pull requests to both repositories

## Areas for Contribution

### High Priority
- **Performance optimization**: Improve processing speed
- **Error handling**: Better error messages and recovery
- **Documentation**: Improve user guides and API docs
- **Testing**: Expand test coverage

### Medium Priority
- **GUI improvements**: Better user interface
- **Audio format support**: Additional input/output formats
- **Cross-platform support**: Linux and macOS compatibility

### Low Priority
- **Advanced features**: Batch processing, presets
- **Integration**: Plugin system, external tool integration

## Submitting Changes

### Pull Request Process

1. **Ensure your code follows the guidelines**
2. **Update documentation** if needed
3. **Add or update tests** for your changes
4. **Create a clear pull request description**:
   - What does this change do?
   - Why is this change needed?
   - How has it been tested?

### Pull Request Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Tests pass locally
- [ ] New tests added (if applicable)
- [ ] Manual testing performed

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No breaking changes (or clearly documented)
```

## Reporting Issues

### Bug Reports

Include:
- Operating system and version
- Python version
- Steps to reproduce
- Expected vs actual behavior
- Error messages or logs
- Sample files (if applicable)

### Feature Requests

Include:
- Clear description of the feature
- Use case and benefits
- Possible implementation approach
- Examples or mockups (if applicable)

## Community Guidelines

- Be respectful and inclusive
- Help others learn and contribute
- Focus on constructive feedback
- Follow the project's code of conduct

## Getting Help

- **Issues**: Use GitHub issues for bugs and feature requests
- **Discussions**: Use GitHub discussions for questions
- **Documentation**: Check the README and inline documentation

## License

By contributing, you agree that your contributions will be licensed under the same license as the project (MIT License).

Thank you for contributing to RockSmith Guitar Mute!
