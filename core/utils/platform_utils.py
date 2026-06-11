from __future__ import annotations

import os
import platform
import tempfile
from pathlib import Path


APP_NAME = "WorkPulse"


def _can_write_dir(path: Path) -> bool:
    try:
        path.mkdir(parents=True, exist_ok=True)
        probe = path / ".write_probe"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink(missing_ok=True)
        return True
    except OSError:
        return False


def is_macos() -> bool:
    return platform.system() == "Darwin"


def is_linux() -> bool:
    return platform.system() == "Linux"


def is_windows() -> bool:
    return platform.system() == "Windows"


def get_app_data_dir() -> Path:
    override = os.getenv("WORKPULSE_DATA_DIR")
    if override:
        path = Path(override).expanduser()
        if _can_write_dir(path):
            return path
        raise OSError(f"WORKPULSE_DATA_DIR is not writable: {path}")

    if is_macos():
        preferred = Path.home() / "Library" / "Application Support" / APP_NAME
    elif is_windows():
        base = os.getenv("LOCALAPPDATA") or os.getenv("APPDATA")
        preferred = Path(base) / APP_NAME if base else Path.home() / "AppData" / "Local" / APP_NAME
    else:
        xdg_data = os.getenv("XDG_DATA_HOME")
        preferred = Path(xdg_data) / APP_NAME.lower() if xdg_data else Path.home() / ".local" / "share" / APP_NAME.lower()

    if _can_write_dir(preferred):
        return preferred

    fallback = Path(tempfile.gettempdir()) / APP_NAME.lower()
    if not _can_write_dir(fallback):
        raise OSError(f"Fallback app data dir is not writable: {fallback}")
    return fallback


def get_log_dir() -> Path:
    return get_app_data_dir() / "logs"


def get_db_path() -> Path:
    return get_app_data_dir() / "workpulse.db"


def get_settings_path() -> Path:
    return get_app_data_dir() / "settings.json"


def default_window_geometry() -> dict[str, float | bool]:
    if is_macos():
        return {
            "width": 1280,
            "height": 860,
            "left": 780,
            "top": 80,
            "always_on_top": False,
        }
    return {
        "width": 1220,
        "height": 860,
        "left": 48,
        "top": 64,
        "always_on_top": False,
    }
