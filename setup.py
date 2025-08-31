#!/usr/bin/env python3
"""
Setup script for RockSmith Guitar Mute
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme_path = Path(__file__).parent / "README.md"
long_description = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""

# Read requirements
requirements_path = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_path.exists():
    requirements = requirements_path.read_text(encoding="utf-8").strip().split("\n")
    requirements = [req.strip() for req in requirements if req.strip() and not req.startswith("#")]

setup(
    name="rocksmith-guitar-mute",
    version="1.0.0",
    description="AI-powered tool for removing guitar tracks from Rocksmith 2014 PSARC files",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="RockSmith Guitar Mute Team",
    url="https://github.com/yourusername/RockSmithGuitarMute",
    packages=find_packages(),
    py_modules=["rocksmith_guitar_mute", "audio2wem_windows"],
    install_requires=requirements,
    extras_require={
        "gui": ["tkinter"],
        "dev": ["pytest", "black", "flake8"],
    },
    entry_points={
        "console_scripts": [
            "rocksmith-guitar-mute=rocksmith_guitar_mute:main",
            "rocksmith-gui=gui.gui_main:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Multimedia :: Sound/Audio",
        "Topic :: Multimedia :: Sound/Audio :: Analysis",
    ],
    python_requires=">=3.8",
    include_package_data=True,
    zip_safe=False,
)
