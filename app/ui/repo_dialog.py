from __future__ import annotations

import flet as ft

from app.ui.theme import PANEL_RAISED


class RepoDialog:
    def __init__(self, page: ft.Page, repos: list[tuple[str, str]], users: list[tuple[str, str]], on_save_repo, on_save_mapping) -> None:
        self.page = page
        self.repos = repos
        self.users = users
        self.on_save_repo = on_save_repo
        self.on_save_mapping = on_save_mapping

    def open(self) -> None:
        field_width = 500
        repo_name = ft.TextField(label="Display name", autofocus=True, border_radius=14, bgcolor=PANEL_RAISED, width=field_width)
        repo_remote = ft.TextField(label="Canonical remote", border_radius=14, bgcolor=PANEL_RAISED, width=field_width)
        repo_branch = ft.TextField(label="Default branch", value="main", border_radius=14, bgcolor=PANEL_RAISED, width=field_width)
        repo_dropdown = ft.Dropdown(
            label="Repo for mapping",
            options=[ft.dropdown.Option(key=repo_id, text=name) for repo_id, name in self.repos],
            width=field_width,
            border_radius=14,
            bgcolor=PANEL_RAISED,
        )
        user_dropdown = ft.Dropdown(
            label="User",
            options=[ft.dropdown.Option(key=user_id, text=name) for user_id, name in self.users],
            width=field_width,
            border_radius=14,
            bgcolor=PANEL_RAISED,
        )
        path_field = ft.TextField(label="Local path", border_radius=14, bgcolor=PANEL_RAISED, width=field_width)

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Repos"),
            content=ft.Container(
                width=560,
                content=ft.Column(
                    [
                        ft.Text("Create logical repositories and map local paths per user.", size=13),
                        repo_name,
                        repo_remote,
                        repo_branch,
                        ft.Row([ft.ElevatedButton("Add repo", icon=ft.Icons.ADD, on_click=lambda _e: self.on_save_repo(repo_name.value or "", repo_remote.value or "", repo_branch.value or "main"))]),
                        ft.Divider(),
                        repo_dropdown,
                        user_dropdown,
                        path_field,
                    ],
                    spacing=14,
                    tight=True,
                ),
            ),
            actions=[
                ft.TextButton("Close", on_click=lambda _e: self._close(dialog)),
                ft.ElevatedButton(
                    "Save mapping",
                    icon=ft.Icons.FOLDER_OPEN,
                    on_click=lambda _e: self._save_mapping(dialog, repo_dropdown.value, user_dropdown.value, path_field.value or ""),
                ),
            ],
        )
        self.page.open(dialog)

    def _close(self, dialog: ft.AlertDialog) -> None:
        self.page.close(dialog)

    def _save_mapping(self, dialog: ft.AlertDialog, repo_id: str | None, user_id: str | None, local_path: str) -> None:
        if repo_id and user_id:
            self._close(dialog)
            self.on_save_mapping(repo_id, user_id, local_path)
