#!/usr/bin/env python3
"""
Test script pour vérifier le système de logging détaillé
"""

import sys
from pathlib import Path

# Ajouter le répertoire du projet au path
sys.path.insert(0, str(Path(__file__).parent))

from rocksmith_guitar_mute import setup_logging, RocksmithGuitarMute

def test_logging_system():
    """Test du système de logging détaillé"""
    print("Test du système de logging détaillé...")
    
    # Test 1: Logging de base
    print("1. Test du logging de base...")
    setup_logging(verbose=True, log_file="test_logging.log")
    
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info("Test message INFO")
    logger.debug("Test message DEBUG") 
    logger.warning("Test message WARNING")
    logger.error("Test message ERROR")
    
    # Test 2: Créer une instance du processeur pour déclencher le logging système
    print("2. Test de l'initialisation du processeur...")
    try:
        processor = RocksmithGuitarMute(demucs_model="htdemucs_6s", device="cpu")
        logger.info("Processeur créé avec succès")
    except Exception as e:
        logger.error(f"Erreur lors de la création du processeur: {e}")
    
    # Test 3: Vérifier que le fichier de log a été créé
    log_file = Path("test_logging.log")
    if log_file.exists():
        print(f"✅ Fichier de log créé: {log_file}")
        print(f"   Taille: {log_file.stat().st_size} bytes")
        
        # Lire les premières lignes pour vérifier le contenu
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()[:20]  # Premières 20 lignes
            print("   Contenu (premières lignes):")
            for i, line in enumerate(lines, 1):
                print(f"   {i:2d}: {line.rstrip()}")
        
        return True
    else:
        print("❌ Fichier de log non créé")
        return False

if __name__ == "__main__":
    success = test_logging_system()
    
    if success:
        print("\n🎉 Test de logging réussi !")
        print("Le fichier test_logging.log contient toutes les informations de diagnostic.")
    else:
        print("\n💥 Test de logging échoué.")
    
    # Nettoyer le fichier de test
    test_log = Path("test_logging.log")
    if test_log.exists():
        print(f"\nPour voir le contenu complet, ouvrez: {test_log.absolute()}")
        print("Le fichier sera conservé pour inspection.")
