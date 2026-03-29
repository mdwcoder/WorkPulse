from __future__ import annotations

import json

import flet as ft

from app.ui.theme import PANEL_RAISED, TEXT, TEXT_MUTED, badge, card, commit_policy_badge, priority_badge, subtle_divider
from core.enums import CommitPolicy, TaskPriority, TaskStatus
from core.models import Task
from core.utils.time_utils import format_dt


def build_task_detail_panel(
    *,
    task: Task | None,
    repos: list[tuple[str, str]],
    users: list[tuple[str, str]],
    path_warning: str | None,
    on_save,
    on_mark_done,
    on_set_active,
    on_open_path,
    on_open_repo_config,
    on_close,
) -> ft.Control:
    field_width = 280
    is_new = task is None
    title_field = ft.TextField(
        label="Title",
        value=task.title if task else "",
        autofocus=is_new,
        dense=True,
        width=field_width,
        border_radius=14,
        bgcolor=PANEL_RAISED,
    )
    description_field = ft.TextField(
        label="Description",
        value=task.description if task else "",
        multiline=True,
        min_lines=4,
        max_lines=8,
        dense=True,
        width=field_width,
        border_radius=14,
        bgcolor=PANEL_RAISED,
    )
    assignee_dropdown = ft.Dropdown(
        label="Assignee",
        value=task.assignee_user_id if task else None,
        options=[ft.dropdown.Option(key=user_id, text=name) for user_id, name in users],
        width=field_width,
        border_radius=14,
        bgcolor=PANEL_RAISED,
    )
    status_dropdown = ft.Dropdown(
        label="Status",
        value=task.status.value if task else TaskStatus.BACKLOG.value,
        options=[ft.dropdown.Option(key=status.value, text=status.value.capitalize()) for status in TaskStatus],
        width=field_width,
        border_radius=14,
        bgcolor=PANEL_RAISED,
    )
    priority_dropdown = ft.Dropdown(
        label="Priority",
        value=task.priority.value if task else TaskPriority.MEDIUM.value,
        options=[ft.dropdown.Option(key=item.value, text=item.value.capitalize()) for item in TaskPriority],
        width=field_width,
        border_radius=14,
        bgcolor=PANEL_RAISED,
    )
    repo_dropdown = ft.Dropdown(
        label="Repo",
        value=task.repo_id if task else None,
        options=[ft.dropdown.Option(key=repo_id, text=repo_name) for repo_id, repo_name in repos],
        width=field_width,
        border_radius=14,
        bgcolor=PANEL_RAISED,
    )
    branch_field = ft.TextField(
        label="Branch",
        value=task.branch_name if task else "",
        dense=True,
        width=field_width,
        border_radius=14,
        bgcolor=PANEL_RAISED,
    )
    tags_field = ft.TextField(
        label="Tags (comma separated)",
        value=", ".join(json.loads(task.tags_json)) if task else "",
        dense=True,
        width=field_width,
        border_radius=14,
        bgcolor=PANEL_RAISED,
    )
    commit_policy_dropdown = ft.Dropdown(
        label="Commit policy",
        value=task.commit_policy.value if task else CommitPolicy.OPTIONAL.value,
        options=[ft.dropdown.Option(key=item.value, text=item.value) for item in CommitPolicy],
        width=field_width,
        border_radius=14,
        bgcolor=PANEL_RAISED,
    )

    info_items: list[ft.Control] = []
    if task:
        info_items.extend(
            [
                ft.Row([badge(f"ID {task.id[:8]}"), priority_badge(task.priority), commit_policy_badge(task.commit_policy)], wrap=True),
                ft.Text(f"Created {format_dt(task.created_at)}", color=TEXT_MUTED, size=12),
                ft.Text(f"Updated {format_dt(task.updated_at)}", color=TEXT_MUTED, size=12),
            ]
        )
        if task.completion_timestamp:
            info_items.append(ft.Text(f"Completed {format_dt(task.completion_timestamp)}", color=TEXT_MUTED, size=12))

    warning_control = ft.Container(
        visible=bool(path_warning),
        content=badge(path_warning or "", fg="#FBBF24", bg="#332812"),
    )

    def _save(_e: ft.ControlEvent) -> None:
        payload = {
            "title": title_field.value or "",
            "description": description_field.value or "",
            "assignee_user_id": assignee_dropdown.value,
            "status": TaskStatus(status_dropdown.value),
            "priority": TaskPriority(priority_dropdown.value),
            "tags": [part.strip() for part in (tags_field.value or "").split(",") if part.strip()],
            "repo_id": repo_dropdown.value,
            "branch_name": branch_field.value.strip() or None,
            "commit_policy": CommitPolicy(commit_policy_dropdown.value),
        }
        on_save(task.id if task else None, payload)

    header_text = "New Task" if is_new else "Task Details"
    return card(
        ft.Column(
            [
                ft.Row(
                    [
                        ft.Column(
                            [
                                ft.Text(header_text, size=24, weight=ft.FontWeight.W_700, color=TEXT),
                                ft.Text("Technical context, ownership and completion flow.", size=12, color=TEXT_MUTED),
                            ],
                            spacing=4,
                            expand=True,
                        ),
                        ft.IconButton(icon=ft.Icons.CLOSE, on_click=on_close, icon_color=TEXT_MUTED),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                warning_control,
                ft.ResponsiveRow(
                    [
                        ft.Container(title_field, col={"xs": 12}),
                        ft.Container(assignee_dropdown, col={"xs": 12, "md": 6}),
                        ft.Container(status_dropdown, col={"xs": 12, "md": 6}),
                        ft.Container(priority_dropdown, col={"xs": 12, "md": 6}),
                        ft.Container(commit_policy_dropdown, col={"xs": 12, "md": 6}),
                        ft.Container(repo_dropdown, col={"xs": 12, "md": 6}),
                        ft.Container(branch_field, col={"xs": 12, "md": 6}),
                        ft.Container(tags_field, col={"xs": 12}),
                        ft.Container(description_field, col={"xs": 12}),
                    ],
                    run_spacing=10,
                    spacing=10,
                ),
                subtle_divider(),
                ft.Row(
                    [
                        ft.ElevatedButton("Save task", icon=ft.Icons.SAVE, on_click=_save),
                        ft.OutlinedButton("Set as active", icon=ft.Icons.PLAY_CIRCLE, on_click=on_set_active, disabled=is_new),
                        ft.OutlinedButton("Open local path", icon=ft.Icons.FOLDER_OPEN, on_click=on_open_path, disabled=is_new),
                        ft.OutlinedButton("Open repo config", icon=ft.Icons.SETTINGS, on_click=on_open_repo_config),
                        ft.ElevatedButton(
                            "Mark as Done",
                            icon=ft.Icons.CHECK_CIRCLE,
                            on_click=on_mark_done,
                            disabled=is_new,
                            style=ft.ButtonStyle(bgcolor="#E5E7EB", color="#111827"),
                        ),
                    ],
                    wrap=True,
                ),
                ft.Column(info_items, spacing=6),
            ],
            spacing=16,
            scroll=ft.ScrollMode.AUTO,
        ),
        expand=True,
    )
