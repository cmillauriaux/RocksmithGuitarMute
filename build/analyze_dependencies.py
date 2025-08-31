#!/usr/bin/env python3
"""
Script d'analyse des dépendances pour optimiser la taille de l'exécutable
"""

import sys
import os
import importlib
import pkgutil
from pathlib import Path
import subprocess

def get_package_size(package_name):
    """Estime la taille d'un package installé."""
    try:
        import pkg_resources
        dist = pkg_resources.get_distribution(package_name)
        location = Path(dist.location)
        
        if package_name in ['torch', 'torchaudio']:
            # Pour PyTorch, chercher dans le dossier spécifique
            torch_path = location / package_name
            if torch_path.exists():
                size = sum(f.stat().st_size for f in torch_path.rglob('*') if f.is_file())
                return size / (1024 * 1024)  # MB
        
        # Pour les autres packages
        if location.exists():
            size = sum(f.stat().st_size for f in location.rglob('*') if f.is_file())
            return size / (1024 * 1024)  # MB
            
    except Exception as e:
        print(f"Erreur pour {package_name}: {e}")
    
    return 0

def analyze_imports():
    """Analyse les imports utilisés dans le projet."""
    print("🔍 Analyse des imports dans le projet...")
    
    # Fichiers Python du projet
    python_files = [
        'rocksmith_guitar_mute.py',
        'gui_main.py',
        'gui_config.py',
        'launch_gui.py',
        'audio2wem_windows.py'
    ]
    
    used_imports = set()
    
    for file_path in python_files:
        if Path(file_path).exists():
            print(f"  📄 Analyse de {file_path}")
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Extraire les imports
                lines = content.split('\n')
                for line in lines:
                    line = line.strip()
                    if line.startswith('import ') or line.startswith('from '):
                        # Nettoyer la ligne d'import
                        if line.startswith('import '):
                            module = line.replace('import ', '').split()[0].split('.')[0]
                        elif line.startswith('from '):
                            module = line.replace('from ', '').split()[0].split('.')[0]
                        
                        used_imports.add(module)
                        
            except Exception as e:
                print(f"    ❌ Erreur lecture {file_path}: {e}")
    
    return used_imports

def analyze_package_dependencies():
    """Analyse les dépendances des packages principaux."""
    print("\n📦 Analyse des tailles de packages...")
    
    # Packages principaux à analyser
    packages = [
        'torch', 'torchaudio', 'demucs', 'soundfile', 'numpy', 'scipy',
        'librosa', 'matplotlib', 'pandas', 'sklearn', 'cv2', 'PIL',
        'jupyter', 'notebook', 'IPython', 'pytest', 'setuptools'
    ]
    
    package_sizes = []
    
    for package in packages:
        try:
            # Tenter d'importer pour vérifier la présence
            importlib.import_module(package)
            size = get_package_size(package)
            package_sizes.append((package, size, True))  # True = installé
            print(f"  ✅ {package:<15} : {size:>8.1f} MB")
        except ImportError:
            package_sizes.append((package, 0, False))  # False = non installé
            print(f"  ❌ {package:<15} : non installé")
        except Exception as e:
            print(f"  ⚠️  {package:<15} : erreur - {e}")
    
    return package_sizes

def check_cuda_requirements():
    """Vérifie les exigences CUDA."""
    print("\n🎮 Analyse du support CUDA...")
    
    try:
        import torch
        print(f"  PyTorch version: {torch.__version__}")
        print(f"  CUDA disponible: {torch.cuda.is_available()}")
        
        if torch.cuda.is_available():
            print(f"  Version CUDA: {torch.version.cuda}")
            print(f"  Nombre de GPUs: {torch.cuda.device_count()}")
            for i in range(torch.cuda.device_count()):
                print(f"    GPU {i}: {torch.cuda.get_device_name(i)}")
        else:
            print("  ⚠️  CUDA non disponible - version CPU-only détectée")
            print("  💡 Pour CUDA: pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu118")
            
    except ImportError:
        print("  ❌ PyTorch non installé")

