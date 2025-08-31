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
    """Récupère les chemins des DLL Python nécessaires."""
    import sys
    import os
    
    python_dll_paths = []
    
    # Chemin de l'installation Python
    python_dir = Path(sys.executable).parent
    
    # DLL Python principale
    python_version = f"python{sys.version_info.major}{sys.version_info.minor}"
    python_dll = python_dir / f"{python_version}.dll"
    
    if python_dll.exists():
        python_dll_paths.append((str(python_dll), '.'))
    
    # DLLs dans le dossier DLLs
    dlls_dir = python_dir / "DLLs"
    if dlls_dir.exists():
        for dll_file in dlls_dir.glob("*.dll"):
            python_dll_paths.append((str(dll_file), 'DLLs'))
    
    # Bibliothèques système importantes
    system_dlls = [
        "vcruntime140.dll",
        "msvcp140.dll", 
        "api-ms-win-crt-runtime-l1-1-0.dll"
    ]
    
    # Chercher dans System32
    system32 = Path(os.environ.get('SYSTEMROOT', 'C:\\Windows')) / "System32"
    for dll_name in system_dlls:
        dll_path = system32 / dll_name
        if dll_path.exists():
            python_dll_paths.append((str(dll_path), '.'))
    
    return python_dll_paths

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
    """Compile un exécutable onefile optimisé."""
    print("Compilation optimisee pour reduire la taille...")
    print("Support CUDA conserve")
    
    excludes = get_optimized_excludes()
    hidden_imports = get_optimized_hidden_imports()
    
    print(f"Exclusion de {len(excludes)} modules inutiles")
    print(f"Inclusion de {len(hidden_imports)} imports essentiels")
    
    # Construire la commande PyInstaller
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--clean', '--noconfirm', '--onefile', '--windowed',
        '--name', 'RockSmithGuitarMute_Optimized',
        
        # Données nécessaires
        '--add-data', '../rs-utils;rs-utils',
        '--add-data', '../rsrtools/src/rsrtools;rsrtools', 
        '--add-data', '../demucs/demucs;demucs',
        '--add-data', '../demucs/conf;demucs/conf',
        '--add-data', '../audio2wem_windows.py;.',
        
        # Optimisations UPX
        '--upx-dir', 'upx',  # Si UPX est disponible
        
        # Optimisations de taille
        '--strip',  # Supprimer les symboles de debug
        '--noupx',  # Désactiver UPX par défaut (peut causer des problèmes)
    ]
    
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
        exe_path = Path('dist/RockSmithGuitarMute_Optimized.exe')
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
        exe_path = Path('dist/RockSmithGuitarMute_Optimized.exe')
        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            print(f"\nResultat de l'optimisation:")
            print(f"  Executable optimise: {exe_path}")
            print(f"  Taille finale: {size_mb:.1f} MB")
            print(f"  Reduction par rapport a la version originale (416 MB): {416 - size_mb:.1f} MB")
            print(f"  Pourcentage de reduction: {((416 - size_mb) / 416) * 100:.1f}%")
        
        print("\nOptimisation reussie!")
        print("Testez l'executable pour verifier qu'il fonctionne correctement")
        print("Lancez: dist\\RockSmithGuitarMute_Optimized.exe")
    else:
        print("\nEchec de l'optimisation")
        print("Utilisez la version originale ou ajustez les exclusions")

if __name__ == "__main__":
    main()
