from __future__ import annotations

import flet as ft

from app.ui.theme import PANEL_RAISED


class UserDialog:
    def __init__(self, page: ft.Page, users: list[tuple[str, str]], current_user_id: str | None, on_create, on_select) -> None:
        self.page = page
        self.users = users
        self.current_user_id = current_user_id
        self.on_create = on_create
        self.on_select = on_select

    def open(self) -> None:
        field_width = 420
        name_field = ft.TextField(label="New user", autofocus=True, border_radius=14, bgcolor=PANEL_RAISED, width=field_width)
        user_dropdown = ft.Dropdown(
            label="Current user",
            value=self.current_user_id,
            options=[ft.dropdown.Option(key=user_id, text=name) for user_id, name in self.users],
            width=field_width,
            border_radius=14,
            bgcolor=PANEL_RAISED,
        )
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Users"),
            content=ft.Container(
                width=480,
                content=ft.Column(
                    [
                        user_dropdown,
                        ft.Row(
                            [ft.OutlinedButton("Use selected", on_click=lambda _e: self._select(dialog, user_dropdown.value))]
                        ),
                        ft.Divider(),
                        name_field,
                    ],
                    tight=True,
                    spacing=14,
                ),
            ),
            actions=[
                ft.TextButton("Close", on_click=lambda _e: self._close(dialog)),
                ft.ElevatedButton("Create user", icon=ft.Icons.PERSON_ADD, on_click=lambda _e: self._create(dialog, name_field.value or "")),
            ],
        )
        self.page.open(dialog)

    def _close(self, dialog: ft.AlertDialog) -> None:
        self.page.close(dialog)

    def _create(self, dialog: ft.AlertDialog, name: str) -> None:
        self._close(dialog)
        self.on_create(name)

    def _select(self, dialog: ft.AlertDialog, user_id: str | None) -> None:
        if user_id:
            self._close(dialog)
            self.on_select(user_id)
