#!/usr/bin/env python3
"""
Script de compilation pour Windows - RockSmith Guitar Mute
Crée un exécutable standalone avec PyInstaller
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path
import argparse


def check_dependencies():
    """Vérifie que toutes les dépendances sont installées."""
    print("Verification des dependances...")
    
    # Afficher l'environnement pour debug
    print(f"Environnement Python:")
    print(f"  - Version: {sys.version}")
    print(f"  - Executable: {sys.executable}")
    
    # Packages avec leurs noms d'import alternatifs
    required_packages = [
        ('PyInstaller', 'pyinstaller'),  # PyInstaller s'importe avec une majuscule
        ('torch', 'torch'),
        ('torchaudio', 'torchaudio'), 
        ('demucs', 'demucs'),
        ('soundfile', 'soundfile'),
        ('numpy', 'numpy')
    ]
    
    missing_packages = []
    version_info = {}
    
    for import_name, package_name in required_packages:
        try:
            module = __import__(import_name)
            version = getattr(module, '__version__', 'version inconnue')
            version_info[package_name] = version
            print(f"  OK {package_name} ({version})")
        except ImportError:
            # Essayer avec le nom alternatif
            try:
                module = __import__(package_name)
                version = getattr(module, '__version__', 'version inconnue')
                version_info[package_name] = version
                print(f"  OK {package_name} ({version})")
            except ImportError:
                missing_packages.append(package_name)
                print(f"  ERREUR {package_name} (manquant)")
    
    # Vérifications spéciales pour PyTorch
    if 'torch' in version_info:
        try:
            import torch
            cuda_available = torch.cuda.is_available()
            cuda_count = torch.cuda.device_count() if cuda_available else 0
            print(f"  PyTorch CUDA: {'OK' if cuda_available else 'NON'} ({cuda_count} GPU(s))")
            
            # Détecter si on est dans un environnement CI
            is_ci = os.environ.get('GITHUB_ACTIONS') == 'true'
            if is_ci:
                print(f"  Environnement CI detecte (GitHub Actions)")
            else:
                print(f"  Environnement local detecte")
                
        except Exception as e:
            print(f"  ATTENTION Erreur lors de la verification PyTorch: {e}")
    
    if missing_packages:
        print(f"\nERREUR Packages manquants: {', '.join(missing_packages)}")
        print("Installez-les avec: pip install " + " ".join(missing_packages))
        return False
    
    print("OK Toutes les dependances sont installees!")
    return True


def clean_build_dirs():
    """Nettoie les répertoires de build précédents."""
    print("Nettoyage des builds precedents...")
    
    dirs_to_clean = ['build', 'dist', '__pycache__']
    
    for dir_name in dirs_to_clean:
        if Path(dir_name).exists():
            shutil.rmtree(dir_name)
            print(f"  Supprime: {dir_name}")
    
    # NE PAS supprimer les fichiers .spec - ils contiennent la configuration importante
    # for spec_file in Path('.').glob('*.spec'):
    #     spec_file.unlink()
    #     print(f"  Supprime: {spec_file}")
    print("  Conservation des fichiers .spec (configuration importante)")


def get_torch_paths():
    """Récupère les chemins des bibliothèques PyTorch."""
    try:
        import torch
        torch_path = Path(torch.__file__).parent
        
        # Chemins importants pour PyTorch
        torch_lib = torch_path / "lib"
        torch_bin = torch_path / "bin"
        
        paths = []
        if torch_lib.exists():
            paths.append(str(torch_lib))
        if torch_bin.exists():
            paths.append(str(torch_bin))
            
        return paths
    except ImportError:
        return []


def get_python_dll_paths():
    """Récupère les chemins des DLL Python nécessaires."""
    import sys
    import os
    
    python_dll_paths = []
    
    # Chemin de l'installation Python
    python_dir = Path(sys.executable).parent
    
    # Debug: afficher les chemins Python
    print(f"DEBUG: Python executable: {sys.executable}")
    print(f"DEBUG: Python directory: {python_dir}")
    print(f"DEBUG: Python version: {sys.version}")
    
    # Vérifier si on est dans un environnement CI
    is_ci = os.environ.get('GITHUB_ACTIONS') == 'true'
    if is_ci:
        print("DEBUG: Running in GitHub Actions CI environment")
    
    # DLL Python principale - recherche exhaustive
    python_version = f"python{sys.version_info.major}{sys.version_info.minor}"
    
    # Emplacements possibles pour la DLL Python principale
    possible_locations = [
        python_dir / f"{python_version}.dll",
        python_dir.parent / "DLLs" / f"{python_version}.dll",
        Path(sys.base_prefix) / f"{python_version}.dll",
        Path(sys.base_prefix) / "DLLs" / f"{python_version}.dll",
        Path(sys.executable).parent / f"{python_version}.dll",
        # Recherche dans System32 pour les installations système
        Path(os.environ.get('SYSTEMROOT', 'C:\\Windows')) / "System32" / f"{python_version}.dll",
    ]
    
    python_dll_found = False
    for python_dll in possible_locations:
        if python_dll.exists():
            python_dll_paths.append((str(python_dll), '.'))
            print(f"DEBUG: Found main Python DLL: {python_dll}")
            python_dll_found = True
            break
    
    if not python_dll_found:
        print(f"WARNING: Main Python DLL {python_version}.dll not found in any location!")
        # En dernier recours, chercher toute DLL python*.dll
        for search_dir in [python_dir, python_dir.parent, Path(sys.base_prefix)]:
            if search_dir.exists():
                for dll_file in search_dir.rglob("python*.dll"):
                    python_dll_paths.append((str(dll_file), '.'))
                    print(f"DEBUG: Found fallback Python DLL: {dll_file}")
                    python_dll_found = True
                    break
            if python_dll_found:
                break
    
    # DLLs dans le dossier DLLs
    dlls_dir = python_dir / "DLLs"
    if dlls_dir.exists():
        dll_count = 0
        for dll_file in dlls_dir.glob("*.dll"):
            python_dll_paths.append((str(dll_file), 'DLLs'))
            dll_count += 1
        print(f"DEBUG: Found {dll_count} DLLs in {dlls_dir}")
    else:
        print(f"DEBUG: DLLs directory not found at: {dlls_dir}")
        # Recherche alternative pour les DLL
        if is_ci:
            alt_dlls_dirs = [
                python_dir.parent / "DLLs",
                Path(sys.base_prefix) / "DLLs"
            ]
            for alt_dir in alt_dlls_dirs:
                if alt_dir.exists():
                    dll_count = 0
                    for dll_file in alt_dir.glob("*.dll"):
                        python_dll_paths.append((str(dll_file), 'DLLs'))
                        dll_count += 1
                    print(f"DEBUG: Found {dll_count} DLLs in alternative location: {alt_dir}")
                    break
    
    # Bibliothèques système importantes
    system_dlls = [
        "vcruntime140.dll",
        "msvcp140.dll", 
        "api-ms-win-crt-runtime-l1-1-0.dll",
        "ucrtbase.dll",
        "kernel32.dll",
        "user32.dll"
    ]
    
    # Chercher dans System32 et SysWOW64
    system_dirs = [
        Path(os.environ.get('SYSTEMROOT', 'C:\\Windows')) / "System32",
        Path(os.environ.get('SYSTEMROOT', 'C:\\Windows')) / "SysWOW64"
    ]
    
    system_dll_count = 0
    for system_dir in system_dirs:
        if system_dir.exists():
            for dll_name in system_dlls:
                dll_path = system_dir / dll_name
                if dll_path.exists():
                    python_dll_paths.append((str(dll_path), '.'))
                    system_dll_count += 1
                    break  # Prendre seulement la première occurrence
    print(f"DEBUG: Found {system_dll_count}/{len(system_dlls)} system DLLs")
    
    # Rechercher les DLL spécifiques à PyTorch et TorchAudio
    try:
        import torch
        import torchaudio
        
        torch_dir = Path(torch.__file__).parent
        torchaudio_dir = Path(torchaudio.__file__).parent
        
        # DLL PyTorch critiques
        torch_dlls = []
        for torch_lib_dir in [torch_dir / "lib", torch_dir / "bin", torch_dir]:
            if torch_lib_dir.exists():
                for dll_pattern in ["torch_cpu.dll", "torch_*.dll", "c10.dll", "fbgemm.dll"]:
                    for dll_file in torch_lib_dir.glob(dll_pattern):
                        torch_dlls.append((str(dll_file), '.'))
                        print(f"DEBUG: Found PyTorch DLL: {dll_file.name}")
        
        # DLL TorchAudio critiques  
        for torchaudio_lib_dir in [torchaudio_dir / "lib", torchaudio_dir / "bin", torchaudio_dir]:
            if torchaudio_lib_dir.exists():
                for dll_pattern in ["torchaudio*.dll", "sox*.dll"]:
                    for dll_file in torchaudio_lib_dir.glob(dll_pattern):
                        torch_dlls.append((str(dll_file), '.'))
                        print(f"DEBUG: Found TorchAudio DLL: {dll_file.name}")
        
        python_dll_paths.extend(torch_dlls)
        print(f"DEBUG: Found {len(torch_dlls)} PyTorch/TorchAudio DLLs")
        
    except ImportError:
        print("DEBUG: PyTorch/TorchAudio not available for DLL detection")
    
    # Vérification finale
    total_dlls = len(python_dll_paths)
    print(f"DEBUG: Total DLLs found: {total_dlls}")
    
    if total_dlls < 5:  # Minimum attendu
        print("WARNING: Very few DLLs found - this may cause runtime errors!")
        print("This could explain the 'Failed to load Python DLL' error.")
    
    return python_dll_paths


def get_demucs_data_files():
    """Récupère les fichiers de données Demucs nécessaires."""
    try:
        import demucs
        import torch
        demucs_path = Path(demucs.__file__).parent
        
        data_files = []
        
        # Fichiers de configuration
        conf_dir = demucs_path / "conf"
        if conf_dir.exists():
            for conf_file in conf_dir.rglob("*.yaml"):
                rel_path = conf_file.relative_to(demucs_path.parent)
                data_files.append((str(conf_file), str(rel_path.parent)))
        
        # Fichiers remote
        remote_dir = demucs_path / "remote"
        if remote_dir.exists():
            for remote_file in remote_dir.rglob("*"):
                if remote_file.is_file():
                    rel_path = remote_file.relative_to(demucs_path.parent)
                    data_files.append((str(remote_file), str(rel_path.parent)))
        
        # Inclure les modèles Demucs téléchargés
        print("DEBUG: Searching for Demucs models...")
        model_locations = [
            Path.home() / ".cache" / "torch" / "hub" / "checkpoints",
            Path.home() / "AppData" / "Local" / "torch" / "hub" / "checkpoints",
            Path.home() / ".torch" / "models",
        ]
        
        model_count = 0
        for cache_dir in model_locations:
            if cache_dir.exists():
                print(f"DEBUG: Searching in {cache_dir}")
                for model_file in cache_dir.glob("*.th"):
                    # Vérifier si c'est un modèle Demucs
                    if any(model_name in model_file.name for model_name in ['htdemucs', 'mdx', 'demucs']):
                        data_files.append((str(model_file), 'torch_models'))
                        model_count += 1
                        print(f"DEBUG: Including model: {model_file.name} ({model_file.stat().st_size / (1024*1024):.1f} MB)")
        
        print(f"DEBUG: Found {model_count} Demucs model files")
        if model_count == 0:
            print("WARNING: No Demucs models found! The application may not work properly.")
        
        return data_files
    except ImportError:
        return []


def create_pyinstaller_spec(onefile=False, debug=False):
    """Crée le fichier .spec pour PyInstaller."""
    print("Creation du fichier de configuration PyInstaller...")
    
    torch_paths = get_torch_paths()
    demucs_data = get_demucs_data_files()
    python_dlls = get_python_dll_paths()
    
    print(f"DLL Python detectees: {len(python_dlls)}")
    for dll_path, dest in python_dlls[:5]:  # Afficher les 5 premières
        print(f"  - {Path(dll_path).name} -> {dest}")
    if len(python_dlls) > 5:
        print(f"  ... et {len(python_dlls) - 5} autres")
    
    spec_content = f'''# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path

# Configuration de base
block_cipher = None
app_name = "RockSmithGuitarMute"

# Chemins des bibliothèques
torch_paths = {torch_paths}

# DLL Python nécessaires
python_dlls = {python_dlls}

# Données Demucs
demucs_datas = {demucs_data}

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
    hooksconfig={{}},
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
    debug={debug},
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console={debug},  # Console en mode debug
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
'''
    
    with open('rocksmith_gui.spec', 'w', encoding='utf-8') as f:
        f.write(spec_content)
    
    print("OK Fichier rocksmith_gui.spec cree!")


def build_executable(debug=False, onefile=False):
    """Compile l'exécutable avec PyInstaller."""
    print("Compilation de l'executable...")
    
    if onefile:
        print("Mode onefile active (peut resoudre les problemes de DLL)")
        print("DEBUG: Utilisation de la logique amelioree avec inclusion DLL")
        
        # Récupérer les DLL Python pour les inclure explicitement
        python_dlls = get_python_dll_paths()
        demucs_data = get_demucs_data_files()
        
        print(f"DEBUG: Trouvé {len(python_dlls)} DLL Python à inclure")
        print(f"DEBUG: Trouvé {len(demucs_data)} fichiers Demucs à inclure")
        
        # Pour onefile, utiliser directement PyInstaller sans .spec
        cmd = [
            sys.executable, '-m', 'PyInstaller',
            '--clean',
            '--noconfirm',
            '--onefile',
            '--windowed',  # Pas de console
            '--name', 'RockSmithGuitarMute',

            '--add-data', '../rs-utils;rs-utils',
            '--add-data', '../rsrtools/src/rsrtools;rsrtools', 
            '--add-data', '../demucs/demucs;demucs',
            '--add-data', '../demucs/conf;demucs/conf',
            '--add-data', '../audio2wem_windows.py;.',
        ]
        
        # Ajouter les DLL Python explicitement
        for dll_path, dest in python_dlls:
            cmd.extend(['--add-binary', f'{dll_path};{dest}'])
            
        # Ajouter les données Demucs (y compris les modèles)
        for data_path, dest in demucs_data:
            cmd.extend(['--add-data', f'{data_path};{dest}'])
        
        # Hidden imports essentiels avec focus sur NumPy
        hidden_imports = [
            'torch', 'torchaudio', 'demucs', 'demucs.separate', 'demucs.pretrained',
            'soundfile', 'numpy', 'scipy', 'tkinter', 'tkinter.ttk', 
            'tkinter.filedialog', 'tkinter.messagebox',
            'rsrtools.files.welder', 'rsrtools.files.config', 'rsrtools.files.exceptions',
            'torch.nn', 'torch.nn.functional', 'torch.optim', 'torch.utils', 'torch.utils.data',
            'torch._C', 'torch._C._nn', 'torch._C._fft', 'torch._C._linalg', 'torch._C._sparse',
            'torch.backends', 'torch.backends.cpu', 'torch.backends.mkl', 'torch.backends.mkldnn',
            'torchaudio.transforms', 'torchaudio.functional', 'torchaudio.models', 
            'torchaudio._extension', 'torchaudio.io',
            'demucs.hdemucs', 'demucs.htdemucs', 'demucs.wdemucs', 'demucs.transformer',
            'demucs.spec', 'demucs.states', 'demucs.utils', 'demucs.wav', 'demucs.audio',
            'demucs.repo', 'demucs.apply', 'demucs.api',
            # Fix critique pour NumPy dans l'environnement CI
            'numpy.core', 'numpy.core.multiarray', 'numpy.core._multiarray_umath',
            'numpy.core.multiarray_umath', 'numpy.core.numeric', 'numpy.core.umath',
            'numpy._typing', 'numpy._typing._array_like', 'numpy._typing._dtype_like',
            'numpy.lib', 'numpy.lib.recfunctions', 'numpy.ma', 'numpy.ma.core',
            'numpy.random', 'numpy.random._pickle', 'numpy.linalg', 'numpy.fft',
            'numpy.core._methods', 'numpy.core.arrayprint', 'numpy.core.fromnumeric',
            'numpy.core.function_base', 'numpy.core.getlimits', 'numpy.core.shape_base',
            # Dépendances supplémentaires pour Demucs
            'diffq', 'einops', 'julius', 'openunmix', 'tqdm', 'omegaconf',
            'hydra', 'hydra.core', 'hydra.core.config_store', 'hydra.core.global_hydra',
            'dora', 'lameenc', 'packaging', 'setuptools', 'pkg_resources',
            # Imports supplémentaires pour résoudre les erreurs CI
            'typing_extensions', 'importlib_metadata', 'importlib_resources'
        ]
        
        for import_name in hidden_imports:
            cmd.extend(['--hidden-import', import_name])
        
        cmd.append('../gui/gui_main.py')
    else:
        # Pour onedir, utiliser le fichier .spec
        cmd = [
            sys.executable, '-m', 'PyInstaller',
            '--clean',
            '--noconfirm'
        ]
        
        # Pour le mode debug avec .spec, on doit modifier le .spec lui-même
        if debug:
            cmd.extend(['--log-level', 'DEBUG'])
        
        cmd.append('rocksmith_gui.spec')
    
    print(f"Commande: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("OK Compilation reussie!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"ERREUR Erreur de compilation:")
        print(f"STDOUT: {e.stdout}")
        print(f"STDERR: {e.stderr}")
        return False


