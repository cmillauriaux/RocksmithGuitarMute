# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path

# Configuration de base
block_cipher = None
app_name = "RockSmithGuitarMute"

# Chemins des bibliothèques
torch_paths = ['C:\\Users\\Cedric\\AppData\\Local\\Programs\\Python\\Python311\\Lib\\site-packages\\torch\\lib', 'C:\\Users\\Cedric\\AppData\\Local\\Programs\\Python\\Python311\\Lib\\site-packages\\torch\\bin']

# DLL Python nécessaires
python_dlls = [('C:\\Users\\Cedric\\AppData\\Local\\Programs\\Python\\Python311\\python311.dll', '.'), ('C:\\Users\\Cedric\\AppData\\Local\\Programs\\Python\\Python311\\DLLs\\libcrypto-3.dll', 'DLLs'), ('C:\\Users\\Cedric\\AppData\\Local\\Programs\\Python\\Python311\\DLLs\\libffi-8.dll', 'DLLs'), ('C:\\Users\\Cedric\\AppData\\Local\\Programs\\Python\\Python311\\DLLs\\libssl-3.dll', 'DLLs'), ('C:\\Users\\Cedric\\AppData\\Local\\Programs\\Python\\Python311\\DLLs\\sqlite3.dll', 'DLLs'), ('C:\\Users\\Cedric\\AppData\\Local\\Programs\\Python\\Python311\\DLLs\\tcl86t.dll', 'DLLs'), ('C:\\Users\\Cedric\\AppData\\Local\\Programs\\Python\\Python311\\DLLs\\tk86t.dll', 'DLLs'), ('C:\\WINDOWS\\System32\\vcruntime140.dll', '.'), ('C:\\WINDOWS\\SysWOW64\\vcruntime140.dll', '.'), ('C:\\Users\\Cedric\\AppData\\Local\\Programs\\Python\\Python311\\Lib\\site-packages\\torch\\lib\\torch_cpu.dll', '.'), ('C:\\Users\\Cedric\\AppData\\Local\\Programs\\Python\\Python311\\Lib\\site-packages\\torch\\lib\\torch_cpu.dll', '.'), ('C:\\Users\\Cedric\\AppData\\Local\\Programs\\Python\\Python311\\Lib\\site-packages\\torch\\lib\\torch_global_deps.dll', '.'), ('C:\\Users\\Cedric\\AppData\\Local\\Programs\\Python\\Python311\\Lib\\site-packages\\torch\\lib\\torch_python.dll', '.'), ('C:\\Users\\Cedric\\AppData\\Local\\Programs\\Python\\Python311\\Lib\\site-packages\\torch\\lib\\c10.dll', '.'), ('C:\\Users\\Cedric\\AppData\\Local\\Programs\\Python\\Python311\\Lib\\site-packages\\torch\\lib\\fbgemm.dll', '.'), ('C:\\Users\\Cedric\\AppData\\Local\\Programs\\Python\\Python311\\Lib\\site-packages\\torch\\bin\\fbgemm.dll', '.')]

