from __future__ import annotations

import asyncio

import flet as ft

from app.controllers.app_controller import AppController
from app.ui.board_view import build_board_view
from app.ui.completion_dialog import CompletionDialog
from app.ui.focus_view import build_focus_view
from app.ui.header import build_header
from app.ui.repo_dialog import RepoDialog
from app.ui.settings_dialog import SettingsDialog
from app.ui.task_detail_panel import build_task_detail_panel
from app.ui.team_view import build_team_view
from app.ui.theme import BG, BORDER, PANEL, PANEL_RAISED, TEXT, TEXT_MUTED, card, configure_page
from app.ui.time_view import build_time_view
from app.ui.user_dialog import UserDialog
from app.ui.workspace_dialog import WorkspaceDialog
from core.enums import CommitPolicy, TaskPriority, TaskStatus
from core.utils.logger import get_logger
from core.utils.time_utils import format_relative

LOGGER = get_logger("workpulse.ui.main")


class WorkPulseWindow:
    tabs = [
        ("board", "Board"),
        ("focus", "Focus"),
        ("time", "Time"),
        ("team", "Team"),
    ]

    def __init__(self, page: ft.Page) -> None:
        self.page = page
        self.app = AppController()
        self.selected_tab = "board"
        self.root = ft.Container(expand=True)
        self.creating_task = False

    def mount(self) -> None:
        configure_page(self.page, self.app.settings.dark_theme)
        self._configure_window()
        self.page.window.on_event = self._handle_window_event
        self.page.add(self.root)
        self.app.ensure_defaults_after_first_workspace()
        self.refresh()
        self.page.run_task(self._ticker)
        if self.app.settings.auto_sync_on_startup and self.app.current_workspace and self.app.current_workspace.sync_enabled:
            self.run_sync()

    def _configure_window(self) -> None:
        settings = self.app.settings
        geometry = self.app.window_service.restore_geometry(settings)
        self.page.window.width = geometry.width
        self.page.window.height = geometry.height
        self.page.window.left = geometry.left
        self.page.window.top = geometry.top
        self.page.window.always_on_top = geometry.always_on_top
        self.page.window.minimizable = True
        self.page.window.resizable = True

    def _handle_window_event(self, event: ft.WindowEvent) -> None:
        if str(event.data).lower() in {"moved", "resized", "close"} and self.app.settings.remember_window_geometry:
            self.app.window_service.persist_geometry(
                self.app.settings,
                width=self.page.window.width,
                height=self.page.window.height,
                left=self.page.window.left,
                top=self.page.window.top,
                always_on_top=self.page.window.always_on_top,
            )
        if str(event.data).lower() == "close":
            self.page.window.destroy()

    async def _ticker(self) -> None:
        while True:
            await asyncio.sleep(1)
            try:
                self.app.time.tick()
                if self.selected_tab in {"focus", "time"}:
                    self.refresh()
            except Exception as exc:  # pragma: no cover
                LOGGER.exception("Ticker error: %s", exc)

    def refresh(self) -> None:
        configure_page(self.page, self.app.settings.dark_theme)
        self.root.content = ft.Column(
            [
                build_header(self),
                ft.Container(
                    content=self._build_body(),
                    expand=True,
                    padding=ft.padding.only(left=22, top=18, right=22, bottom=18),
                    bgcolor=BG,
                ),
                self._build_footer(),
            ],
            spacing=0,
            expand=True,
        )
        self.page.update()

    def _build_body(self) -> ft.Control:
        if self.selected_tab == "board":
            return build_board_view(self)
        if self.selected_tab == "focus":
            return build_focus_view(self)
        if self.selected_tab == "time":
            return build_time_view(self)
        return build_team_view(self)

    def _build_footer(self) -> ft.Container:
        status = self.app.footer_status()
        return ft.Container(
            content=ft.Row(
                [
                    ft.Text(f"Last sync: {format_relative(status['last_sync']) if status['last_sync'] != 'Never' else 'Never'}", size=12, color=TEXT_MUTED),
                    ft.Text(f"Pending: {status['pending']}", size=12, color=TEXT_MUTED),
                    ft.Text(f"Active task: {status['active_task']}", size=12, color=TEXT_MUTED),
                    ft.Text(f"User: {status['current_user']}", size=12, color=TEXT_MUTED),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            padding=ft.padding.only(left=22, top=10, right=22, bottom=12),
            bgcolor=PANEL,
            border=ft.border.only(top=ft.BorderSide(1, BORDER)),
        )

    def set_tab(self, tab_key: str) -> None:
        self.selected_tab = tab_key
        self.refresh()

    def handle_workspace_change(self, workspace_id: str | None) -> None:
        if not workspace_id:
            return
        self.app.set_current_workspace(workspace_id)
        self.refresh()

    def notify(self, message: str, error: bool = False) -> None:
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(message),
            bgcolor="#34191B" if error else "#173323",
            open=True,
        )
        self.page.update()

    def toggle_pin(self) -> None:
        self.page.window.always_on_top = not self.page.window.always_on_top
        if self.app.settings.remember_window_geometry:
            self.app.window_service.persist_geometry(
                self.app.settings,
                width=self.page.window.width,
                height=self.page.window.height,
                left=self.page.window.left,
                top=self.page.window.top,
                always_on_top=self.page.window.always_on_top,
            )
        self.refresh()

    def minimize_window(self) -> None:
        self.page.window.minimized = True

    def run_sync(self) -> None:
        try:
            result = self.app.sync.manual_sync()
            self.notify(result.message, error=not result.ok)
        except Exception as exc:
            self.notify(str(exc), error=True)
        self.refresh()

    def open_settings(self) -> None:
        SettingsDialog(
            self.page,
            self.app,
            on_manage_workspaces=self.open_workspace_dialog,
            on_manage_repos=self.open_repo_dialog,
            on_manage_users=self.open_user_dialog,
            on_reset_geometry=self.reset_window_geometry,
            on_applied=self.refresh,
        ).open()

    def open_workspace_dialog(self) -> None:
        workspaces = [(item.id, item.name) for item in self.app.workspace_service.list_workspaces()]
        current = self.app.current_workspace
        WorkspaceDialog(
            self.page,
            workspaces=workspaces,
            current_workspace_id=current.id if current else None,
            on_create=self._create_workspace_from_dialog,
            on_select=self._select_workspace_from_dialog,
        ).open()

    def _create_workspace_from_dialog(self, name: str, owner_name: str | None) -> None:
        try:
            self.app.create_workspace(name.strip(), owner_name.strip() if owner_name else None)
            self.notify("Workspace created.")
        except Exception as exc:
            self.notify(str(exc), error=True)
        self.refresh()

    def _select_workspace_from_dialog(self, workspace_id: str) -> None:
        self.app.set_current_workspace(workspace_id)
        self.notify("Workspace switched.")
        self.refresh()

    def open_user_dialog(self) -> None:
        workspace = self.app.current_workspace
        if not workspace:
            self.notify("Create a workspace first.", error=True)
            return
        users = [(item.id, item.display_name) for item in self.app.workspace_service.list_users(workspace.id)]
        current = self.app.current_user
        UserDialog(
            self.page,
            users=users,
            current_user_id=current.id if current else None,
            on_create=self._create_user_from_dialog,
            on_select=self._select_user_from_dialog,
        ).open()

    def _create_user_from_dialog(self, name: str) -> None:
        workspace = self.app.current_workspace
        if not workspace:
            return
        try:
            self.app.workspace_service.create_user(workspace.id, name, make_current=not bool(self.app.current_user))
            self.notify("User created.")
        except Exception as exc:
            self.notify(str(exc), error=True)
        self.refresh()

    def _select_user_from_dialog(self, user_id: str) -> None:
        workspace = self.app.current_workspace
        if workspace:
            self.app.set_current_user(user_id)
            self.notify("Current user updated.")
        self.refresh()

    def open_repo_dialog(self) -> None:
        workspace = self.app.current_workspace
        if not workspace:
            self.notify("Create a workspace first.", error=True)
            return
        repos = [(repo.id, repo.display_name) for repo in self.app.repo_service.list_repos(workspace.id)]
        users = [(user.id, user.display_name) for user in self.app.workspace_service.list_users(workspace.id)]
        RepoDialog(
            self.page,
            repos=repos,
            users=users,
            on_save_repo=self._save_repo_from_dialog,
            on_save_mapping=self._save_mapping_from_dialog,
        ).open()

    def _save_repo_from_dialog(self, display_name: str, canonical_remote: str, default_branch: str) -> None:
        workspace = self.app.current_workspace
        user = self.app.current_user
        if not workspace:
            return
        try:
            self.app.repo_service.create_repo(workspace.id, display_name, canonical_remote, default_branch, actor_user_id=user.id if user else None)
            self.notify("Repo created.")
        except Exception as exc:
            self.notify(str(exc), error=True)
        self.refresh()

    def _save_mapping_from_dialog(self, repo_id: str, user_id: str, local_path: str) -> None:
        workspace = self.app.current_workspace
        if not workspace:
            return
        try:
            self.app.repo_service.upsert_mapping(workspace.id, repo_id, user_id, local_path)
            self.notify("Repo mapping saved.")
        except Exception as exc:
            self.notify(str(exc), error=True)
        self.refresh()

    def update_board_filter(self, key: str, value) -> None:
        cleaned = value or None if key in {"repo_id", "status", "commit_policy"} else value
        setattr(self.app.board.filters, key, cleaned)
        self.refresh()

    def move_task(self, task_id: str, status_value: str) -> None:
        try:
            self.app.board.move(task_id, TaskStatus(status_value))
            self._maybe_auto_sync()
        except Exception as exc:
            self.notify(str(exc), error=True)
        self.refresh()

    def set_active_task(self, task_id: str) -> None:
        try:
            self.app.board.set_active(task_id)
            self.notify("Active task updated.")
            self._maybe_auto_sync()
        except Exception as exc:
            self.notify(str(exc), error=True)
        self.refresh()

    def clear_active_task(self) -> None:
        self.app.board.clear_active()
        self.refresh()

    def open_task_editor(self, task_id: str | None) -> None:
        is_wide = (self.page.window.width or 0) >= 1180
        self.app.board.set_selected_task(task_id)
        if task_id and is_wide:
            self.refresh()
            return
        self._open_task_dialog(task_id)

    def build_task_detail(self, task) -> ft.Control:
        workspace = self.app.current_workspace
        user = self.app.current_user
        repos = [(repo.id, repo.display_name) for repo in self.app.repo_service.list_repos(workspace.id)] if workspace else []
        users = [(item.id, item.display_name) for item in self.app.workspace_service.list_users(workspace.id)] if workspace else []
        path_warning = None
        if task and user and task.repo_id and task.assignee_user_id == user.id and not self.app.repo_service.get_mapping(task.repo_id, user.id):
            path_warning = "Assigned repo has no local path mapping for the current user."
        return build_task_detail_panel(
            task=task,
            repos=repos,
            users=users,
            path_warning=path_warning,
            on_save=self._save_task_from_panel,
            on_mark_done=(lambda _e: self.open_completion(task.id)) if task else (lambda _e: None),
            on_set_active=(lambda _e: self.set_active_task(task.id)) if task else (lambda _e: None),
            on_open_path=(lambda _e: self.open_task_local_path(task.id)) if task else (lambda _e: None),
            on_open_repo_config=(lambda _e: self.open_repo_dialog()),
            on_close=(lambda _e: self.close_task_detail()),
        )

    def _open_task_dialog(self, task_id: str | None) -> None:
        task = self.app.task_service.get_task(task_id) if task_id else None
        content = self.build_task_detail(task)
        dialog = ft.AlertDialog(
            modal=True,
            content=ft.Container(width=860, height=720, content=content),
            actions=[ft.TextButton("Close", on_click=lambda _e: self._close_dialog(dialog))],
        )
        self.page.open(dialog)

    def _close_dialog(self, dialog: ft.AlertDialog) -> None:
        self.page.close(dialog)
        self.refresh()

    def _save_task_from_panel(self, task_id: str | None, payload: dict) -> None:
        try:
            if task_id:
                self.app.task.update_task(task_id, **payload)
                self.notify("Task updated.")
            else:
                self.app.task.create_task(**payload)
                self.notify("Task created.")
            self._maybe_auto_sync()
        except Exception as exc:
            self.notify(str(exc), error=True)
        self.refresh()

    def close_task_detail(self) -> None:
        self.app.board.set_selected_task(None)
        self.refresh()

    def open_completion(self, task_id: str) -> None:
        try:
            context = self.app.task.completion_context(task_id)
            CompletionDialog(self.page, context, on_submit=lambda close_only, message: self._complete_task(task_id, close_only, message)).open()
        except Exception as exc:
            self.notify(str(exc), error=True)

    def _complete_task(self, task_id: str, close_only: bool, commit_message: str | None) -> None:
        ok, message = self.app.task.complete_task(task_id, close_only, commit_message)
        if ok:
            self._maybe_auto_sync()
        self.notify(message, error=not ok)
        self.refresh()

    def open_task_local_path(self, task_id: str) -> None:
        task = self.app.task_service.get_task(task_id)
        user = self.app.current_user
        if not task or not user:
            return
        mapping = self.app.repo_service.get_mapping(task.repo_id, user.id) if task.repo_id else None
        ok, message = self.app.repo_service.open_local_path(mapping.local_path if mapping else None)
        self.notify(message, error=not ok)

    def open_active_local_path(self) -> None:
        user = self.app.current_user
        if not user:
            return
        task = self.app.task_service.get_active_task(user.id)
        if task:
            self.open_task_local_path(task.id)

    def start_pomodoro(self) -> None:
        try:
            self.app.time.start_pomodoro(self.app.settings.pomodoro_work_minutes)
        except Exception as exc:
            self.notify(str(exc), error=True)
        self.refresh()

    def start_or_resume_pomodoro(self) -> None:
        session = self.app.pomodoro_service.current(self.app.current_user.id) if self.app.current_user else None
        try:
            if session and session.state.value == "paused":
                self.app.time.resume_pomodoro()
            else:
                self.start_pomodoro()
        except Exception as exc:
            self.notify(str(exc), error=True)
        self.refresh()

    def pause_pomodoro(self) -> None:
        self.app.time.pause_pomodoro()
        self.refresh()

    def reset_pomodoro(self) -> None:
        self.app.time.reset_pomodoro()
        self.refresh()

    def start_work_session(self) -> None:
        try:
            self.app.time.start_work_session()
            self.notify("Work session started.")
        except Exception as exc:
            self.notify(str(exc), error=True)
        self.refresh()

    def end_work_session(self) -> None:
        self.app.time.end_work_session()
        self.refresh()

    def clock_in(self) -> None:
        self.app.time.clock_in()
        self.refresh()

    def clock_out(self) -> None:
        self.app.time.clock_out()
        self.refresh()

    def reset_window_geometry(self) -> None:
        self.app.window_service.reset_geometry(self.app.settings)
        self._configure_window()
        self.refresh()

    def _maybe_auto_sync(self) -> None:
        workspace = self.app.current_workspace
        if workspace and workspace.sync_enabled and self.app.settings.auto_sync_on_task_changes and not self.app.settings.manual_only_sync:
            self.run_sync()
