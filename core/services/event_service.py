from __future__ import annotations

from typing import Any

from core.enums import EntityType, EventType
from core.models import EventLog
from core.repositories import EventRepository


class EventService:
    def __init__(self, repository: EventRepository) -> None:
        self.repository = repository

    def emit(
        self,
        workspace_id: str,
        actor_user_id: str | None,
        event_type: EventType,
        entity_type: EntityType,
        entity_id: str | None,
        payload: dict[str, Any],
    ) -> EventLog:
        return self.repository.create(
            workspace_id=workspace_id,
            actor_user_id=actor_user_id,
            event_type=event_type.value,
            entity_type=entity_type.value,
            entity_id=entity_id,
            payload=payload,
        )

    def pending_count(self, workspace_id: str) -> int:
        return self.repository.pending_count(workspace_id)

    def list_workspace_events(self, workspace_id: str) -> list[EventLog]:
        return self.repository.list_all_by_workspace(workspace_id)

    def mark_workspace_synced(self, workspace_id: str, synced_at: str) -> None:
        self.repository.mark_synced(workspace_id, synced_at)