def create_installer_script():
    """Crée un script d'installation simple."""
    print("Creation du script d'installation...")
    
    installer_content = '''@echo off
echo ========================================
echo   RockSmith Guitar Mute - Installation
echo ========================================
echo.

REM Vérifier si le dossier de destination existe
set "INSTALL_DIR=%PROGRAMFILES%\\RockSmithGuitarMute"

echo Installation dans: %INSTALL_DIR%
echo.

REM Créer le dossier d'installation
if not exist "%INSTALL_DIR%" (
    mkdir "%INSTALL_DIR%"
)

REM Copier les fichiers
echo Copie des fichiers...
xcopy /E /I /Y "RockSmithGuitarMute\\*" "%INSTALL_DIR%\\"

REM Créer un raccourci sur le bureau
echo Création du raccourci...
set "DESKTOP=%USERPROFILE%\\Desktop"
set "SHORTCUT=%DESKTOP%\\RockSmith Guitar Mute.lnk"

powershell -Command "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%SHORTCUT%'); $Shortcut.TargetPath = '%INSTALL_DIR%\\RockSmithGuitarMute.exe'; $Shortcut.WorkingDirectory = '%INSTALL_DIR%'; $Shortcut.Save()"

echo.
echo Installation terminee!
echo.
echo Le programme est installé dans: %INSTALL_DIR%
echo Un raccourci a été créé sur le bureau.
echo.
pause
'''
    
    with open('dist/install.bat', 'w', encoding='utf-8') as f:
        f.write(installer_content)
    
    print("OK Script d'installation cree: dist/install.bat")


