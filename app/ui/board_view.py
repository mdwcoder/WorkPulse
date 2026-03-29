from __future__ import annotations

import flet as ft

from app.ui.task_card import build_task_card
from app.ui.theme import PANEL_RAISED, TEXT, TEXT_MUTED, badge, card, section_title
from core.enums import CommitPolicy, TaskStatus


def build_board_view(window: "WorkPulseWindow") -> ft.Control:
    app = window.app
    workspace = app.current_workspace
    user = app.current_user
    if not workspace:
        return _empty_state("Create a workspace to start organizing tasks.", window.open_workspace_dialog)

    if not user:
        return _empty_state("Create or select a user to work with task ownership and focus state.", window.open_user_dialog)

    board = app.board
    repos = app.repo_service.list_repos(workspace.id)
    users = {item.id: item.display_name for item in app.workspace_service.list_users(workspace.id)}
    active_task = app.task_service.get_active_task(user.id)

    topbar = ft.Row(
        [
            ft.ElevatedButton("Create task", icon=ft.Icons.ADD, on_click=lambda _e: window.open_task_editor(None)),
            ft.Switch(
                label="Assigned to me",
                value=board.filters.assigned_to_me,
                on_change=lambda e: window.update_board_filter("assigned_to_me", e.control.value),
            ),
            ft.Switch(
                label="Active task",
                value=board.filters.active_only,
                on_change=lambda e: window.update_board_filter("active_only", e.control.value),
            ),
            ft.Dropdown(
                label="Repo",
                width=180,
                value=board.filters.repo_id,
                options=[ft.dropdown.Option(key="", text="All")] + [ft.dropdown.Option(key=repo.id, text=repo.display_name) for repo in repos],
                on_change=lambda e: window.update_board_filter("repo_id", e.control.value),
            ),
            ft.Dropdown(
                label="Status",
                width=160,
                value=board.filters.status,
                options=[ft.dropdown.Option(key="", text="All")] + [ft.dropdown.Option(key=status.value, text=status.value.capitalize()) for status in TaskStatus],
                on_change=lambda e: window.update_board_filter("status", e.control.value),
            ),
            ft.Dropdown(
                label="Commit",
                width=170,
                value=board.filters.commit_policy,
                options=[ft.dropdown.Option(key="", text="All")] + [ft.dropdown.Option(key=policy.value, text=policy.value) for policy in CommitPolicy],
                on_change=lambda e: window.update_board_filter("commit_policy", e.control.value),
            ),
        ],
        wrap=True,
        spacing=10,
    )

    is_wide = (window.page.window.width or 0) >= 1180
    column_controls = []
    repo_names = {repo.id: repo.display_name for repo in repos}
    columns_order = [
        (TaskStatus.BACKLOG, "Backlog"),
        (TaskStatus.DOING, "Doing"),
        (TaskStatus.REVIEW, "Review"),
        (TaskStatus.DONE, "Done"),
    ]
    for status, label in columns_order:
        tasks = board.column_tasks(status)
        task_controls = [
            build_task_card(
                task,
                assignee_name=users.get(task.assignee_user_id, "Unassigned"),
                repo_name=repo_names.get(task.repo_id, "No repo"),
                is_active=bool(active_task and active_task.id == task.id),
                needs_path=bool(task.repo_id and not app.repo_service.get_mapping(task.repo_id, user.id) and task.assignee_user_id == user.id),
                on_open=window.open_task_editor,
                on_set_active=lambda task_id: window.set_active_task(task_id),
                on_move=window.move_task,
            )
            for task in tasks
        ]
        if not task_controls:
            task_controls = [badge("No tasks", fg=TEXT_MUTED, bg=PANEL_RAISED)]
        column_controls.append(
            card(
                ft.Column(
                    [
                        ft.Row(
                            [
                                section_title(label, str(len(tasks))),
                                badge(str(len(tasks)), fg=TEXT_MUTED, bg=PANEL_RAISED),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                        ft.ListView(task_controls, spacing=12, expand=True, padding=0),
                    ],
                    spacing=14,
                    expand=True,
                ),
                expand=1,
            )
        )

    detail_control: ft.Control | None = None
    selected = board.selected_task()
    if selected and is_wide:
        detail_control = window.build_task_detail(selected)

    body: ft.Control
    if is_wide:
        items: list[ft.Control] = [ft.Container(content=item, expand=1) for item in column_controls]
        if detail_control:
            items.append(ft.Container(content=detail_control, width=420))
        body = ft.Row(items, spacing=14, expand=True, vertical_alignment=ft.CrossAxisAlignment.START)
    else:
        body = ft.Column(column_controls, spacing=14, expand=True, scroll=ft.ScrollMode.AUTO)

    return ft.Column(
        [
            ft.Row(
                [
                    ft.Column(
                        [
                            ft.Text("Board", size=28, weight=ft.FontWeight.W_800, color=TEXT),
                            ft.Text("Technical kanban with task context, repo branch and completion policy.", color=TEXT_MUTED, size=13),
                        ],
                        spacing=3,
                        expand=True,
                    ),
                ]
            ),
            topbar,
            ft.Container(content=body, expand=True),
        ],
        spacing=16,
        expand=True,
    )


def _empty_state(message: str, action) -> ft.Control:
    return ft.Container(
        expand=True,
        alignment=ft.alignment.center,
        content=card(
            ft.Column(
                [
                    ft.Text("WorkPulse", size=30, weight=ft.FontWeight.W_800),
                    ft.Text(message, size=14, color=TEXT_MUTED, text_align=ft.TextAlign.CENTER),
                    ft.ElevatedButton("Configure now", icon=ft.Icons.SETTINGS, on_click=lambda _e: action()),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=16,
            ),
            padding=34,
        ),
    )
