#!/usr/bin/env python3
"""
Hook PyInstaller pour NumPy - Resout les problemes numpy.core.multiarray
"""

from PyInstaller.utils.hooks import collect_submodules, collect_data_files

# Collecter tous les sous-modules NumPy
hiddenimports = collect_submodules('numpy')

# Ajouter specifiquement les modules problematiques
hiddenimports.extend([
    'numpy.core',
    'numpy.core.multiarray', 
    'numpy.core._multiarray_umath',
    'numpy.core.multiarray_umath',
    'numpy._typing',
    'numpy._typing._array_like', 
    'numpy._typing._dtype_like',
    'numpy.lib',
    'numpy.lib.recfunctions',
    'numpy.ma',
    'numpy.ma.core',
    'numpy.random',
    'numpy.random._pickle',
    'numpy.linalg',
    'numpy.fft',
])

# Collecter les fichiers de donnees NumPy
datas = collect_data_files('numpy')
