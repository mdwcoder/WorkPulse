from __future__ import annotations

import json

import flet as ft

from app.ui.theme import PANEL_RAISED, TEXT, TEXT_MUTED, badge, card, presence_badge


def build_focus_view(window: "WorkPulseWindow") -> ft.Control:
    app = window.app
    workspace = app.current_workspace
    user = app.current_user
    if not workspace or not user:
        return ft.Container(content=ft.Text("Create a workspace and a user to unlock focus mode."), alignment=ft.alignment.center, expand=True)

    active_task = app.task_service.get_active_task(user.id)
    focus_state = app.time.focus_state()
    pomodoro = app.time.pomodoro_snapshot()
    if not active_task:
        return ft.Container(
            expand=True,
            alignment=ft.alignment.center,
            content=card(
                ft.Column(
                    [
                        ft.Text("No active task", size=32, weight=ft.FontWeight.W_800),
                        ft.Text("Set one from Board to enter execution mode.", color=TEXT_MUTED),
                        ft.ElevatedButton("Go to Board", icon=ft.Icons.VIEW_KANBAN, on_click=lambda _e: window.set_tab("board")),
                    ],
                    spacing=16,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                padding=36,
            ),
        )

    repo = app.repo_service.get_repo(active_task.repo_id)
    mapping = app.repo_service.get_mapping(active_task.repo_id, user.id) if active_task.repo_id else None
    has_local_path = bool(mapping and mapping.local_path)
    tags = [badge(tag, fg=TEXT_MUTED, bg=PANEL_RAISED) for tag in json.loads(active_task.tags_json)]
    return ft.ResponsiveRow(
        [
            ft.Container(
                col={"xs": 12, "md": 7},
                content=card(
                    ft.Column(
                        [
                            presence_badge(focus_state),
                            ft.Text(active_task.title, size=48, weight=ft.FontWeight.W_800, color=TEXT),
                            ft.Text(active_task.description or "No description", color=TEXT_MUTED, size=14),
                            ft.Row(
                                [
                                    badge(repo.display_name if repo else "No repo"),
                                    badge(active_task.branch_name or "No branch"),
                                    *tags,
                                ],
                                wrap=True,
                            ),
                            ft.Text(mapping.local_path if mapping else "Missing local path mapping", size=12, color=TEXT_MUTED),
                            ft.Row(
                                [
                                    ft.ElevatedButton("Open path", icon=ft.Icons.FOLDER_OPEN, on_click=lambda _e: window.open_active_local_path(), disabled=not has_local_path),
                                    ft.ElevatedButton("Start Pomodoro", icon=ft.Icons.TIMER, on_click=lambda _e: window.start_pomodoro()),
                                    ft.OutlinedButton("Mark as Done", icon=ft.Icons.CHECK, on_click=lambda _e: window.open_completion(active_task.id)),
                                    ft.OutlinedButton("Clear active task", icon=ft.Icons.CLOSE, on_click=lambda _e: window.clear_active_task()),
                                ],
                                wrap=True,
                            ),
                        ],
                        spacing=18,
                    ),
                    expand=True,
                ),
            ),
            ft.Container(
                col={"xs": 12, "md": 5},
                content=card(
                    ft.Column(
                        [
                            ft.Text("Current session", size=16, weight=ft.FontWeight.W_600),
                            ft.Text(str(pomodoro["formatted"]), size=68, weight=ft.FontWeight.W_800, color=TEXT),
                            ft.Text(app.time.pomodoro_label(), size=12, color=TEXT_MUTED),
                            ft.Text("Focus state follows active task plus a running pomodoro or work session.", color=TEXT_MUTED, size=12),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=18,
                    ),
                    expand=True,
                    bgcolor=PANEL_RAISED,
                ),
            ),
        ],
        spacing=16,
        run_spacing=16,
    )
