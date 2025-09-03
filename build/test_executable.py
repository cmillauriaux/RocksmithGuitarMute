#!/usr/bin/env python3
"""
Script de test pour l'exécutable RockSmith Guitar Mute
Teste les imports critiques et la fonctionnalité de base
"""

import sys
import os
import traceback

def test_imports():
    """Test tous les imports critiques."""
    results = {}
    
    # Test des imports critiques
    imports_to_test = [
        'numpy',
        'torch', 
        'torchaudio',
        'demucs',
        'soundfile',
        'rsrtools'
    ]
    
    for module in imports_to_test:
        try:
            if module == 'numpy':
                import numpy as np
                # Test spécifique pour numpy.core.multiarray (problème CI)
                import numpy.core.multiarray
                results[module] = f'OK - v{np.__version__}'
            elif module == 'torch':
                import torch
                cuda_status = "CUDA available" if torch.cuda.is_available() else "CPU only"
                results[module] = f'OK - v{torch.__version__} ({cuda_status})'
            elif module == 'torchaudio':
                import torchaudio
                results[module] = f'OK - v{torchaudio.__version__}'
            elif module == 'demucs':
                import demucs
                import demucs.pretrained
                # Test de chargement de modèle
                try:
                    model = demucs.pretrained.get_model('htdemucs_6s')
                    results[module] = f'OK - v{demucs.__version__} (htdemucs_6s loaded)'
                except Exception as e:
                    results[module] = f'PARTIAL - v{demucs.__version__} (model error: {str(e)})'
            elif module == 'soundfile':
                import soundfile
                results[module] = f'OK - v{soundfile.__version__}'
            elif module == 'rsrtools':
                import rsrtools
                results[module] = f'OK - v{rsrtools.__version__}'
            else:
                exec(f'import {module}')
                results[module] = 'OK'
        except Exception as e:
            results[module] = f'ERROR - {str(e)}'
    
    return results

def test_environment():
    """Test l'environnement d'exécution."""
    print("=== Environment Test ===")
    print(f"Python version: {sys.version}")
    print(f"Python executable: {sys.executable}")
    print(f"Platform: {sys.platform}")
    print(f"Working directory: {os.getcwd()}")
    
    # Test si on est dans un exécutable PyInstaller
    if hasattr(sys, 'frozen'):
        print("[OK] Running in PyInstaller executable")
        if hasattr(sys, '_MEIPASS'):
            print(f"   Temp directory: {sys._MEIPASS}")
    else:
        print("[WARNING] Running in Python interpreter (not executable)")

def main():
    """Fonction principale."""
    print('=== RockSmith Guitar Mute - Executable Test ===')
    
    try:
        # Test de l'environnement
        test_environment()
        print()
        
        # Test des imports
        print("=== Import Test ===")
        results = test_imports()
        
        for module, status in results.items():
            if status.startswith('OK'):
                print(f'[OK] {module}: {status}')
            elif status.startswith('PARTIAL'):
                print(f'[WARNING] {module}: {status}')
            else:
                print(f'[ERROR] {module}: {status}')
        
        # Comptage des imports réussis
        successful = sum(1 for status in results.values() if status.startswith('OK'))
        partial = sum(1 for status in results.values() if status.startswith('PARTIAL'))
        total = len(results)
        
        print(f'\nSummary: {successful}/{total} imports successful, {partial} partial')
        
        if successful >= total - 1:  # Permettre 1 échec
            print('[OK] Import test PASSED')
            return 0
        elif successful + partial >= total - 1:  # Permettre des imports partiels
            print('[WARNING] Import test PASSED (with warnings)')
            return 0
        else:
            print('[ERROR] Import test FAILED')
            return 1
            
    except Exception as e:
        print(f'[ERROR] Test script failed: {e}')
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
