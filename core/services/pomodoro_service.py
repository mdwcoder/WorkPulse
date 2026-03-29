from __future__ import annotations

from datetime import timedelta

from core.enums import EntityType, EventType, PomodoroState
from core.models import PomodoroSession
from core.repositories import PomodoroRepository
from core.services.event_service import EventService
from core.utils.time_utils import parse_iso, utc_now, utc_now_iso


class PomodoroService:
    def __init__(self, repository: PomodoroRepository, event_service: EventService) -> None:
        self.repository = repository
        self.event_service = event_service

    def current(self, user_id: str) -> PomodoroSession | None:
        session = self.repository.get_current(user_id)
        if session and session.state == PomodoroState.RUNNING and session.planned_end_at:
            planned = parse_iso(session.planned_end_at)
            if planned and planned <= utc_now():
                session = self.repository.update(session.id, state=PomodoroState.FINISHED, ended_at=utc_now_iso())
        return session

    def start(self, workspace_id: str, user_id: str, duration_minutes: int, task_id: str | None = None) -> PomodoroSession:
        existing = self.current(user_id)
        if existing:
            self.reset(existing.id)
        planned_end_at = (utc_now() + timedelta(minutes=duration_minutes)).isoformat()
        session = self.repository.create(user_id, task_id, duration_minutes, planned_end_at)
        self.event_service.emit(
            workspace_id=workspace_id,
            actor_user_id=user_id,
            event_type=EventType.POMODORO_STARTED,
            entity_type=EntityType.POMODORO,
            entity_id=session.id,
            payload=session.to_dict(),
        )
        return session

    def pause(self, workspace_id: str, user_id: str) -> PomodoroSession | None:
        session = self.current(user_id)
        if not session or session.state != PomodoroState.RUNNING or not session.planned_end_at:
            return session
        planned = parse_iso(session.planned_end_at)
        remaining = max(int((planned - utc_now()).total_seconds()), 0) if planned else 0
        session = self.repository.update(session.id, state=PomodoroState.PAUSED, paused_remaining_seconds=remaining)
        self.event_service.emit(
            workspace_id=workspace_id,
            actor_user_id=user_id,
            event_type=EventType.POMODORO_PAUSED,
            entity_type=EntityType.POMODORO,
            entity_id=session.id,
            payload=session.to_dict(),
        )
        return session

    def resume(self, workspace_id: str, user_id: str) -> PomodoroSession | None:
        session = self.current(user_id)
        if not session or session.state != PomodoroState.PAUSED:
            return session
        planned = (utc_now() + timedelta(seconds=session.paused_remaining_seconds)).isoformat()
        session = self.repository.update(
            session.id,
            state=PomodoroState.RUNNING,
            planned_end_at=planned,
            paused_remaining_seconds=0,
        )
        self.event_service.emit(
            workspace_id=workspace_id,
            actor_user_id=user_id,
            event_type=EventType.POMODORO_RESUMED,
            entity_type=EntityType.POMODORO,
            entity_id=session.id,
            payload=session.to_dict(),
        )
        return session

    def reset(self, session_id: str) -> PomodoroSession:
        return self.repository.update(session_id, state=PomodoroState.CANCELLED, ended_at=utc_now_iso(), paused_remaining_seconds=0)

    def tick(self, workspace_id: str, user_id: str) -> PomodoroSession | None:
        session = self.current(user_id)
        if not session:
            return None
        if session.state == PomodoroState.RUNNING and session.planned_end_at:
            planned = parse_iso(session.planned_end_at)
            if planned and planned <= utc_now():
                session = self.repository.update(session.id, state=PomodoroState.FINISHED, ended_at=utc_now_iso())
                self.event_service.emit(
                    workspace_id=workspace_id,
                    actor_user_id=user_id,
                    event_type=EventType.POMODORO_FINISHED,
                    entity_type=EntityType.POMODORO,
                    entity_id=session.id,
                    payload=session.to_dict(),
                )
        return session

    def remaining_seconds(self, user_id: str) -> int:
        session = self.current(user_id)
        if not session:
            return 0
        if session.state == PomodoroState.PAUSED:
            return session.paused_remaining_seconds
        if session.state == PomodoroState.RUNNING and session.planned_end_at:
            planned = parse_iso(session.planned_end_at)
            if planned:
                return max(int((planned - utc_now()).total_seconds()), 0)
        return 0

    def list_recent(self, user_id: str, limit: int = 8) -> list[PomodoroSession]:
        return self.repository.list_recent(user_id, limit)
