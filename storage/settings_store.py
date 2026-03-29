from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from core.models import AppSettings, WindowGeometry
from core.utils.platform_utils import get_settings_path


class SettingsStore:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or get_settings_path()
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> AppSettings:
        if not self.path.exists():
            settings = AppSettings()
            self.save(settings)
            return settings
        data = json.loads(self.path.read_text(encoding="utf-8"))
        geometry = WindowGeometry(**data.get("window_geometry", {}))
        settings_data = {key: value for key, value in data.items() if key != "window_geometry"}
        return AppSettings(window_geometry=geometry, **settings_data)

    def save(self, settings: AppSettings) -> None:
        payload = asdict(settings)
        payload["window_geometry"] = asdict(settings.window_geometry)
        self.path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
