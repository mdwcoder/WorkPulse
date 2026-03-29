from __future__ import annotations

from core.models import AppSettings


class SettingsController:
    def __init__(self, app: "AppController") -> None:
        self.app = app

    def get_settings(self) -> AppSettings:
        self.app.reload_settings()
        return self.app.settings

    def update_general(
        self,
        *,
        dark_theme: bool,
        remember_window_geometry: bool,
        restore_last_workspace: bool,
        start_always_on_top: bool,
        compact_mode: bool,
    ) -> None:
        settings = self.app.settings
        settings.dark_theme = dark_theme
        settings.remember_window_geometry = remember_window_geometry
        settings.restore_last_workspace = restore_last_workspace
        settings.start_always_on_top = start_always_on_top
        settings.compact_mode = compact_mode
        self.app.save_settings()

    def update_time(self, work_minutes: int, short_break: int, long_break: int, auto_start_next: bool) -> None:
        settings = self.app.settings
        settings.pomodoro_work_minutes = work_minutes
        settings.pomodoro_short_break_minutes = short_break
        settings.pomodoro_long_break_minutes = long_break
        settings.pomodoro_auto_start_next = auto_start_next
        self.app.save_settings()

    def update_sync_preferences(self, manual_only: bool, auto_on_startup: bool, auto_on_task_changes: bool) -> None:
        settings = self.app.settings
        settings.manual_only_sync = manual_only
        settings.auto_sync_on_startup = auto_on_startup
        settings.auto_sync_on_task_changes = auto_on_task_changes
        self.app.save_settings()
