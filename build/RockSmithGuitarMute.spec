# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['..\\gui\\gui_main.py'],
    pathex=[],
    binaries=[('C:\\Users\\Cedric\\AppData\\Local\\Programs\\Python\\Python311\\python311.dll', '.'), ('C:\\Users\\Cedric\\AppData\\Local\\Programs\\Python\\Python311\\DLLs\\libcrypto-3.dll', 'DLLs'), ('C:\\Users\\Cedric\\AppData\\Local\\Programs\\Python\\Python311\\DLLs\\libffi-8.dll', 'DLLs'), ('C:\\Users\\Cedric\\AppData\\Local\\Programs\\Python\\Python311\\DLLs\\libssl-3.dll', 'DLLs'), ('C:\\Users\\Cedric\\AppData\\Local\\Programs\\Python\\Python311\\DLLs\\sqlite3.dll', 'DLLs'), ('C:\\Users\\Cedric\\AppData\\Local\\Programs\\Python\\Python311\\DLLs\\tcl86t.dll', 'DLLs'), ('C:\\Users\\Cedric\\AppData\\Local\\Programs\\Python\\Python311\\DLLs\\tk86t.dll', 'DLLs'), ('C:\\WINDOWS\\System32\\vcruntime140.dll', '.'), ('C:\\WINDOWS\\SysWOW64\\vcruntime140.dll', '.'), ('C:\\Users\\Cedric\\AppData\\Local\\Programs\\Python\\Python311\\Lib\\site-packages\\torch\\lib\\torch_cpu.dll', '.'), ('C:\\Users\\Cedric\\AppData\\Local\\Programs\\Python\\Python311\\Lib\\site-packages\\torch\\lib\\torch_cpu.dll', '.'), ('C:\\Users\\Cedric\\AppData\\Local\\Programs\\Python\\Python311\\Lib\\site-packages\\torch\\lib\\torch_global_deps.dll', '.'), ('C:\\Users\\Cedric\\AppData\\Local\\Programs\\Python\\Python311\\Lib\\site-packages\\torch\\lib\\torch_python.dll', '.'), ('C:\\Users\\Cedric\\AppData\\Local\\Programs\\Python\\Python311\\Lib\\site-packages\\torch\\lib\\c10.dll', '.'), ('C:\\Users\\Cedric\\AppData\\Local\\Programs\\Python\\Python311\\Lib\\site-packages\\torch\\lib\\fbgemm.dll', '.'), ('C:\\Users\\Cedric\\AppData\\Local\\Programs\\Python\\Python311\\Lib\\site-packages\\torch\\bin\\fbgemm.dll', '.')],
    datas=[('../rs-utils', 'rs-utils'), ('../rsrtools/src/rsrtools', 'rsrtools'), ('../demucs/demucs', 'demucs'), ('../demucs/conf', 'demucs/conf'), ('../audio2wem_windows.py', '.'), ('C:\\Users\\Cedric\\AppData\\Local\\Programs\\Python\\Python311\\Lib\\site-packages\\demucs\\remote\\files.txt', 'demucs\\remote'), ('C:\\Users\\Cedric\\AppData\\Local\\Programs\\Python\\Python311\\Lib\\site-packages\\demucs\\remote\\hdemucs_mmi.yaml', 'demucs\\remote'), ('C:\\Users\\Cedric\\AppData\\Local\\Programs\\Python\\Python311\\Lib\\site-packages\\demucs\\remote\\htdemucs.yaml', 'demucs\\remote'), ('C:\\Users\\Cedric\\AppData\\Local\\Programs\\Python\\Python311\\Lib\\site-packages\\demucs\\remote\\htdemucs_6s.yaml', 'demucs\\remote'), ('C:\\Users\\Cedric\\AppData\\Local\\Programs\\Python\\Python311\\Lib\\site-packages\\demucs\\remote\\htdemucs_ft.yaml', 'demucs\\remote'), ('C:\\Users\\Cedric\\AppData\\Local\\Programs\\Python\\Python311\\Lib\\site-packages\\demucs\\remote\\mdx.yaml', 'demucs\\remote'), ('C:\\Users\\Cedric\\AppData\\Local\\Programs\\Python\\Python311\\Lib\\site-packages\\demucs\\remote\\mdx_extra.yaml', 'demucs\\remote'), ('C:\\Users\\Cedric\\AppData\\Local\\Programs\\Python\\Python311\\Lib\\site-packages\\demucs\\remote\\mdx_extra_q.yaml', 'demucs\\remote'), ('C:\\Users\\Cedric\\AppData\\Local\\Programs\\Python\\Python311\\Lib\\site-packages\\demucs\\remote\\mdx_q.yaml', 'demucs\\remote'), ('C:\\Users\\Cedric\\AppData\\Local\\Programs\\Python\\Python311\\Lib\\site-packages\\demucs\\remote\\repro_mdx_a.yaml', 'demucs\\remote'), ('C:\\Users\\Cedric\\AppData\\Local\\Programs\\Python\\Python311\\Lib\\site-packages\\demucs\\remote\\repro_mdx_a_hybrid_only.yaml', 'demucs\\remote'), ('C:\\Users\\Cedric\\AppData\\Local\\Programs\\Python\\Python311\\Lib\\site-packages\\demucs\\remote\\repro_mdx_a_time_only.yaml', 'demucs\\remote')],
    hiddenimports=['torch', 'torchaudio', 'demucs', 'demucs.separate', 'demucs.pretrained', 'soundfile', 'numpy', 'scipy', 'tkinter', 'tkinter.ttk', 'tkinter.filedialog', 'tkinter.messagebox', 'rsrtools.files.welder', 'rsrtools.files.config', 'rsrtools.files.exceptions', 'torch.nn', 'torch.nn.functional', 'torch.optim', 'torch.utils', 'torch.utils.data', 'torch._C', 'torch._C._nn', 'torch._C._fft', 'torch._C._linalg', 'torch._C._sparse', 'torch.backends', 'torch.backends.cpu', 'torch.backends.mkl', 'torch.backends.mkldnn', 'torchaudio.transforms', 'torchaudio.functional', 'torchaudio.models', 'torchaudio._extension', 'torchaudio.io', 'demucs.hdemucs', 'demucs.htdemucs', 'demucs.wdemucs', 'demucs.transformer', 'demucs.spec', 'demucs.states', 'demucs.utils', 'demucs.wav', 'demucs.audio', 'demucs.repo', 'demucs.apply', 'numpy.core', 'numpy.core.multiarray', 'numpy.core._multiarray_umath', 'numpy.core.multiarray_umath', 'numpy.core.numeric', 'numpy.core.umath', 'numpy._typing', 'numpy._typing._array_like', 'numpy._typing._dtype_like', 'numpy.lib', 'numpy.lib.recfunctions', 'numpy.ma', 'numpy.ma.core', 'numpy.random', 'numpy.random._pickle', 'numpy.linalg', 'numpy.fft', 'numpy.core._methods', 'numpy.core.arrayprint', 'numpy.core.fromnumeric', 'numpy.core.function_base', 'numpy.core.getlimits', 'numpy.core.shape_base', 'diffq', 'einops', 'julius', 'openunmix', 'tqdm', 'omegaconf', 'hydra', 'hydra.core', 'hydra.core.config_store', 'hydra.core.global_hydra', 'dora', 'lameenc', 'packaging', 'setuptools', 'pkg_resources', 'dora_search', 'typing_extensions', 'importlib_metadata', 'importlib_resources', 'antlr4', 'antlr4.tree', 'antlr4.error'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='..\\RSGM_v1a_box.ico',
)
