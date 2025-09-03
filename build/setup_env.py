# Configuration d'environnement pour l'exécution en CI Windows
# Résout les problèmes d'encodage Unicode

import os
import sys

# Forcer l'encodage UTF-8 pour stdout/stderr
if sys.platform.startswith('win'):
    # Configurer l'encodage par défaut pour Windows
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    
    # Reconfigurer stdout et stderr
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8')

print("Environment configured for UTF-8 encoding")
