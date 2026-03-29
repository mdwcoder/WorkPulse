from __future__ import annotations

from core.enums import PomodoroState, PresenceStatus, PunchType
from core.utils.time_utils import format_duration, format_minutes, parse_iso, utc_now


class TimeController:
    def __init__(self, app: "AppController") -> None:
        self.app = app

    def focus_state(self) -> PresenceStatus:
        user = self.app.current_user
        if not user:
            return PresenceStatus.OFFLINE
        active_task = self.app.task_service.get_active_task(user.id)
        pomodoro = self.app.pomodoro_service.current(user.id)
        work_session = self.app.punch_service.current_work_session(user.id)
        if active_task and (pomodoro or work_session):
            return PresenceStatus.ACTIVE
        if active_task:
            return PresenceStatus.IDLE
        return PresenceStatus.OFFLINE

    def start_pomodoro(self, duration_minutes: int) -> None:
        workspace = self.app.current_workspace
        user = self.app.current_user
        if not workspace or not user:
            raise ValueError("Select workspace and user before starting a pomodoro.")
        active_task = self.app.task_service.get_active_task(user.id)
        self.app.pomodoro_service.start(workspace.id, user.id, duration_minutes, task_id=active_task.id if active_task else None)

    def pause_pomodoro(self) -> None:
        workspace = self.app.current_workspace
        user = self.app.current_user
        if workspace and user:
            self.app.pomodoro_service.pause(workspace.id, user.id)

    def resume_pomodoro(self) -> None:
        workspace = self.app.current_workspace
        user = self.app.current_user
        if workspace and user:
            self.app.pomodoro_service.resume(workspace.id, user.id)

    def reset_pomodoro(self) -> None:
        user = self.app.current_user
        if not user:
            return
        current = self.app.pomodoro_service.current(user.id)
        if current:
            self.app.pomodoro_service.reset(current.id)

    def pomodoro_snapshot(self) -> dict[str, object]:
        user = self.app.current_user
        if not user:
            return {"session": None, "remaining": 0, "formatted": "25:00"}
        session = self.app.pomodoro_service.current(user.id)
        remaining = self.app.pomodoro_service.remaining_seconds(user.id)
        if not session:
            remaining = self.app.settings.pomodoro_work_minutes * 60
        return {
            "session": session,
            "remaining": remaining,
            "formatted": format_duration(remaining),
        }

    def start_work_session(self) -> None:
        workspace = self.app.current_workspace
        user = self.app.current_user
        if not workspace or not user:
            raise ValueError("Select workspace and user before starting a work session.")
        active_task = self.app.task_service.get_active_task(user.id)
        self.app.punch_service.start_work_session(workspace.id, user.id, task_id=active_task.id if active_task else None)

    def end_work_session(self) -> None:
        workspace = self.app.current_workspace
        user = self.app.current_user
        if workspace and user:
            self.app.punch_service.end_work_session(workspace.id, user.id)

    def current_work_duration(self) -> str:
        user = self.app.current_user
        if not user:
            return "00:00"
        session = self.app.punch_service.current_work_session(user.id)
        if not session:
            return "00:00"
        started = parse_iso(session.started_at)
        if not started:
            return "00:00"
        return format_duration((utc_now() - started).total_seconds())

    def today_work_duration(self) -> str:
        user = self.app.current_user
        if not user:
            return "00:00"
        today = utc_now().date()
        total_seconds = 0
        for session in self.app.punch_service.list_recent_work_sessions(user.id, limit=200):
            started = parse_iso(session.started_at)
            if not started or started.date() != today:
                continue
            ended = parse_iso(session.ended_at) or utc_now()
            total_seconds += max(int((ended - started).total_seconds()), 0)
        return format_duration(total_seconds)

    def focus_score(self) -> str:
        user = self.app.current_user
        if not user:
            return "0%"
        today = utc_now().date()
        work_seconds = 0
        for session in self.app.punch_service.list_recent_work_sessions(user.id, limit=200):
            started = parse_iso(session.started_at)
            if not started or started.date() != today:
                continue
            ended = parse_iso(session.ended_at) or utc_now()
            work_seconds += max(int((ended - started).total_seconds()), 0)

        focus_seconds = 0
        for session in self.app.pomodoro_service.list_recent(user.id, limit=200):
            started = parse_iso(session.started_at)
            if not started or started.date() != today:
                continue
            if session.state == PomodoroState.FINISHED:
                focus_seconds += session.duration_minutes * 60
            elif session.state == PomodoroState.RUNNING:
                focus_seconds += max(session.duration_minutes * 60 - self.app.pomodoro_service.remaining_seconds(user.id), 0)
            elif session.state == PomodoroState.PAUSED:
                focus_seconds += max(session.duration_minutes * 60 - session.paused_remaining_seconds, 0)

        if work_seconds <= 0:
            return "0%"
        return f"{round(min((focus_seconds / work_seconds) * 100, 100))}%"

    def pomodoro_label(self) -> str:
        snapshot = self.pomodoro_snapshot()
        session = snapshot["session"]
        if not session:
            return f"{self.app.settings.pomodoro_work_minutes} min block"
        state_labels = {
            PomodoroState.RUNNING: "running",
            PomodoroState.PAUSED: "paused",
            PomodoroState.FINISHED: "finished",
            PomodoroState.CANCELLED: "cancelled",
            PomodoroState.IDLE: "idle",
        }
        return f"{state_labels.get(session.state, 'session')} · {format_minutes(session.duration_minutes)}"

    def pomodoro_controls(self) -> dict[str, object]:
        user = self.app.current_user
        session = self.app.pomodoro_service.current(user.id) if user else None
        if not session:
            return {
                "primary_label": "Start Pomodoro",
                "can_pause": False,
                "can_reset": False,
                "can_start": True,
            }
        if session.state == PomodoroState.PAUSED:
            return {
                "primary_label": "Resume Pomodoro",
                "can_pause": False,
                "can_reset": True,
                "can_start": True,
            }
        if session.state == PomodoroState.RUNNING:
            return {
                "primary_label": "Running",
                "can_pause": True,
                "can_reset": True,
                "can_start": False,
            }
        return {
            "primary_label": "Start Pomodoro",
            "can_pause": False,
            "can_reset": False,
            "can_start": True,
        }

    def work_session_controls(self) -> dict[str, bool]:
        user = self.app.current_user
        active = self.app.punch_service.current_work_session(user.id) if user else None
        return {
            "can_start": active is None,
            "can_end": active is not None,
        }

    def punch_controls(self) -> dict[str, object]:
        user = self.app.current_user
        if not user:
            return {"can_clock_in": False, "can_clock_out": False, "last_clock_in": None, "last_clock_out": None}
        state = self.app.punch_service.punch_state(user.id)
        return {
            "can_clock_in": state != "clocked in",
            "can_clock_out": state == "clocked in",
            "last_clock_in": self.app.punch_service.last_punch_of_type(user.id, PunchType.CLOCK_IN),
            "last_clock_out": self.app.punch_service.last_punch_of_type(user.id, PunchType.CLOCK_OUT),
        }

    def clock_in(self) -> None:
        workspace = self.app.current_workspace
        user = self.app.current_user
        if workspace and user:
            self.app.punch_service.clock_in(workspace.id, user.id)

    def clock_out(self) -> None:
        workspace = self.app.current_workspace
        user = self.app.current_user
        if workspace and user:
            self.app.punch_service.clock_out(workspace.id, user.id)

    def tick(self) -> None:
        workspace = self.app.current_workspace
        user = self.app.current_user
        if workspace and user:
            self.app.pomodoro_service.tick(workspace.id, user.id)
