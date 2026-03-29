from __future__ import annotations

import flet as ft

from app.ui.theme import PANEL_RAISED, TEXT, TEXT_MUTED, badge, card
from core.enums import PunchType
from core.utils.time_utils import format_relative


def build_time_view(window: "WorkPulseWindow") -> ft.Control:
    app = window.app
    user = app.current_user
    if not user:
        return ft.Container(content=ft.Text("Create a user to unlock time tracking."), alignment=ft.alignment.center, expand=True)

    active_task = app.task_service.get_active_task(user.id)
    pomodoro = app.time.pomodoro_snapshot()
    pomodoro_controls = app.time.pomodoro_controls()
    work_session = app.punch_service.current_work_session(user.id)
    work_session_controls = app.time.work_session_controls()
    punch_controls = app.time.punch_controls()
    pomodoros = app.pomodoro_service.list_recent(user.id)
    work_history = app.punch_service.list_recent_work_sessions(user.id)
    punches = app.punch_service.list_recent_punches(user.id)

    history_controls = []
    for session in pomodoros[:4]:
        history_controls.append(ft.Text(f"Pomodoro {session.duration_minutes}m • {format_relative(session.created_at)}", size=12))
    for session in work_history[:4]:
        history_controls.append(ft.Text(f"Work session • {format_relative(session.started_at)}", size=12))
    for record in punches[:4]:
        verb = "Clock in" if record.punch_type == PunchType.CLOCK_IN else "Clock out"
        history_controls.append(ft.Text(f"{verb} • {format_relative(record.created_at)}", size=12))
    if not history_controls:
        history_controls = [ft.Text("No time history yet.", size=12, color=TEXT_MUTED)]

    return ft.ResponsiveRow(
        [
            ft.Container(
                col={"xs": 12, "lg": 8},
                content=ft.Column(
                    [
                        ft.ResponsiveRow(
                            [
                                _metric("Daily Total", app.time.today_work_duration(), "Tracked today"),
                                _metric("Focus Score", app.time.focus_score(), "Pomodoro share of tracked time"),
                                _metric("Active Task", active_task.title if active_task else "None", active_task.branch_name if active_task else "No branch"),
                            ],
                            spacing=12,
                            run_spacing=12,
                        ),
                        card(
                            ft.Column(
                                [
                                    ft.Text("Current Session", size=14, color=TEXT_MUTED),
                                    ft.Text(str(pomodoro["formatted"]), size=96, weight=ft.FontWeight.W_800),
                                    ft.Row(
                                        [
                                            ft.IconButton(icon=ft.Icons.PAUSE, on_click=lambda _e: window.pause_pomodoro(), disabled=not pomodoro_controls["can_pause"]),
                                            ft.ElevatedButton(
                                                str(pomodoro_controls["primary_label"]),
                                                icon=ft.Icons.PLAY_ARROW,
                                                on_click=lambda _e: window.start_or_resume_pomodoro(),
                                                disabled=not pomodoro_controls["can_start"],
                                            ),
                                            ft.IconButton(icon=ft.Icons.REPLAY, on_click=lambda _e: window.reset_pomodoro(), disabled=not pomodoro_controls["can_reset"]),
                                        ],
                                        alignment=ft.MainAxisAlignment.CENTER,
                                    ),
                                    ft.Row([badge(app.time.pomodoro_label())], alignment=ft.MainAxisAlignment.CENTER),
                                ],
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                spacing=18,
                            ),
                            expand=True,
                        ),
                        ft.Row(
                            [
                                ft.Container(
                                    content=card(
                                        ft.Row(
                                            [
                                                ft.Icon(ft.Icons.LOGIN, color="#4ADE80"),
                                                ft.Column(
                                                    [
                                                        ft.Text("Clock In", size=18, weight=ft.FontWeight.W_700),
                                                        ft.Text(app.punch_service.punch_state(user.id), size=12, color=TEXT_MUTED),
                                                    ],
                                                    spacing=4,
                                                ),
                                            ],
                                            spacing=12,
                                        ),
                                        expand=True,
                                    ),
                                    expand=1,
                                    on_click=lambda _e: window.clock_in(),
                                    ink=True,
                                    disabled=not punch_controls["can_clock_in"],
                                ),
                                ft.Container(
                                    content=card(
                                        ft.Row(
                                            [
                                                ft.Icon(ft.Icons.LOGOUT, color="#F87171"),
                                                ft.Column(
                                                    [
                                                        ft.Text("Clock Out", size=18, weight=ft.FontWeight.W_700),
                                                        ft.Text(
                                                            format_relative(punch_controls["last_clock_out"].created_at) if punch_controls["last_clock_out"] else "No clock out yet",
                                                            size=12,
                                                            color=TEXT_MUTED,
                                                        ),
                                                    ],
                                                    spacing=4,
                                                ),
                                            ],
                                            spacing=12,
                                        ),
                                        expand=True,
                                    ),
                                    expand=1,
                                    on_click=lambda _e: window.clock_out(),
                                    ink=True,
                                    disabled=not punch_controls["can_clock_out"],
                                ),
                            ],
                            spacing=12,
                        ),
                    ],
                    spacing=14,
                ),
            ),
            ft.Container(
                col={"xs": 12, "lg": 4},
                content=ft.Column(
                    [
                        card(
                            ft.Column(
                                [
                                    ft.Text("Work Session", size=20, weight=ft.FontWeight.W_700),
                                    ft.Text(app.time.current_work_duration(), size=36, weight=ft.FontWeight.W_800),
                                    ft.Row(
                                        [
                                            ft.ElevatedButton("Start", icon=ft.Icons.PLAY_CIRCLE, on_click=lambda _e: window.start_work_session(), disabled=not work_session_controls["can_start"]),
                                            ft.OutlinedButton("End", icon=ft.Icons.STOP_CIRCLE, on_click=lambda _e: window.end_work_session(), disabled=not work_session_controls["can_end"]),
                                        ],
                                        wrap=True,
                                    ),
                                    ft.Text(
                                        f"Bound to {active_task.title}" if work_session and active_task else "You can attach new sessions to the active task.",
                                        size=12,
                                        color=TEXT_MUTED,
                                    ),
                                ],
                                spacing=14,
                            ),
                            bgcolor=PANEL_RAISED,
                        ),
                        card(
                            ft.Column(
                                [
                                    ft.Text("Activity History", size=20, weight=ft.FontWeight.W_700),
                                    *history_controls,
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


def _metric(title: str, value: str, subtitle: str) -> ft.Container:
    return ft.Container(
        col={"xs": 12, "md": 4},
        content=card(
            ft.Column(
                [
                    ft.Text(title.upper(), size=12, color=TEXT_MUTED),
                    ft.Text(value, size=34, weight=ft.FontWeight.W_800, color=TEXT),
                    ft.Text(subtitle, size=12, color=TEXT_MUTED),
                ],
                spacing=8,
            ),
            bgcolor=PANEL_RAISED,
        ),
    )
