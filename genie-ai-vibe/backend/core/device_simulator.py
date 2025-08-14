import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import db_handler
from typing import Dict, Any

# Default device states
DEFAULT_DEVICE_STATES = {
    "light_living_room": {
        "on": False,
        "brightness": 70,
        "color": "#FFD700",
        "type": "light",
        "name": "Living Room Light"
    },
    "light_kitchen": {
        "on": False,
        "brightness": 80,
        "color": "#FFFFFF",
        "type": "light",
        "name": "Kitchen Light"
    },
    "light_bedroom": {
        "on": False,
        "brightness": 60,
        "color": "#FFF8DC",
        "type": "light",
        "name": "Bedroom Light"
    },
    "ac_main": {
        "on": False,
        "temperature": 22,
        "mode": "cool",
        "fan_speed": "medium",
        "type": "ac",
        "name": "Main AC"
    },
    "blinds_living_room": {
        "open": False,
        "position": 0,
        "type": "blinds",
        "name": "Living Room Blinds"
    },
    "door_front": {
        "locked": True,
        "type": "door",
        "name": "Front Door"
    },
    "music_player": {
        "playing": False,
        "track": "None",
        "volume": 50,
        "playlist": "Chill Vibes",
        "type": "music",
        "name": "Music Player"
    },
    "security_system": {
        "armed": True,
        "mode": "home",
        "type": "security",
        "name": "Security System"
    }
}

class DeviceSimulator:
    def __init__(self):
        # Initialize database
        db_handler.init_db()
        
        # Load states from database or use defaults
        self._device_states = db_handler.get_all_device_states()
        
        # If no states in database, use defaults and save them
        if not self._device_states:
            self._device_states = DEFAULT_DEVICE_STATES.copy()
            for device_id, state in self._device_states.items():
                db_handler.upsert_device_state(device_id, state)
            print("Initialized with default device states")
        else:
            # Merge with defaults to ensure all devices exist
            for device_id, default_state in DEFAULT_DEVICE_STATES.items():
                if device_id not in self._device_states:
                    self._device_states[device_id] = default_state
                    db_handler.upsert_device_state(device_id, default_state)
            print(f"Loaded {len(self._device_states)} device states from database")

    def get_all_device_states(self) -> Dict[str, Dict[str, Any]]:
        """Get all current device states"""
        return self._device_states.copy()

    def get_device_state(self, device_id: str) -> Dict[str, Any]:
        """Get a specific device state"""
        return self._device_states.get(device_id, {})

    def update_device_state(self, device_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update a specific device state and persist to database"""
        if device_id not in self._device_states:
            raise ValueError(f"Device {device_id} not found")
        
        # Update the state
        self._device_states[device_id].update(updates)
        
        # Persist to database
        db_handler.upsert_device_state(device_id, self._device_states[device_id])
        
        print(f"Updated {device_id}: {updates}")
        return self._device_states[device_id].copy()

    def apply_scene(self, scene_name: str) -> Dict[str, Dict[str, Any]]:
        """Apply a predefined scene that changes multiple device states"""
        scene_changes = {}
        
        if scene_name == "Movie Mode":
            scene_changes = {
                "light_living_room": {"on": True, "brightness": 20, "color": "#4B0082"},
                "light_kitchen": {"on": False},
                "light_bedroom": {"on": False},
                "blinds_living_room": {"open": False, "position": 0},
                "music_player": {"playing": False},
                "ac_main": {"on": True, "temperature": 21}
            }
        
        elif scene_name == "Good Morning":
            scene_changes = {
                "light_living_room": {"on": True, "brightness": 90, "color": "#FFFDD0"},
                "light_kitchen": {"on": True, "brightness": 85, "color": "#FFFFFF"},
                "light_bedroom": {"on": True, "brightness": 70, "color": "#FFF8DC"},
                "blinds_living_room": {"open": True, "position": 100},
                "music_player": {"playing": True, "track": "Morning Relax Mix", "volume": 40},
                "ac_main": {"on": True, "temperature": 22},
                "security_system": {"armed": False, "mode": "off"}
            }
        
        elif scene_name == "Relax":
            scene_changes = {
                "light_living_room": {"on": True, "brightness": 40, "color": "#FF6B6B"},
                "light_kitchen": {"on": False},
                "light_bedroom": {"on": True, "brightness": 30, "color": "#FFB6C1"},
                "music_player": {"playing": True, "track": "Ambient Sounds", "volume": 35},
                "ac_main": {"on": True, "temperature": 23}
            }
        
        elif scene_name == "Energetic":
            scene_changes = {
                "light_living_room": {"on": True, "brightness": 100, "color": "#00FF7F"},
                "light_kitchen": {"on": True, "brightness": 100, "color": "#FFFFFF"},
                "light_bedroom": {"on": True, "brightness": 90, "color": "#87CEEB"},
                "blinds_living_room": {"open": True, "position": 100},
                "music_player": {"playing": True, "track": "Upbeat Workout Mix", "volume": 70},
                "ac_main": {"on": True, "temperature": 20}
            }
        
        elif scene_name == "Focus":
            scene_changes = {
                "light_living_room": {"on": True, "brightness": 80, "color": "#F0F8FF"},
                "light_kitchen": {"on": True, "brightness": 75, "color": "#FFFFFF"},
                "music_player": {"playing": True, "track": "Focus & Concentration", "volume": 25},
                "ac_main": {"on": True, "temperature": 21}
            }
        
        elif scene_name == "Sleep":
            scene_changes = {
                "light_living_room": {"on": False},
                "light_kitchen": {"on": False},
                "light_bedroom": {"on": True, "brightness": 10, "color": "#191970"},
                "blinds_living_room": {"open": False, "position": 0},
                "music_player": {"playing": True, "track": "Sleep Sounds", "volume": 20},
                "ac_main": {"on": True, "temperature": 20},
                "door_front": {"locked": True},
                "security_system": {"armed": True, "mode": "night"}
            }
        
        else:
            raise ValueError(f"Unknown scene: {scene_name}")
        
        # Apply all changes
        for device_id, updates in scene_changes.items():
            if device_id in self._device_states:
                self._device_states[device_id].update(updates)
                db_handler.upsert_device_state(device_id, self._device_states[device_id])
        
        print(f"Applied scene '{scene_name}' affecting {len(scene_changes)} devices")
        return self._device_states.copy()

# Global instance
device_simulator = DeviceSimulator() 