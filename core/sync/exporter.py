from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

from core.db import Database
from core.models import EventLog
from core.repositories import (
    ActiveTaskRepository,
    EventRepository,
    PomodoroRepository,
    PunchRepository,
    RepoLocalMappingRepository,
    RepoRepository,
    TaskRepository,
    UserRepository,
    WorkSessionRepository,
    WorkspaceRepository,
)


class SyncExporter:
    def __init__(self, db: Database) -> None:
        self.workspace_repository = WorkspaceRepository(db)
        self.user_repository = UserRepository(db)
        self.repo_repository = RepoRepository(db)
        self.mapping_repository = RepoLocalMappingRepository(db)
        self.task_repository = TaskRepository(db)
        self.active_repository = ActiveTaskRepository(db)
        self.pomodoro_repository = PomodoroRepository(db)
        self.work_session_repository = WorkSessionRepository(db)
        self.punch_repository = PunchRepository(db)
        self.event_repository = EventRepository(db)

    def export_workspace(self, workspace_id: str, sync_repo_path: Path) -> None:
        sync_root = sync_repo_path / "workpulse-sync"
        sync_root.mkdir(parents=True, exist_ok=True)
        (sync_root / "events").mkdir(parents=True, exist_ok=True)
        (sync_root / "snapshots").mkdir(parents=True, exist_ok=True)

        workspace = self.workspace_repository.get(workspace_id)
        if workspace is None:
            raise ValueError("Workspace not found for sync export.")
        users = self.user_repository.list_by_workspace(workspace_id)
        repos = self.repo_repository.list_by_workspace(workspace_id)
        mappings = self.mapping_repository.list_by_workspace(workspace_id)
        tasks = self.task_repository.list_by_workspace(workspace_id)
        active_tasks = self.active_repository.list_all()
        pomodoros = [session for user in users for session in self.pomodoro_repository.list_recent(user.id, limit=200)]
        work_sessions = [session for user in users for session in self.work_session_repository.list_recent(user.id, limit=200)]
        punches = [record for user in users for record in self.punch_repository.list_recent(user.id, limit=200)]
        events = self.event_repository.list_all_by_workspace(workspace_id)

        snapshot = {
            "workspace": workspace.to_dict(),
            "users": [item.to_dict() for item in users],
            "repos": [item.to_dict() for item in repos],
            "repo_mappings": [item.to_dict() for item in mappings],
            "tasks": [item.to_dict() for item in tasks],
            "active_tasks": [item.to_dict() for item in active_tasks if item.user_id in {user.id for user in users}],
            "pomodoros": [item.to_dict() for item in pomodoros],
            "work_sessions": [item.to_dict() for item in work_sessions],
            "punches": [item.to_dict() for item in punches],
        }

        (sync_root / "workspace.json").write_text(json.dumps(workspace.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
        (sync_root / "users.json").write_text(json.dumps(snapshot["users"], indent=2, ensure_ascii=False), encoding="utf-8")
        (sync_root / "repos.json").write_text(
            json.dumps(
                {
                    "repos": snapshot["repos"],
                    "repo_mappings": snapshot["repo_mappings"],
                },
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        (sync_root / "snapshots" / "latest.json").write_text(json.dumps(snapshot, indent=2, ensure_ascii=False), encoding="utf-8")

        buckets: dict[str, list[EventLog]] = defaultdict(list)
        for event in events:
            bucket = event.created_at[:10]
            buckets[bucket].append(event)
        for bucket, items in buckets.items():
            lines = "\n".join(json.dumps(event.to_dict(), ensure_ascii=False) for event in items)
            (sync_root / "events" / f"{bucket}.jsonl").write_text(lines + ("\n" if lines else ""), encoding="utf-8")
