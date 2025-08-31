#!/usr/bin/env python3
"""
Configuration for RockSmith Guitar Mute GUI
"""

import json
import os
from pathlib import Path
from typing import Dict, Any


class GUIConfig:
    """Gestionnaire de configuration pour l'interface graphique."""
    
    def __init__(self):
        self.config_file = Path.home() / ".rocksmith_guitar_mute" / "config.json"
        self.config_file.parent.mkdir(exist_ok=True)
        self.default_config = {
            "last_input_path": "",
            "last_output_path": "",
            "demucs_model": "htdemucs_6s",
            "device": "auto",
            "workers": os.cpu_count(),
            "overwrite_files": False,
            "window_geometry": "800x600",
            "log_level": "INFO",
            "auto_save_config": True,
            "recent_inputs": [],
            "recent_outputs": []
        }
        self.config = self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """Charge la configuration depuis le fichier."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                # Fusionner avec les valeurs par défaut pour les nouvelles clés
                merged_config = self.default_config.copy()
                merged_config.update(config)
                return merged_config
            except (json.JSONDecodeError, IOError):
                # En cas d'erreur, utiliser la configuration par défaut
                pass
        
        return self.default_config.copy()
    
    def save_config(self) -> None:
        """Sauvegarde la configuration dans le fichier."""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except IOError:
            # Ignorer les erreurs de sauvegarde
            pass
    
    def get(self, key: str, default=None):
        """Récupère une valeur de configuration."""
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Définit une valeur de configuration."""
        self.config[key] = value
        if self.config.get("auto_save_config", True):
            self.save_config()
    
    def add_recent_input(self, path: str) -> None:
        """Ajoute un chemin d'entrée aux récents."""
        recent = self.config.get("recent_inputs", [])
        if path in recent:
            recent.remove(path)
        recent.insert(0, path)
        # Garder seulement les 10 derniers
        self.config["recent_inputs"] = recent[:10]
        if self.config.get("auto_save_config", True):
            self.save_config()
    
    def add_recent_output(self, path: str) -> None:
        """Ajoute un chemin de sortie aux récents."""
        recent = self.config.get("recent_outputs", [])
        if path in recent:
            recent.remove(path)
        recent.insert(0, path)
        # Garder seulement les 10 derniers
        self.config["recent_outputs"] = recent[:10]
        if self.config.get("auto_save_config", True):
            self.save_config()
    
    def get_recent_inputs(self) -> list:
        """Récupère la liste des chemins d'entrée récents."""
        return self.config.get("recent_inputs", [])
    
    def get_recent_outputs(self) -> list:
        """Récupère la liste des chemins de sortie récents."""
        return self.config.get("recent_outputs", [])
