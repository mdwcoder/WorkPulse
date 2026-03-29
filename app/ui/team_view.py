from __future__ import annotations

import flet as ft

from app.ui.theme import PANEL_RAISED, TEXT, TEXT_MUTED, card, team_presence_badge
from core.utils.time_utils import format_relative


def build_team_view(window: "WorkPulseWindow") -> ft.Control:
    snapshots = window.app.team.snapshot()
    summary = window.app.team.summary()
    if not snapshots:
        return ft.Container(content=ft.Text("Create users to populate the team view."), alignment=ft.alignment.center, expand=True)

    members = []
    for snapshot in snapshots:
        members.append(
            ft.Container(
                content=ft.Row(
                    [
                        ft.CircleAvatar(content=ft.Text(snapshot.user.display_name[:1].upper()), radius=18),
                        ft.Column(
                            [
                                ft.Text(snapshot.user.display_name, size=18, weight=ft.FontWeight.W_700, color=TEXT),
                                ft.Text(snapshot.active_task.title if snapshot.active_task else "No active task", size=12, color=TEXT_MUTED),
                            ],
                            spacing=4,
                            expand=True,
                        ),
                        team_presence_badge(snapshot.presence),
                        ft.Column(
                            [
                                ft.Text(format_relative(snapshot.last_activity_at), size=12),
                                ft.Text(snapshot.last_completed_task.completion_commit_hash[:7] if snapshot.last_completed_task and snapshot.last_completed_task.completion_commit_hash else "-", size=12, color=TEXT_MUTED),
                            ],
                            spacing=4,
                            horizontal_alignment=ft.CrossAxisAlignment.END,
                        ),
                    ],
                    spacing=12,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                padding=ft.padding.symmetric(horizontal=12, vertical=10),
                border_radius=14,
                bgcolor=PANEL_RAISED,
            )
        )

    return ft.ResponsiveRow(
        [
            ft.Container(
                col={"xs": 12, "lg": 8},
                content=card(
                    ft.Column(
                        [
                            ft.Text("Engineering Team", size=30, weight=ft.FontWeight.W_800),
                            ft.Text(f"{len(snapshots)} members in the workspace", color=TEXT_MUTED),
                            ft.Column(members, spacing=10),
                        ],
                        spacing=16,
                    ),
                    expand=True,
                ),
            ),
            ft.Container(
                col={"xs": 12, "lg": 4},
                content=ft.Column(
                    [
                        card(
                            ft.Column(
                                [
                                    ft.Text("Activity Pulse", size=20, weight=ft.FontWeight.W_700),
                                    ft.Text(f"{summary.active_members}/{len(snapshots)}", size=40, weight=ft.FontWeight.W_800),
                                    ft.Text("Active members right now", color=TEXT_MUTED),
                                    ft.Text(f"{summary.completed_with_commit_today} completed tasks with commit today", color=TEXT_MUTED, size=12),
                                ],
                                spacing=10,
                            ),
                            bgcolor=PANEL_RAISED,
                        ),
                        card(
                            ft.Column(
                                [
                                    ft.Text("Recent Highlights", size=20, weight=ft.FontWeight.W_700),
                                    *([ft.Text(item, size=12) for item in summary.recent_highlights] or [ft.Text("No recent highlights yet.", size=12, color=TEXT_MUTED)]),
                                ],
                                spacing=10,
                            ),
                            expand=True,
                        ),
                    ],
                    spacing=14,
                    expand=True,
                ),
            ),
        ],
        spacing=14,
        run_spacing=14,
    )
