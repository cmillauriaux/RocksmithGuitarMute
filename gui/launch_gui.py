#!/usr/bin/env python3
"""
Script de lancement simple pour l'interface graphique RockSmith Guitar Mute
"""

import sys
import os
from pathlib import Path

def main():
    """Fonction principale de lancement."""
    print("🚀 Lancement de RockSmith Guitar Mute GUI...")
    
    # Ajouter le répertoire courant au path pour les imports
    current_dir = Path(__file__).parent
    sys.path.insert(0, str(current_dir))
    
    # Vérifier que tkinter est disponible
    try:
        import tkinter as tk
        print("✅ Tkinter disponible")
    except ImportError:
        print("❌ Erreur: Tkinter n'est pas disponible")
        print("Tkinter est normalement inclus avec Python. Réinstallez Python si nécessaire.")
        input("Appuyez sur Entrée pour fermer...")
        sys.exit(1)
    
    # Nettoyer les fichiers .pyc qui pourraient causer des conflits
    try:
        import glob
        pyc_files = glob.glob("**/*.pyc", recursive=True)
        for pyc_file in pyc_files:
            try:
                os.remove(pyc_file)
            except:
                pass  # Ignorer les erreurs de suppression
    except:
        pass  # Ignorer les erreurs de nettoyage
    
    # Importer et lancer l'interface
    try:
        from gui_main import main as gui_main
        print("✅ Interface graphique chargée")
        gui_main()
        
    except ImportError as e:
        print(f"❌ Erreur d'importation: {e}")
        print("\n🔧 Solutions possibles:")
        print("1. Installer les dépendances: pip install -r requirements.txt")
        print("2. Nettoyer les fichiers temporaires: clean.bat")
        print("3. Vérifier que tous les fichiers sont présents")
        input("\nAppuyez sur Entrée pour fermer...")
        sys.exit(1)
        
    except Exception as e:
        print(f"❌ Erreur lors du lancement: {e}")
        print(f"Type d'erreur: {type(e).__name__}")
        print("\n🔧 Essayez de:")
        print("1. Nettoyer les fichiers temporaires: clean.bat")
        print("2. Redémarrer votre ordinateur")
        print("3. Vérifier les logs pour plus de détails")
        input("\nAppuyez sur Entrée pour fermer...")
        sys.exit(1)

if __name__ == "__main__":
    main()
