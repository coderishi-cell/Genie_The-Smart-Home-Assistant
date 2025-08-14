import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.device_simulator import device_simulator
from typing import Dict, Any, Tuple

# Mood settings mapping moods to scenes and frontend theme variables
MOOD_SETTINGS = {
    "Relax": {
        "scene_name": "Relax",
        "frontend_theme_vars": {
            "bgGradientStart": "#0D1B2A",
            "bgGradientEnd": "#003F5C",
            "accentColor": "#00E5FF",
            "accentColorRGB": "0, 229, 255",
            "textColorPrimary": "#F8F8FF",
            "cardBgColor": "rgba(23, 37, 59, 0.5)",
            "glowColor": "#00E5FF"
        }
    },
    "Energetic": {
        "scene_name": "Energetic", 
        "frontend_theme_vars": {
            "bgGradientStart": "#FF6B35",
            "bgGradientEnd": "#F7931E",
            "accentColor": "#00FF7F",
            "accentColorRGB": "0, 255, 127",
            "textColorPrimary": "#FFFFFF",
            "cardBgColor": "rgba(255, 107, 53, 0.2)",
            "glowColor": "#00FF7F"
        }
    },
    "Movie Mode": {
        "scene_name": "Movie Mode",
        "frontend_theme_vars": {
            "bgGradientStart": "#0F0F23",
            "bgGradientEnd": "#000000",
            "accentColor": "#4B0082",
            "accentColorRGB": "75, 0, 130",
            "textColorPrimary": "#C0C0C0",
            "cardBgColor": "rgba(15, 15, 35, 0.8)",
            "glowColor": "#4B0082"
        }
    },
    "Good Morning": {
        "scene_name": "Good Morning",
        "frontend_theme_vars": {
            "bgGradientStart": "#FFE4B5",
            "bgGradientEnd": "#FFEFD5",
            "accentColor": "#FF8C00",
            "accentColorRGB": "255, 140, 0",
            "textColorPrimary": "#2F4F4F",
            "cardBgColor": "rgba(255, 228, 181, 0.4)",
            "glowColor": "#FF8C00"
        }
    },
    "Focus": {
        "scene_name": "Focus",
        "frontend_theme_vars": {
            "bgGradientStart": "#E6F3FF",
            "bgGradientEnd": "#B3D9FF",
            "accentColor": "#0066CC",
            "accentColorRGB": "0, 102, 204",
            "textColorPrimary": "#1A1A1A",
            "cardBgColor": "rgba(230, 243, 255, 0.6)",
            "glowColor": "#0066CC"
        }
    },
    "Sleep": {
        "scene_name": "Sleep",
        "frontend_theme_vars": {
            "bgGradientStart": "#191970",
            "bgGradientEnd": "#000080",
            "accentColor": "#483D8B",
            "accentColorRGB": "72, 61, 139",
            "textColorPrimary": "#E6E6FA",
            "cardBgColor": "rgba(25, 25, 112, 0.4)",
            "glowColor": "#483D8B"
        }
    }
}

class MoodEngine:
    def __init__(self):
        self.current_mood = "Relax"  # Default mood
    
    def get_available_moods(self) -> list:
        """Get list of available mood names"""
        return list(MOOD_SETTINGS.keys())
    
    def get_current_mood(self) -> str:
        """Get the current active mood"""
        return self.current_mood
    
    def set_mood(self, mood_name: str) -> Tuple[Dict[str, Any], Dict[str, Dict[str, Any]]]:
        """
        Set a new mood, apply the corresponding scene, and return theme vars and device states
        
        Returns:
            Tuple of (frontend_theme_vars, updated_device_states)
        """
        if mood_name not in MOOD_SETTINGS:
            available_moods = ", ".join(self.get_available_moods())
            raise ValueError(f"Unknown mood '{mood_name}'. Available moods: {available_moods}")
        
        # Update current mood
        self.current_mood = mood_name
        
        # Get mood settings
        mood_config = MOOD_SETTINGS[mood_name]
        
        # Apply the corresponding scene to devices
        updated_device_states = device_simulator.apply_scene(mood_config["scene_name"])
        
        # Get theme variables for frontend
        theme_vars = mood_config["frontend_theme_vars"]
        
        print(f"Mood set to '{mood_name}' with scene '{mood_config['scene_name']}'")
        
        return theme_vars, updated_device_states
    
    def get_mood_preview(self, mood_name: str) -> Dict[str, Any]:
        """Get theme variables for a mood without applying it"""
        if mood_name not in MOOD_SETTINGS:
            raise ValueError(f"Unknown mood '{mood_name}'")
        
        return MOOD_SETTINGS[mood_name]["frontend_theme_vars"]

# Global instance
mood_engine = MoodEngine() 