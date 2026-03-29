from __future__ import annotations

import flet as ft

from app.ui.theme import PANEL_RAISED, card


class SettingsDialog:
    def __init__(self, page: ft.Page, app, on_manage_workspaces, on_manage_repos, on_manage_users, on_reset_geometry, on_applied) -> None:
        self.page = page
        self.app = app
        self.on_manage_workspaces = on_manage_workspaces
        self.on_manage_repos = on_manage_repos
        self.on_manage_users = on_manage_users
        self.on_reset_geometry = on_reset_geometry
        self.on_applied = on_applied

    def open(self) -> None:
        settings = self.app.settings_controller.get_settings()
        workspace = self.app.current_workspace
        sync_ready = bool(workspace and workspace.sync_enabled and workspace.sync_repo_local_path)
        wide_field = 520
        compact_field = 180
        dark_theme = ft.Switch(label="Dark theme", value=settings.dark_theme)
        remember_geometry = ft.Switch(label="Remember window geometry", value=settings.remember_window_geometry)
        restore_last_workspace = ft.Switch(label="Restore last workspace", value=settings.restore_last_workspace)
        start_top = ft.Switch(label="Start always on top", value=settings.start_always_on_top)
        compact_mode = ft.Switch(label="Compact mode", value=settings.compact_mode)
        manual_sync = ft.Switch(label="Manual-only sync", value=settings.manual_only_sync)
        auto_sync_start = ft.Switch(label="Auto sync on startup", value=settings.auto_sync_on_startup)
        auto_sync_tasks = ft.Switch(label="Auto sync on task changes", value=settings.auto_sync_on_task_changes)
        sync_enabled = ft.Switch(label="Enable sync", value=bool(workspace.sync_enabled) if workspace else False)
        sync_repo_path = ft.TextField(label="Sync repo local path", value=workspace.sync_repo_local_path if workspace else "", width=wide_field, border_radius=14, bgcolor=PANEL_RAISED)
        sync_remote_url = ft.TextField(label="Remote URL", value=workspace.sync_remote_url if workspace else "", width=wide_field, border_radius=14, bgcolor=PANEL_RAISED)
        sync_branch = ft.TextField(label="Sync branch", value=workspace.sync_branch if workspace else "main", width=compact_field, border_radius=14, bgcolor=PANEL_RAISED)
        work_minutes = ft.TextField(label="Pomodoro work minutes", value=str(settings.pomodoro_work_minutes), width=compact_field, border_radius=14, bgcolor=PANEL_RAISED)
        short_break = ft.TextField(label="Short break minutes", value=str(settings.pomodoro_short_break_minutes), width=compact_field, border_radius=14, bgcolor=PANEL_RAISED)
        long_break = ft.TextField(label="Long break minutes", value=str(settings.pomodoro_long_break_minutes), width=compact_field, border_radius=14, bgcolor=PANEL_RAISED)
        auto_start_next = ft.Switch(label="Auto-start next session", value=settings.pomodoro_auto_start_next)
        dialog: ft.AlertDialog

        def save_all(_e: ft.ControlEvent) -> None:
            try:
                self.app.settings_controller.update_general(
                    dark_theme=dark_theme.value,
                    remember_window_geometry=remember_geometry.value,
                    restore_last_workspace=restore_last_workspace.value,
                    start_always_on_top=start_top.value,
                    compact_mode=compact_mode.value,
                )
                self.app.settings_controller.update_sync_preferences(
                    manual_only=manual_sync.value,
                    auto_on_startup=auto_sync_start.value,
                    auto_on_task_changes=auto_sync_tasks.value,
                )
                self.app.settings_controller.update_time(
                    work_minutes=int(work_minutes.value or "25"),
                    short_break=int(short_break.value or "5"),
                    long_break=int(long_break.value or "15"),
                    auto_start_next=auto_start_next.value,
                )
                if workspace:
                    self.app.workspace_service.update_sync_settings(
                        workspace.id,
                        sync_enabled=sync_enabled.value,
                        sync_repo_local_path=sync_repo_path.value or None,
                        sync_remote_url=sync_remote_url.value or None,
                        sync_branch=sync_branch.value or "main",
                    )
                self._close(dialog)
                self.on_applied()
            except Exception as exc:
                self.page.snack_bar = ft.SnackBar(content=ft.Text(str(exc)), bgcolor="#34191B", open=True)
                self.page.update()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Settings"),
            content=ft.Container(
                width=860,
                height=680,
                content=ft.Column(
                    [
                        card(
                            ft.Column(
                                [
                                    ft.Text("General", size=18, weight=ft.FontWeight.W_700),
                                    dark_theme,
                                    remember_geometry,
                                    restore_last_workspace,
                                    start_top,
                                    compact_mode,
                                ],
                                spacing=8,
                            ),
                            bgcolor=PANEL_RAISED,
                        ),
                        card(
                            ft.Column(
                                [
                                    ft.Text("Sync", size=18, weight=ft.FontWeight.W_700),
                                    sync_enabled,
                                    sync_repo_path,
                                    sync_remote_url,
                                    sync_branch,
                                    manual_sync,
                                    auto_sync_start,
                                    auto_sync_tasks,
                                    ft.Row(
                                        [
                                            ft.OutlinedButton("Init sync repo", on_click=lambda _e: self._run_sync_action(self.app.sync.init_repo)),
                                            ft.OutlinedButton("Pull", on_click=lambda _e: self._run_sync_action(self.app.sync.pull_only), disabled=not sync_ready),
                                            ft.OutlinedButton("Push", on_click=lambda _e: self._run_sync_action(self.app.sync.push_only), disabled=not sync_ready),
                                            ft.ElevatedButton("Full sync", on_click=lambda _e: self._run_sync_action(self.app.sync.manual_sync), disabled=not sync_ready),
                                        ],
                                        wrap=True,
                                    ),
                                    ft.Text(
                                        "Enable sync and configure a local sync repo path to activate pull, push and full sync."
                                        if not sync_ready
                                        else "Sync actions operate on the workspace metadata repo.",
                                        size=12,
                                        color="#8F99A5",
                                    ),
                                ],
                                spacing=8,
                            ),
                            bgcolor=PANEL_RAISED,
                        ),
                        card(
                            ft.Column(
                                [
                                    ft.Text("Repos & Users", size=18, weight=ft.FontWeight.W_700),
                                    ft.Row(
                                        [
                                            ft.ElevatedButton("Manage workspaces", on_click=lambda _e: self._open_nested(dialog, self.on_manage_workspaces)),
                                            ft.ElevatedButton("Manage repos", on_click=lambda _e: self._open_nested(dialog, self.on_manage_repos)),
                                            ft.ElevatedButton("Manage users", on_click=lambda _e: self._open_nested(dialog, self.on_manage_users)),
                                        ],
                                        wrap=True,
                                    ),
                                ],
                                spacing=10,
                            ),
                            bgcolor=PANEL_RAISED,
                        ),
                        card(
                            ft.Column(
                                [
                                    ft.Text("Time", size=18, weight=ft.FontWeight.W_700),
                                    ft.Row([work_minutes, short_break, long_break], wrap=True),
                                    auto_start_next,
                                ],
                                spacing=10,
                            ),
                            bgcolor=PANEL_RAISED,
                        ),
                        card(
                            ft.Column(
                                [
                                    ft.Text("Window", size=18, weight=ft.FontWeight.W_700),
                                    ft.Row(
                                        [
                                            ft.ElevatedButton("Reset geometry", on_click=lambda _e: self.on_reset_geometry()),
                                        ]
                                    ),
                                ]
                            ),
                            bgcolor=PANEL_RAISED,
                        ),
                    ],
                    scroll=ft.ScrollMode.AUTO,
                    spacing=14,
                ),
            ),
            actions=[
                ft.TextButton("Close", on_click=lambda _e: self._close(dialog)),
                ft.ElevatedButton("Apply settings", icon=ft.Icons.SAVE, on_click=save_all),
            ],
        )
        self.page.open(dialog)

    def _close(self, dialog: ft.AlertDialog) -> None:
        self.page.close(dialog)

    def _run_sync_action(self, action) -> None:
        try:
            result = action()
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(result.message),
                bgcolor="#173323" if result.ok else "#34191B",
                open=True,
            )
            self.page.update()
        except Exception as exc:
            self.page.snack_bar = ft.SnackBar(content=ft.Text(str(exc)), bgcolor="#34191B", open=True)
            self.page.update()

    def _open_nested(self, dialog: ft.AlertDialog, action) -> None:
        self._close(dialog)
        action()
