from __future__ import annotations

from core.enums import EntityType, EventType, PunchType
from core.models import PunchRecord, WorkSession
from core.repositories import PunchRepository, WorkSessionRepository
from core.services.event_service import EventService
from core.utils.time_utils import utc_now_iso


class PunchService:
    def __init__(
        self,
        punch_repository: PunchRepository,
        work_session_repository: WorkSessionRepository,
        event_service: EventService,
    ) -> None:
        self.punch_repository = punch_repository
        self.work_session_repository = work_session_repository
        self.event_service = event_service

    def clock_in(self, workspace_id: str, user_id: str) -> PunchRecord:
        record = self.punch_repository.create(user_id, PunchType.CLOCK_IN)
        self.event_service.emit(
            workspace_id=workspace_id,
            actor_user_id=user_id,
            event_type=EventType.CLOCK_IN,
            entity_type=EntityType.PUNCH,
            entity_id=record.id,
            payload=record.to_dict(),
        )
        return record

    def clock_out(self, workspace_id: str, user_id: str) -> PunchRecord:
        record = self.punch_repository.create(user_id, PunchType.CLOCK_OUT)
        self.event_service.emit(
            workspace_id=workspace_id,
            actor_user_id=user_id,
            event_type=EventType.CLOCK_OUT,
            entity_type=EntityType.PUNCH,
            entity_id=record.id,
            payload=record.to_dict(),
        )
        return record

    def last_punch(self, user_id: str) -> PunchRecord | None:
        return self.punch_repository.get_last(user_id)

    def last_punch_of_type(self, user_id: str, punch_type: PunchType) -> PunchRecord | None:
        for record in self.list_recent_punches(user_id, limit=50):
            if record.punch_type == punch_type:
                return record
        return None

    def punch_state(self, user_id: str) -> str:
        last = self.last_punch(user_id)
        if not last or last.punch_type == PunchType.CLOCK_OUT:
            return "clocked out"
        return "clocked in"

    def list_recent_punches(self, user_id: str, limit: int = 8) -> list[PunchRecord]:
        return self.punch_repository.list_recent(user_id, limit)

    def start_work_session(self, workspace_id: str, user_id: str, task_id: str | None = None) -> WorkSession:
        existing = self.work_session_repository.get_current(user_id)
        if existing:
            return existing
        session = self.work_session_repository.create(user_id=user_id, task_id=task_id)
        self.event_service.emit(
            workspace_id=workspace_id,
            actor_user_id=user_id,
            event_type=EventType.WORK_SESSION_STARTED,
            entity_type=EntityType.WORK_SESSION,
            entity_id=session.id,
            payload=session.to_dict(),
        )
        return session

    def end_work_session(self, workspace_id: str, user_id: str) -> WorkSession | None:
        session = self.work_session_repository.get_current(user_id)
        if not session:
            return None
        session = self.work_session_repository.update(session.id, ended_at=utc_now_iso())
        self.event_service.emit(
            workspace_id=workspace_id,
            actor_user_id=user_id,
            event_type=EventType.WORK_SESSION_ENDED,
            entity_type=EntityType.WORK_SESSION,
            entity_id=session.id,
            payload=session.to_dict(),
        )
        return session

    def current_work_session(self, user_id: str) -> WorkSession | None:
        return self.work_session_repository.get_current(user_id)

    def list_recent_work_sessions(self, user_id: str, limit: int = 8) -> list[WorkSession]:
        return self.work_session_repository.list_recent(user_id, limit)