def identify_removable_packages():
    """Identifie les packages qui peuvent être supprimés."""
    print("\n🗑️  Packages potentiellement supprimables...")
    
    # Packages souvent inclus mais pas nécessaires pour notre usage
    removable = [
        ('matplotlib', 'Graphiques - pas utilisé dans l\'interface'),
        ('pandas', 'DataFrames - pas utilisé'),
        ('sklearn', 'Machine Learning - pas utilisé'),
        ('cv2', 'Computer Vision - pas utilisé'),
        ('PIL', 'Images - pas utilisé'),
        ('jupyter', 'Notebooks - pas utilisé'),
        ('notebook', 'Notebooks - pas utilisé'),
        ('IPython', 'Console interactive - pas utilisé'),
        ('pytest', 'Tests - pas nécessaire en production'),
        ('setuptools', 'Installation - pas nécessaire en production'),
    ]
    
    for package, reason in removable:
        try:
            importlib.import_module(package)
            size = get_package_size(package)
            print(f"  🗑️  {package:<15} : {size:>8.1f} MB - {reason}")
        except ImportError:
            print(f"  ✅ {package:<15} : déjà absent")

def analyze_torch_components():
    """Analyse les composants PyTorch pour identifier les parties inutiles."""
    print("\n🔥 Analyse des composants PyTorch...")
    
    try:
        import torch
        torch_path = Path(torch.__file__).parent
        
        # Analyser les sous-dossiers de PyTorch
        subdirs = [d for d in torch_path.iterdir() if d.is_dir()]
        
        torch_components = []
        
        for subdir in subdirs:
            try:
                size = sum(f.stat().st_size for f in subdir.rglob('*') if f.is_file())
                size_mb = size / (1024 * 1024)
                torch_components.append((subdir.name, size_mb))
            except:
                pass
        
        # Trier par taille
        torch_components.sort(key=lambda x: x[1], reverse=True)
        
        print("  Composants PyTorch par taille:")
        for component, size in torch_components[:10]:  # Top 10
            print(f"    {component:<20} : {size:>8.1f} MB")
            
    except ImportError:
        print("  ❌ PyTorch non disponible pour analyse")

def generate_optimization_recommendations():
    """Génère des recommandations d'optimisation."""
    print("\n💡 Recommandations d'optimisation...")
    
    print("  1. 🎯 Exclusions PyInstaller:")
    print("     --exclude-module matplotlib")
    print("     --exclude-module pandas") 
    print("     --exclude-module sklearn")
    print("     --exclude-module cv2")
    print("     --exclude-module PIL")
    print("     --exclude-module jupyter")
    print("     --exclude-module notebook")
    print("     --exclude-module IPython")
    
    print("\n  2. 🔥 Optimisations PyTorch:")
    print("     - Garder seulement les backends nécessaires")
    print("     - Exclure les outils de développement")
    print("     - Optimiser les bibliothèques CUDA")
    
    print("\n  3. 📦 Optimisations générales:")
    print("     - Utiliser UPX pour compresser l'exécutable")
    print("     - Exclure les fichiers de debug")
    print("     - Supprimer les documentations intégrées")

def main():
    """Fonction principale d'analyse."""
    print("🔍 Analyse des dépendances - RockSmith Guitar Mute")
    print("=" * 60)
    
    # Analyser les imports utilisés
    used_imports = analyze_imports()
    print(f"\n📋 Imports détectés dans le projet: {len(used_imports)}")
    for imp in sorted(used_imports):
        print(f"  - {imp}")
    
    # Analyser les tailles des packages
    package_sizes = analyze_package_dependencies()
    
    # Vérifier CUDA
    check_cuda_requirements()
    
    # Identifier les packages supprimables
    identify_removable_packages()
    
    # Analyser PyTorch en détail
    analyze_torch_components()
    
    # Générer les recommandations
    generate_optimization_recommendations()
    
    print("\n" + "=" * 60)
    print("✅ Analyse terminée!")

if __name__ == "__main__":
    main()
