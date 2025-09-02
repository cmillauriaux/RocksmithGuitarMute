
#!/usr/bin/env python3
"""
Hook PyInstaller pour PyTorch - Inclut toutes les dépendances critiques
Remplace le hook d'exclusion par un hook d'inclusion pour le CI
"""

from PyInstaller.utils.hooks import collect_submodules, collect_data_files, collect_dynamic_libs
import os

# Collecter tous les sous-modules PyTorch critiques
hiddenimports = [
    'torch',
    'torch._C',
    'torch._C._nn',
    'torch._C._fft', 
    'torch._C._linalg',
    'torch._C._sparse',
    'torch.backends',
    'torch.backends.cpu',
    'torch.backends.mkl',
    'torch.backends.mkldnn',
    'torch.nn',
    'torch.nn.functional',
    'torch.optim',
    'torch.utils',
    'torch.utils.data',
    # Modules supplémentaires pour la compatibilité CI
    'torch.jit',
    'torch.autograd',
    'torch.distributions',
]

# Collecter automatiquement les sous-modules
try:
    auto_imports = collect_submodules('torch')
    hiddenimports.extend(auto_imports)
except:
    pass

# Collecter les fichiers de données et les bibliothèques dynamiques
try:
    datas = collect_data_files('torch')
    binaries = collect_dynamic_libs('torch')
    
    # Debug: afficher les DLL trouvées
    if binaries:
        print(f"PyInstaller hook-torch: Found {len(binaries)} torch binaries")
    else:
        print("PyInstaller hook-torch: Warning - No torch binaries found")
except:
    datas = []
    binaries = []

# NE PAS utiliser excludedimports pour éviter les problèmes
