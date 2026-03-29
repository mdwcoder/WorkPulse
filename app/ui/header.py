from __future__ import annotations

import flet as ft

from app.ui.theme import BG, BORDER, PANEL, TEXT, TEXT_MUTED, badge, tab_button
from core.enums import SyncState


def build_header(window: "WorkPulseWindow") -> ft.Container:
    app = window.app
    workspace = app.current_workspace
    sync_state = app.sync_state()
    sync_enabled = bool(workspace and workspace.sync_enabled and workspace.sync_repo_local_path)
    workspace_options = [
        ft.dropdown.Option(key=item.id, text=item.name) for item in app.workspace_service.list_workspaces()
    ]
    workspace_dropdown = ft.Dropdown(
        value=workspace.id if workspace else None,
        width=240,
        options=workspace_options,
        hint_text="Select workspace",
        text_size=13,
        bgcolor=PANEL,
        dense=True,
        border_radius=14,
        content_padding=ft.padding.symmetric(horizontal=12, vertical=10),
        on_change=lambda e: window.handle_workspace_change(e.control.value),
    )

    sync_palette = {
        SyncState.SYNCED: ("Synced", "#4ADE80", "#173323"),
        SyncState.PENDING: ("Pending", "#FBBF24", "#342A10"),
        SyncState.OFFLINE: ("Offline", TEXT_MUTED, "#1B2026"),
        SyncState.ERROR: ("Error", "#F87171", "#34191B"),
    }
    label, fg, bg = sync_palette[sync_state]
    header_row = ft.Row(
        [
            ft.Row(
                [
                    ft.Text("WorkPulse", size=26, weight=ft.FontWeight.W_800, color=TEXT),
                    workspace_dropdown,
                    badge(label, fg=fg, bg=bg),
                ],
                spacing=16,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            ft.Row(
                [
                    ft.IconButton(
                        icon=ft.Icons.PUSH_PIN if window.page.window.always_on_top else ft.Icons.PUSH_PIN_OUTLINED,
                        tooltip="Always on top",
                        on_click=lambda _e: window.toggle_pin(),
                    ),
                    ft.IconButton(icon=ft.Icons.SYNC, tooltip="Manual sync", on_click=lambda _e: window.run_sync(), disabled=not sync_enabled),
                    ft.IconButton(icon=ft.Icons.SETTINGS, tooltip="Settings", on_click=lambda _e: window.open_settings()),
                    ft.IconButton(icon=ft.Icons.MINIMIZE, tooltip="Minimize", on_click=lambda _e: window.minimize_window()),
                ],
                spacing=6,
            ),
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )

    tabs_row = ft.Row(
        [tab_button(name, window.selected_tab == key, lambda _e, k=key: window.set_tab(k)) for key, name in window.tabs],
        spacing=16,
    )

    return ft.Container(
        content=ft.Column([header_row, tabs_row], spacing=14),
        padding=ft.padding.only(left=22, top=18, right=22, bottom=14),
        bgcolor=BG,
        border=ft.border.only(bottom=ft.BorderSide(1, BORDER)),
    )
