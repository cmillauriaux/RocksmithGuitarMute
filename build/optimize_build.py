#!/usr/bin/env python3
"""
Script d'optimisation pour réduire la taille de l'exécutable
Garde le support CUDA mais supprime les dépendances inutiles
"""

import sys
import os
import subprocess
from pathlib import Path

def get_python_dll_paths():
    """Récupère les chemins des DLL Python nécessaires - VERSION AMELIOREE."""
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

def get_optimized_excludes():
    """Retourne la liste des modules à exclure pour réduire la taille."""
    excludes = [
        # Packages de visualisation (pas utilisés)
        'matplotlib', 'seaborn', 'plotly', 'bokeh',
        
        # Packages de data science (pas utilisés) 
        'pandas', 'sklearn', 'scikit-learn', 'statsmodels',
        
        # Computer vision (pas utilisé)
        'cv2', 'opencv', 'PIL', 'Pillow', 'skimage',
        
        # Jupyter et notebooks
        'jupyter', 'notebook', 'IPython', 'ipykernel', 'ipywidgets',
        
        # Documentation et exemples
        'sphinx', 'docutils',
        
        # Packages optionnels de PyTorch
        'torchvision',  # Vision - pas utilisé pour audio
        'torchtext',    # Text - pas utilisé
        
        # Autres packages lourds optionnels
        'sympy',        # Mathématiques symboliques
        'networkx',     # Graphes
        'h5py',         # HDF5
        'tables',       # PyTables
    ]
    
    # NE PAS exclure pkg_resources et ses dépendances (jaraco.text, etc.)
    # NE PAS exclure setuptools (nécessaire pour pkg_resources)
    
    return excludes

def get_optimized_hidden_imports():
    """Retourne les imports cachés nécessaires (minimaux)."""
    hidden_imports = [
        # Core PyTorch (garder CUDA)
        'torch', 'torch.cuda', 'torch.nn', 'torch.optim',
        'torchaudio', 'torchaudio.transforms',
        
        # Demucs (nécessaire)
        'demucs', 'demucs.separate', 'demucs.pretrained', 'demucs.api',
        
        # Audio processing
        'soundfile', 'numpy', 'scipy.signal',
        
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
        
        # GUI
        'tkinter', 'tkinter.ttk', 'tkinter.filedialog', 'tkinter.messagebox',
        
        # System
        'threading', 'queue', 'multiprocessing', 'concurrent.futures',
        'pathlib', 'shutil', 'tempfile', 'subprocess', 'logging',
        
        # Package management (nécessaire pour éviter les erreurs)
        'pkg_resources', 'setuptools', 'jaraco.text', 'jaraco.functools',
        
        # Project specific
        'rsrtools.files.welder', 'rsrtools.files.config', 'rsrtools.files.exceptions',
    ]
    
    return hidden_imports

def build_optimized_onefile():
    """Compile un exécutable onefile optimisé AVEC DLL et modèles inclus."""
    print("Compilation optimisee pour reduire la taille...")
    print("Support CUDA conserve")
    print("Inclusion des DLL Python et modeles Demucs...")
    
    excludes = get_optimized_excludes()
    hidden_imports = get_optimized_hidden_imports()
    python_dlls = get_python_dll_paths()
    demucs_data = get_demucs_data_files()
    
    print(f"Exclusion de {len(excludes)} modules inutiles")
    print(f"Inclusion de {len(hidden_imports)} imports essentiels")
    print(f"Inclusion de {len(python_dlls)} DLL Python/système")
    print(f"Inclusion de {len(demucs_data)} fichiers Demucs (dont modèles)")
    
    # Construire la commande PyInstaller
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--clean', '--noconfirm', '--onefile', '--windowed',
        '--name', 'RockSmithGuitarMute',
        
        # Données nécessaires
        '--add-data', '../rs-utils;rs-utils',
        '--add-data', '../rsrtools/src/rsrtools;rsrtools', 
        '--add-data', '../demucs/demucs;demucs',
        '--add-data', '../demucs/conf;demucs/conf',
        '--add-data', '../audio2wem_windows.py;.',
        
        # Hook pour NumPy
        '--additional-hooks-dir', '../hooks',
        
        # Optimisations de taille (mais pas trop agressives)
        '--strip',  # Supprimer les symboles de debug
        '--noupx',  # Désactiver UPX (peut causer des problèmes avec les DLL)
    ]
    
    # Ajouter les DLL Python explicitement
    for dll_path, dest in python_dlls:
        cmd.extend(['--add-binary', f'{dll_path};{dest}'])
        
    # Ajouter les données Demucs (y compris les modèles)
    for data_path, dest in demucs_data:
        cmd.extend(['--add-data', f'{data_path};{dest}'])
    
    # Ajouter les exclusions
    for exclude in excludes:
        cmd.extend(['--exclude-module', exclude])
    
    # Ajouter les imports cachés
    for hidden in hidden_imports:
        cmd.extend(['--hidden-import', hidden])
    
    # Fichier source
    cmd.append('../gui/gui_main.py')
    
    print(f"\nCommande de compilation:")
    print(" ".join(cmd[:10]) + " ...")  # Afficher le début
    
    try:
        print("\nCompilation en cours (peut prendre plusieurs minutes)...")
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("Compilation optimisee reussie!")
        
        # Vérifier le résultat
        exe_path = Path('dist/RockSmithGuitarMute.exe')
        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            print(f"Executable cree: {exe_path}")
            print(f"Taille: {size_mb:.1f} MB")
            return True
        else:
            print("Executable non trouve apres compilation")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"Erreur de compilation:")
        print(f"STDOUT: {e.stdout}")
        print(f"STDERR: {e.stderr}")
        return False

# Fonctions supprimées : build_minimal_spec, compile_with_spec, compare_sizes
# Ces fonctions étaient liées à la version minimale qui n'apportait pas d'avantage

def main():
    """Fonction principale d'optimisation."""
    print("Optimisation de la taille d'executable")
    print("Conservation du support CUDA")
    print("=" * 50)
    
    # Compilation directe optimisée (seule méthode conservée)
    print("\nCompilation optimisee")
    success = build_optimized_onefile()
    
    # Affichage du résultat
    if success:
        exe_path = Path('dist/RockSmithGuitarMute.exe')
        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            print(f"\nResultat de l'optimisation:")
            print(f"  Executable optimise: {exe_path}")
            print(f"  Taille finale: {size_mb:.1f} MB")
            print(f"  Reduction par rapport a la version originale (416 MB): {416 - size_mb:.1f} MB")
            print(f"  Pourcentage de reduction: {((416 - size_mb) / 416) * 100:.1f}%")
        
        print("\nOptimisation reussie!")
        print("Testez l'executable pour verifier qu'il fonctionne correctement")
        print("Lancez: dist\\RockSmithGuitarMute.exe")
    else:
        print("\nEchec de l'optimisation")
        print("Utilisez la version originale ou ajustez les exclusions")

if __name__ == "__main__":
    main()