def create_readme():
    """Crée un fichier README pour la distribution."""
    print("Creation du README de distribution...")
    
    readme_content = '''# RockSmith Guitar Mute - Version Standalone

## Description
RockSmith Guitar Mute est un outil qui utilise l'intelligence artificielle pour supprimer les pistes de guitare des fichiers PSARC de Rocksmith 2014, créant ainsi des backing tracks pour la pratique.

## Installation

### Installation automatique
1. Exécutez `install.bat` en tant qu'administrateur
2. Le programme sera installé dans `C:\\Program Files\\RockSmithGuitarMute`
3. Un raccourci sera créé sur le bureau

### Installation manuelle
1. Extrayez tous les fichiers dans un dossier de votre choix
2. Exécutez `RockSmithGuitarMute.exe`

## Utilisation

### Interface Graphique
1. Lancez `RockSmithGuitarMute.exe`
2. Sélectionnez un fichier PSARC ou un dossier contenant des fichiers PSARC
3. Choisissez un dossier de sortie
4. Configurez les options selon vos besoins
5. Cliquez sur "Démarrer le traitement"

### Options disponibles
- **Modèle Demucs**: Choisissez le modèle d'IA (htdemucs_6s recommandé)
- **Périphérique**: Auto (recommandé), CPU ou CUDA (si GPU compatible)
- **Nombre de processus**: Ajustez selon votre CPU
- **Écrasement**: Autorise le remplacement des fichiers existants

## Configuration système requise
- Windows 10/11 (64-bit)
- 8 GB RAM minimum (16 GB recommandé)
- 2 GB d'espace disque libre
- Processeur multi-cœurs recommandé
- GPU NVIDIA compatible CUDA (optionnel, pour accélération)

## Dépannage

### L'application ne démarre pas
- Vérifiez que vous avez les droits d'administrateur
- Assurez-vous que Windows Defender n'a pas mis en quarantaine l'exécutable
- Installez Microsoft Visual C++ Redistributable si nécessaire

### Traitement lent
- Utilisez un GPU NVIDIA compatible CUDA si disponible
- Réduisez le nombre de processus parallèles
- Fermez les autres applications gourmandes en ressources

### Erreurs de traitement
- Vérifiez que les fichiers PSARC ne sont pas corrompus
- Assurez-vous d'avoir suffisamment d'espace disque
- Consultez les logs dans l'interface pour plus de détails

## Support
Pour obtenir de l'aide ou signaler des problèmes, consultez la documentation du projet sur GitHub.

## Licence
Ce logiciel est distribué sous licence open source. Voir le fichier LICENSE pour plus de détails.
'''
    
    with open('dist/README.txt', 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    print("OK README cree: dist/README.txt")


def optimize_distribution():
    """Optimise la distribution en supprimant les fichiers inutiles."""
    print("Optimisation de la distribution...")
    
    dist_dir = Path('dist/RockSmithGuitarMute')
    if not dist_dir.exists():
        print("ERREUR Dossier de distribution non trouve!")
        return
    
    # Fichiers et dossiers à supprimer pour réduire la taille
    patterns_to_remove = [
        '**/*.pyc',
        '**/__pycache__',
        '**/test*',
        '**/tests',
        '**/examples',
        '**/docs',
        '**/*.md',
        '**/LICENSE*',
        '**/CHANGELOG*',
        '**/README*',
        # Garder seulement notre README
    ]
    
    removed_size = 0
    
    for pattern in patterns_to_remove:
        for item in dist_dir.glob(pattern):
            if item.name == 'README.txt':  # Garder notre README
                continue
                
            try:
                if item.is_file():
                    size = item.stat().st_size
                    item.unlink()
                    removed_size += size
                elif item.is_dir():
                    size = sum(f.stat().st_size for f in item.rglob('*') if f.is_file())
                    shutil.rmtree(item)
                    removed_size += size
            except Exception as e:
                print(f"  ATTENTION Impossible de supprimer {item}: {e}")
    
    print(f"OK Optimisation terminee! {removed_size / (1024*1024):.1f} MB economises")


def main():
    """Fonction principale."""
    parser = argparse.ArgumentParser(description="Script de compilation pour Windows")
    parser.add_argument('--debug', action='store_true', help='Compilation en mode debug')
    parser.add_argument('--clean-only', action='store_true', help='Nettoyer seulement')
    parser.add_argument('--no-optimize', action='store_true', help='Pas d\'optimisation')
    parser.add_argument('--onefile', action='store_true', help='Créer un exécutable en un seul fichier (résout les problèmes de DLL)')
    parser.add_argument('--optimize', action='store_true', help='Optimiser la taille en excluant les dépendances inutiles (garde CUDA)')
    
    args = parser.parse_args()
    
    print("RockSmith Guitar Mute - Compilation Windows")
    print("=" * 50)
    
    # Nettoyage
    clean_build_dirs()
    
    if args.clean_only:
        print("OK Nettoyage termine!")
        return
    
    # Mode optimisation - utiliser notre logique améliorée au lieu du script externe
    if args.optimize:
        print("Mode optimisation active - reduction de la taille avec DLL incluses")
        print("Utilisation de la logique d'optimisation integree...")
        # Ne pas utiliser le script externe, continuer avec notre logique améliorée
    
    # Vérification des dépendances
    if not check_dependencies():
        sys.exit(1)
    
    # Création du fichier spec
    create_pyinstaller_spec(onefile=args.onefile, debug=args.debug)
    
    # Compilation avec nos améliorations DLL
    print("Compilation avec inclusion forcee des DLL Python...")
    if not build_executable(debug=args.debug, onefile=args.onefile):
        print("ERREUR Echec de la compilation!")
        sys.exit(1)
    
    # Vérification du résultat (Windows a toujours l'extension .exe)
    import platform
    exe_extension = '.exe' if platform.system() == 'Windows' else ''
    
    if args.onefile:
        exe_path = Path(f'dist/RockSmithGuitarMute{exe_extension}')
    else:
        exe_path = Path(f'dist/RockSmithGuitarMute/RockSmithGuitarMute{exe_extension}')
    
    if not exe_path.exists():
        print("ERREUR Executable non trouve apres compilation!")
        print(f"Chemin attendu: {exe_path}")
        
        # Debug: lister ce qui a été créé
        print("Contenu de dist/:")
        if Path('dist').exists():
            for item in Path('dist').rglob('*'):
                print(f"  {item}")
        sys.exit(1)
    
    print(f"OK Executable cree: {exe_path}")
    print(f"   Taille: {exe_path.stat().st_size / (1024*1024):.1f} MB")
    
    # Optimisation
    if not args.no_optimize:
        optimize_distribution()
    
    # Création des fichiers additionnels
    create_installer_script()
    create_readme()
    
    print("\nOK Compilation terminee avec succes!")
    print(f"Distribution disponible dans: {Path('dist').absolute()}")
    print("\nFichiers crees:")
    print("  - RockSmithGuitarMute.exe (application principale)")
    print("  - install.bat (script d'installation)")
    print("  - README.txt (documentation)")
    
    print("\nPour distribuer:")
    print("  1. Compressez le dossier 'dist' en ZIP")
    print("  2. Ou utilisez install.bat pour une installation système")


if __name__ == "__main__":
    main()
