from __future__ import annotations

import flet as ft

from app.ui.theme import BLUE, BORDER, GREEN, PANEL_RAISED, RED, TEXT, TEXT_MUTED, badge, commit_policy_badge, priority_badge
from core.models import Task


def build_task_card(
    task: Task,
    *,
    assignee_name: str,
    repo_name: str,
    is_active: bool,
    needs_path: bool,
    on_open,
    on_set_active,
    on_move,
) -> ft.Container:
    badges: list[ft.Control] = [priority_badge(task.priority), commit_policy_badge(task.commit_policy)]
    if is_active:
        badges.append(badge("Active", fg=GREEN, bg="#163122"))
    if needs_path:
        badges.append(badge("Missing path", fg=RED, bg="#2E181B"))

    move_menu = ft.PopupMenuButton(
        icon=ft.Icons.MORE_HORIZ,
        tooltip="Task actions",
        items=[
            ft.PopupMenuItem(text="Move to Backlog", on_click=lambda _e: on_move(task.id, "backlog")),
            ft.PopupMenuItem(text="Move to Doing", on_click=lambda _e: on_move(task.id, "doing")),
            ft.PopupMenuItem(text="Move to Review", on_click=lambda _e: on_move(task.id, "review")),
            ft.PopupMenuItem(text="Move to Done", on_click=lambda _e: on_move(task.id, "done")),
            ft.PopupMenuItem(),
            ft.PopupMenuItem(text="Set as active", on_click=lambda _e: on_set_active(task.id)),
        ],
    )

    return ft.Container(
        content=ft.Column(
            [
                ft.Row(
                    [
                        ft.Text(task.title, size=15, weight=ft.FontWeight.W_700, color=TEXT, expand=True),
                        move_menu,
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.START,
                ),
                ft.Row(
                    [
                        ft.Text(assignee_name, size=12, color=TEXT_MUTED),
                        ft.Text("•", color=BORDER),
                        ft.Text(repo_name, size=12, color=TEXT_MUTED),
                        ft.Text(task.branch_name or "no-branch", size=12, color=TEXT_MUTED),
                    ],
                    wrap=True,
                    spacing=8,
                ),
                ft.Row(badges, wrap=True, spacing=6),
            ],
            spacing=10,
        ),
        padding=16,
        bgcolor=PANEL_RAISED,
        border_radius=16,
        border=ft.border.all(1, GREEN if is_active else BLUE if task.status.value == "review" else BORDER),
        ink=True,
        on_click=lambda _e: on_open(task.id),
    )