# Données Demucs
demucs_datas = [('C:\\Users\\Cedric\\AppData\\Local\\Programs\\Python\\Python311\\Lib\\site-packages\\demucs\\remote\\files.txt', 'demucs\\remote'), ('C:\\Users\\Cedric\\AppData\\Local\\Programs\\Python\\Python311\\Lib\\site-packages\\demucs\\remote\\hdemucs_mmi.yaml', 'demucs\\remote'), ('C:\\Users\\Cedric\\AppData\\Local\\Programs\\Python\\Python311\\Lib\\site-packages\\demucs\\remote\\htdemucs.yaml', 'demucs\\remote'), ('C:\\Users\\Cedric\\AppData\\Local\\Programs\\Python\\Python311\\Lib\\site-packages\\demucs\\remote\\htdemucs_6s.yaml', 'demucs\\remote'), ('C:\\Users\\Cedric\\AppData\\Local\\Programs\\Python\\Python311\\Lib\\site-packages\\demucs\\remote\\htdemucs_ft.yaml', 'demucs\\remote'), ('C:\\Users\\Cedric\\AppData\\Local\\Programs\\Python\\Python311\\Lib\\site-packages\\demucs\\remote\\mdx.yaml', 'demucs\\remote'), ('C:\\Users\\Cedric\\AppData\\Local\\Programs\\Python\\Python311\\Lib\\site-packages\\demucs\\remote\\mdx_extra.yaml', 'demucs\\remote'), ('C:\\Users\\Cedric\\AppData\\Local\\Programs\\Python\\Python311\\Lib\\site-packages\\demucs\\remote\\mdx_extra_q.yaml', 'demucs\\remote'), ('C:\\Users\\Cedric\\AppData\\Local\\Programs\\Python\\Python311\\Lib\\site-packages\\demucs\\remote\\mdx_q.yaml', 'demucs\\remote'), ('C:\\Users\\Cedric\\AppData\\Local\\Programs\\Python\\Python311\\Lib\\site-packages\\demucs\\remote\\repro_mdx_a.yaml', 'demucs\\remote'), ('C:\\Users\\Cedric\\AppData\\Local\\Programs\\Python\\Python311\\Lib\\site-packages\\demucs\\remote\\repro_mdx_a_hybrid_only.yaml', 'demucs\\remote'), ('C:\\Users\\Cedric\\AppData\\Local\\Programs\\Python\\Python311\\Lib\\site-packages\\demucs\\remote\\repro_mdx_a_time_only.yaml', 'demucs\\remote')]

# Données du projet
project_datas = [
    ('../rs-utils', 'rs-utils'),
    ('../rsrtools/src/rsrtools', 'rsrtools'),
    ('../demucs/demucs', 'demucs'),
    ('../demucs/conf', 'demucs/conf'),
    ('../audio2wem_windows.py', '.'),
]

# Modules cachés nécessaires
hidden_imports = [
    'torch',
    'torchaudio', 
    'demucs',
    'demucs.separate',
    'demucs.pretrained',
    'soundfile',
    'numpy',
    'scipy',
    'tkinter',
    'tkinter.ttk',
    'tkinter.filedialog',
    'tkinter.messagebox',
    'threading',
    'queue',
    'multiprocessing',
    'concurrent.futures',
    'pathlib',
    'shutil',
    'tempfile',
    'subprocess',
    'logging',
    'argparse',
    'sys',
    'os',
    # rsrtools imports (corriger le chemin)
    'rsrtools',
    'rsrtools.files',
    'rsrtools.files.welder',
    'rsrtools.files.config', 
    'rsrtools.files.exceptions',
    # Imports cachés supplémentaires pour PyTorch
    'torch.nn',
    'torch.nn.functional',
    'torch.optim',
    'torch.utils',
    'torch.utils.data',
    'torch._C',
    'torch._C._nn',
    'torch._C._fft',
    'torch._C._linalg',
    'torch._C._sparse',
    'torch.backends',
    'torch.backends.cpu',
    'torch.backends.mkl',
    'torch.backends.mkldnn',
    'torchaudio.transforms',
    'torchaudio.functional',
    'torchaudio.models',
    'torchaudio._extension',
    'torchaudio.io',
    # Imports pour Demucs  
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
    # Imports NumPy pour résoudre numpy.core.multiarray
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
]

            # Exclusions pour réduire la taille (mais garder les dépendances essentielles)
        excludes = [
            'matplotlib',
            'IPython',
            'jupyter',
            'notebook',
            'pandas',
            'sklearn',
            'cv2',
            'PIL',
            'pytest',
            # Ne pas exclure setuptools car PyTorch en a besoin
            # 'setuptools',
            # Ne pas exclure numpy.core - critique pour le fix CI
            # 'numpy.core',
        ]a = Analysis(
    ['../gui/gui_main.py'],
    pathex=['..'],
    binaries=python_dlls,
    datas=project_datas + demucs_datas,
    hiddenimports=hidden_imports,
    hookspath=['../hooks'],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=app_name,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # Console en mode debug
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico' if Path('icon.ico').exists() else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name=app_name,
)
