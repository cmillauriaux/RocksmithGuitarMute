# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['..\\gui\\gui_main.py'],
    pathex=[],
    binaries=[],
    datas=[('../rs-utils', 'rs-utils'), ('../rsrtools/src/rsrtools', 'rsrtools'), ('../demucs/demucs', 'demucs'), ('../demucs/conf', 'demucs/conf'), ('../audio2wem_windows.py', '.')],
    hiddenimports=['torch', 'torch.cuda', 'torch.nn', 'torch.optim', 'torchaudio', 'torchaudio.transforms', 'demucs', 'demucs.separate', 'demucs.pretrained', 'demucs.api', 'soundfile', 'numpy', 'scipy.signal', 'tkinter', 'tkinter.ttk', 'tkinter.filedialog', 'tkinter.messagebox', 'threading', 'queue', 'multiprocessing', 'concurrent.futures', 'pathlib', 'shutil', 'tempfile', 'subprocess', 'logging', 'pkg_resources', 'setuptools', 'jaraco.text', 'jaraco.functools', 'rsrtools.files.welder', 'rsrtools.files.config', 'rsrtools.files.exceptions'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['matplotlib', 'seaborn', 'plotly', 'bokeh', 'pandas', 'sklearn', 'scikit-learn', 'statsmodels', 'cv2', 'opencv', 'PIL', 'Pillow', 'skimage', 'jupyter', 'notebook', 'IPython', 'ipykernel', 'ipywidgets', 'sphinx', 'docutils', 'torchvision', 'torchtext', 'sympy', 'networkx', 'h5py', 'tables'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='RockSmithGuitarMute',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
