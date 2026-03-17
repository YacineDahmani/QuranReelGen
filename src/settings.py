"""
Persistent user settings for QuranReelGen.
Settings are stored as a JSON file in the user's app data directory.
On first run, a setup wizard guides the user through configuration.
"""
import os
import json
import sys
import platform

APP_NAME = "QuranReelGen"
SETTINGS_VERSION = 1

def get_settings_dir():
    """Get the platform-appropriate settings directory."""
    if platform.system() == "Windows":
        base = os.environ.get("APPDATA", os.path.expanduser("~"))
    elif platform.system() == "Darwin":
        base = os.path.join(os.path.expanduser("~"), "Library", "Application Support")
    else:
        base = os.environ.get("XDG_CONFIG_HOME", os.path.join(os.path.expanduser("~"), ".config"))
    
    settings_dir = os.path.join(base, APP_NAME)
    os.makedirs(settings_dir, exist_ok=True)
    return settings_dir


def get_settings_path():
    return os.path.join(get_settings_dir(), "settings.json")


DEFAULT_SETTINGS = {
    "version": SETTINGS_VERSION,
    "output_dir": "",
    "default_reciter": "ar.alafasy",
    "default_orientation": "vertical",
    "default_bg_type": "color",
    "default_bg_value": "#000000",
    "default_font_size": 100,
    "default_font_color": "#FFFFFF",
    "default_fps": 24,
    "default_video_quality": "ultrafast",
    "include_translation": False,
    "max_ayahs": 50,
    "first_run_complete": False,
}


def load_settings() -> dict:
    """Load settings from disk. Returns default settings if file doesn't exist."""
    path = get_settings_path()
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Merge with defaults so new keys are always present
            merged = {**DEFAULT_SETTINGS, **data}
            return merged
        except (json.JSONDecodeError, IOError):
            return dict(DEFAULT_SETTINGS)
    return dict(DEFAULT_SETTINGS)


def save_settings(settings: dict):
    """Save settings to disk."""
    path = get_settings_path()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2, ensure_ascii=False)


def is_first_run() -> bool:
    """Check if this is the first time the user is running the app."""
    settings = load_settings()
    return not settings.get("first_run_complete", False)


def reset_settings():
    """Reset settings to defaults."""
    save_settings(dict(DEFAULT_SETTINGS))
