from __future__ import annotations

import flet as ft

from core.enums import CommitPolicy, PresenceStatus, TaskPriority, TaskStatus

BG = "#0A0D10"
PANEL = "#11151A"
PANEL_RAISED = "#161B21"
PANEL_SOFT = "#0F1318"
BORDER = "#232A33"
TEXT = "#F5F7FA"
TEXT_MUTED = "#8F99A5"
GREEN = "#4ADE80"
GREEN_SOFT = "#173323"
RED = "#F87171"
RED_SOFT = "#34191B"
YELLOW = "#FBBF24"
YELLOW_SOFT = "#352A10"
BLUE = "#60A5FA"
BLUE_SOFT = "#15273B"
GRAY_BADGE = "#1E242B"


def configure_page(page: ft.Page, dark_theme: bool = True) -> None:
    page.theme_mode = ft.ThemeMode.DARK if dark_theme else ft.ThemeMode.LIGHT
    page.bgcolor = BG
    page.padding = 0
    page.spacing = 0
    page.window.minimizable = True
    page.window.resizable = True
    page.window.prevent_close = False
    page.title = "WorkPulse"
    page.theme = ft.Theme(font_family="sans-serif")


def card(content: ft.Control, *, padding: int = 18, expand: bool | int = False, bgcolor: str = PANEL) -> ft.Container:
    return ft.Container(
        content=content,
        padding=padding,
        bgcolor=bgcolor,
        border_radius=18,
        border=ft.border.all(1, BORDER),
        expand=expand,
    )


def section_title(label: str, subtitle: str | None = None) -> ft.Column:
    children: list[ft.Control] = [
        ft.Text(label, size=12, weight=ft.FontWeight.W_600, color=TEXT_MUTED),
    ]
    if subtitle:
        children.append(ft.Text(subtitle, size=22, weight=ft.FontWeight.W_700, color=TEXT))
    return ft.Column(children, spacing=6)


def badge(text: str, *, fg: str = TEXT, bg: str = GRAY_BADGE, border_color: str | None = None, icon: str | None = None) -> ft.Container:
    row_items: list[ft.Control] = []
    if icon:
        row_items.append(ft.Icon(icon, size=12, color=fg))
    row_items.append(ft.Text(text, size=11, color=fg, weight=ft.FontWeight.W_500))
    return ft.Container(
        content=ft.Row(row_items, spacing=5, tight=True),
        padding=ft.padding.symmetric(horizontal=9, vertical=5),
        bgcolor=bg,
        border_radius=999,
        border=ft.border.all(1, border_color or bg),
    )


def priority_badge(priority: TaskPriority) -> ft.Container:
    color_map = {
        TaskPriority.LOW: (TEXT_MUTED, GRAY_BADGE),
        TaskPriority.MEDIUM: (YELLOW, YELLOW_SOFT),
        TaskPriority.HIGH: (BLUE, BLUE_SOFT),
        TaskPriority.CRITICAL: (RED, RED_SOFT),
    }
    fg, bg = color_map[priority]
    return badge(priority.value.capitalize(), fg=fg, bg=bg)


def commit_policy_badge(policy: CommitPolicy) -> ft.Container:
    palette = {
        CommitPolicy.NONE: (TEXT_MUTED, GRAY_BADGE),
        CommitPolicy.OPTIONAL: (BLUE, BLUE_SOFT),
        CommitPolicy.REQUIRED: (YELLOW, YELLOW_SOFT),
    }
    fg, bg = palette[policy]
    return badge(policy.value, fg=fg, bg=bg)


def status_badge(status: TaskStatus) -> ft.Container:
    palette = {
        TaskStatus.BACKLOG: (TEXT_MUTED, GRAY_BADGE),
        TaskStatus.DOING: (GREEN, GREEN_SOFT),
        TaskStatus.REVIEW: (BLUE, BLUE_SOFT),
        TaskStatus.DONE: (TEXT, "#1E293B"),
    }
    fg, bg = palette[status]
    return badge(status.value.capitalize(), fg=fg, bg=bg)


def presence_badge(status: PresenceStatus) -> ft.Container:
    palette = {
        PresenceStatus.ACTIVE: ("Focused", GREEN, GREEN_SOFT),
        PresenceStatus.IDLE: ("Drifting", YELLOW, YELLOW_SOFT),
        PresenceStatus.OFFLINE: ("Idle", TEXT_MUTED, GRAY_BADGE),
    }
    label, fg, bg = palette[status]
    return badge(label, fg=fg, bg=bg, icon=ft.Icons.CIRCLE)


def team_presence_badge(status: PresenceStatus) -> ft.Container:
    palette = {
        PresenceStatus.ACTIVE: ("active", GREEN, GREEN_SOFT),
        PresenceStatus.IDLE: ("idle", YELLOW, YELLOW_SOFT),
        PresenceStatus.OFFLINE: ("offline", TEXT_MUTED, GRAY_BADGE),
    }
    label, fg, bg = palette[status]
    return badge(label, fg=fg, bg=bg, icon=ft.Icons.CIRCLE)


def subtle_divider() -> ft.Divider:
    return ft.Divider(height=1, color=BORDER)


def tab_button(label: str, selected: bool, on_click) -> ft.Container:
    return ft.Container(
        content=ft.TextButton(
            text=label,
            on_click=on_click,
            style=ft.ButtonStyle(
                color={ft.ControlState.DEFAULT: TEXT if selected else TEXT_MUTED},
                padding=ft.padding.symmetric(horizontal=6, vertical=4),
                overlay_color="transparent",
            ),
        ),
        border=ft.border.only(bottom=ft.BorderSide(2, TEXT if selected else "transparent")),
    )
