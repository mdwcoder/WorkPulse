from __future__ import annotations

import flet as ft

from app.ui.theme import PANEL_RAISED


class WorkspaceDialog:
    def __init__(self, page: ft.Page, workspaces: list[tuple[str, str]], current_workspace_id: str | None, on_create, on_select) -> None:
        self.page = page
        self.workspaces = workspaces
        self.current_workspace_id = current_workspace_id
        self.on_create = on_create
        self.on_select = on_select

    def open(self) -> None:
        field_width = 460
        error_text = ft.Text("", color="#F87171", size=12, visible=False)
        create_name = ft.TextField(label="Workspace name", autofocus=True, border_radius=14, bgcolor=PANEL_RAISED, width=field_width)
        owner_name = ft.TextField(label="Initial user (optional)", border_radius=14, bgcolor=PANEL_RAISED, width=field_width)
        workspace_dropdown = ft.Dropdown(
            label="Existing workspace",
            value=self.current_workspace_id,
            options=[ft.dropdown.Option(key=workspace_id, text=name) for workspace_id, name in self.workspaces],
            width=field_width,
            border_radius=14,
            bgcolor=PANEL_RAISED,
            visible=bool(self.workspaces),
            hint_text="No workspaces yet" if not self.workspaces else None,
        )
        switch_button = ft.OutlinedButton(
            "Switch",
            icon=ft.Icons.ARROW_FORWARD,
            on_click=lambda _e: self._select(dialog, workspace_dropdown.value),
            disabled=not bool(self.workspaces),
        )

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Workspace"),
            content=ft.Container(
                width=520,
                content=ft.Column(
                    [
                        ft.Text("Create a workspace or switch to an existing one.", size=13),
                        workspace_dropdown,
                        ft.Row([switch_button]),
                        ft.Divider(),
                        error_text,
                        create_name,
                        owner_name,
                    ],
                    tight=True,
                    spacing=14,
                ),
            ),
            actions=[
                ft.TextButton("Close", on_click=lambda _e: self._close(dialog)),
                ft.ElevatedButton(
                    "Create workspace",
                    icon=ft.Icons.ADD,
                    on_click=lambda _e: self._create(dialog, create_name.value or "", owner_name.value or None, error_text),
                ),
            ],
        )
        self.page.open(dialog)

    def _close(self, dialog: ft.AlertDialog) -> None:
        self.page.close(dialog)

    def _create(self, dialog: ft.AlertDialog, name: str, owner_name: str | None, error_text: ft.Text) -> None:
        if not name.strip():
            error_text.value = "Workspace name cannot be empty."
            error_text.visible = True
            error_text.update()
            return
        self._close(dialog)
        self.on_create(name, owner_name)

    def _select(self, dialog: ft.AlertDialog, workspace_id: str | None) -> None:
        if workspace_id:
            self._close(dialog)
            self.on_select(workspace_id)
