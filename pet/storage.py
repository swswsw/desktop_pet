"""Settings and state persistence for desktop sheep pet."""

import json
from pathlib import Path

DEFAULT_SETTINGS = {
    "pet_name": "Fluffy",
    "wool_color": "white",
    "accessory": "none",
    "sound_muted": False,
    "scale": 3,
    "behavior_mode": "wander",
    "show_thoughts": True,
    "happiness": 85,
    "hunger": 75,
    "energy": 90,
    "wool_puff": 60,
    "sheared": False,
}

CONFIG_FILE = Path.home() / ".config" / "desktop_sheep_pet" / "settings.json"


def load_settings() -> dict:
    """Load settings from user's config directory, returning defaults if not found."""
    if not CONFIG_FILE.exists():
        return dict(DEFAULT_SETTINGS)

    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            merged = dict(DEFAULT_SETTINGS)
            merged.update(data)
            return merged
    except Exception as e:
        print(f"[Storage] Failed to load settings: {e}")
        return dict(DEFAULT_SETTINGS)


def save_settings(data: dict):
    """Save settings dictionary to disk."""
    try:
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"[Storage] Failed to save settings: {e}")
