#!/usr/bin/env python3
"""
Configuration for RockSmith Guitar Mute GUI
"""

import json
import os
from pathlib import Path
from typing import Dict, Any


class GUIConfig:
    """Configuration manager for the graphical interface."""
    
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
        """Load configuration from file."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                # Merge with default values for new keys
                merged_config = self.default_config.copy()
                merged_config.update(config)
                return merged_config
            except (json.JSONDecodeError, IOError):
                # In case of error, use default configuration
                pass
        
        return self.default_config.copy()
    
    def save_config(self) -> None:
        """Save configuration to file."""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except IOError:
            # Ignore save errors
            pass
    
    def get(self, key: str, default=None):
        """Get a configuration value."""
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set a configuration value."""
        self.config[key] = value
        if self.config.get("auto_save_config", True):
            self.save_config()
    
    def add_recent_input(self, path: str) -> None:
        """Add an input path to recent ones."""
        recent = self.config.get("recent_inputs", [])
        if path in recent:
            recent.remove(path)
        recent.insert(0, path)
        # Keep only the last 10
        self.config["recent_inputs"] = recent[:10]
        if self.config.get("auto_save_config", True):
            self.save_config()
    
    def add_recent_output(self, path: str) -> None:
        """Add an output path to recent ones."""
        recent = self.config.get("recent_outputs", [])
        if path in recent:
            recent.remove(path)
        recent.insert(0, path)
        # Keep only the last 10
        self.config["recent_outputs"] = recent[:10]
        if self.config.get("auto_save_config", True):
            self.save_config()
    
    def get_recent_inputs(self) -> list:
        """Get the list of recent input paths."""
        return self.config.get("recent_inputs", [])
    
    def get_recent_outputs(self) -> list:
        """Get the list of recent output paths."""
        return self.config.get("recent_outputs", [])
