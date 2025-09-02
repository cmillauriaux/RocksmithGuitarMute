#!/usr/bin/env python3
"""
Hook PyInstaller pour Demucs - Inclut toutes les dépendances critiques
"""

from PyInstaller.utils.hooks import collect_submodules, collect_data_files
import os

# Collecter tous les sous-modules Demucs
hiddenimports = collect_submodules('demucs')

# Ajouter spécifiquement les modules critiques
hiddenimports.extend([
    'demucs.separate',
    'demucs.pretrained',
    'demucs.hdemucs',
    'demucs.htdemucs', 
    'demucs.wdemucs',
    'demucs.transformer',
    'demucs.spec',
    'demucs.states',
    'demucs.utils',
    'demucs.wav',
    'demucs.audio',
    'demucs.repo',
    'demucs.apply',
    'demucs.api',
])

# Collecter les fichiers de données Demucs (configurations, etc.)
datas = collect_data_files('demucs')

# Debug
print(f"PyInstaller hook-demucs: Found {len(hiddenimports)} demucs modules")
if datas:
    print(f"PyInstaller hook-demucs: Found {len(datas)} demucs data files")
else:
    print("PyInstaller hook-demucs: Warning - No demucs data files found")
