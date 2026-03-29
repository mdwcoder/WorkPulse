from __future__ import annotations

from core.models import AppSettings, WindowGeometry
from core.utils.platform_utils import default_window_geometry
from storage.settings_store import SettingsStore


class WindowService:
    def __init__(self, settings_store: SettingsStore) -> None:
        self.settings_store = settings_store

    def restore_geometry(self, settings: AppSettings) -> WindowGeometry:
        defaults = default_window_geometry()
        geometry = settings.window_geometry
        width = geometry.width if geometry.width and geometry.width >= 720 else defaults["width"]
        height = geometry.height if geometry.height and geometry.height >= 560 else defaults["height"]
        left = geometry.left if geometry.left is not None and geometry.left >= 0 else defaults["left"]
        top = geometry.top if geometry.top is not None and geometry.top >= 0 else defaults["top"]
        always_on_top = geometry.always_on_top if settings.remember_window_geometry else bool(settings.start_always_on_top)
        return WindowGeometry(width=width, height=height, left=left, top=top, always_on_top=always_on_top)

    def persist_geometry(
        self,
        settings: AppSettings,
        *,
        width: float | None,
        height: float | None,
        left: float | None,
        top: float | None,
        always_on_top: bool,
    ) -> AppSettings:
        settings.window_geometry = WindowGeometry(
            width=width,
            height=height,
            left=left,
            top=top,
            always_on_top=always_on_top,
        )
        self.settings_store.save(settings)
        return settings

    def reset_geometry(self, settings: AppSettings) -> AppSettings:
        settings.window_geometry = WindowGeometry(**default_window_geometry())
        self.settings_store.save(settings)
        return settings
