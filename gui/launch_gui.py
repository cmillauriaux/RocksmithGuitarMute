#!/usr/bin/env python3
"""
Simple launch script for RockSmith Guitar Mute graphical interface
"""

import sys
import os
from pathlib import Path

def main():
    """Main launch function."""
    print("🚀 Launching RockSmith Guitar Mute GUI...")
    
    # Add current directory to path for imports
    current_dir = Path(__file__).parent
    sys.path.insert(0, str(current_dir))
    
    # Check that tkinter is available
    try:
        import tkinter as tk
        print("✅ Tkinter disponible")
    except ImportError:
        print("❌ Erreur: Tkinter n'est pas disponible")
        print("Tkinter est normalement inclus avec Python. Réinstallez Python si nécessaire.")
        input("Appuyez sur Entrée pour fermer...")
        sys.exit(1)
    
    # Check that Pillow is available for images
    try:
        from PIL import Image, ImageTk
        print("✅ Pillow disponible pour les images")
    except ImportError:
        print("⚠️ Avertissement: Pillow n'est pas installé")
        print("Le logo pourrait ne pas s'afficher. Installez Pillow avec:")
        print("pip install Pillow")
        print("L'interface continuera sans les images...")
    
    # Clean .pyc files that could cause conflicts
    try:
        import glob
        pyc_files = glob.glob("**/*.pyc", recursive=True)
        for pyc_file in pyc_files:
            try:
                os.remove(pyc_file)
            except:
                pass  # Ignore deletion errors
    except:
        pass  # Ignore cleanup errors
    
    # Import and launch interface
    try:
        from gui_main import main as gui_main
        print("✅ Interface graphique chargée")
        gui_main()
        
    except ImportError as e:
        print(f"❌ Erreur d'import: {e}")
        print("\n🔧 Solutions possibles:")
        print("1. Installer les dépendances: pip install -r requirements.txt")
        print("2. Installer Pillow pour les images: pip install Pillow")
        print("3. Nettoyer les fichiers temporaires: clean.bat")
        print("4. Vérifier que tous les fichiers sont présents")
        input("\nAppuyez sur Entrée pour fermer...")
        sys.exit(1)
        
    except Exception as e:
        print(f"❌ Erreur de lancement: {e}")
        print(f"Type d'erreur: {type(e).__name__}")
        print("\n🔧 Essayez de:")
        print("1. Nettoyer les fichiers temporaires: clean.bat")
        print("2. Redémarrer votre ordinateur")
        print("3. Consulter les logs pour plus de détails")
        input("\nAppuyez sur Entrée pour fermer...")
        sys.exit(1)

if __name__ == "__main__":
    main()
