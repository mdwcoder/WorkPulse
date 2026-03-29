from __future__ import annotations

import json
from pathlib import Path

from core.db import Database
from core.enums import CommitPolicy, PomodoroState, PunchType, TaskPriority, TaskStatus
from core.models import ActiveTask, EventLog, PomodoroSession, PunchRecord, Repo, RepoLocalMapping, Task, User, WorkSession, Workspace
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
from core.sync.conflict_handler import ConflictHandler


class SyncImporter:
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
        self.conflicts = ConflictHandler()

    def import_workspace(self, workspace_id: str, sync_repo_path: Path) -> None:
        snapshot_path = sync_repo_path / "workpulse-sync" / "snapshots" / "latest.json"
        if not snapshot_path.exists():
            return
        snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
        workspace = self._workspace(snapshot["workspace"])
        if workspace.id == workspace_id and self.conflicts.should_apply(self.workspace_repository.get(workspace.id), workspace):
            self.workspace_repository.upsert_snapshot(workspace)

        for user_data in snapshot.get("users", []):
            user = self._user(user_data)
            if self.conflicts.should_apply(self.user_repository.get(user.id), user):
                self.user_repository.upsert_snapshot(user)

        for repo_data in snapshot.get("repos", []):
            repo = self._repo(repo_data)
            if self.conflicts.should_apply(self.repo_repository.get(repo.id), repo):
                self.repo_repository.upsert_snapshot(repo)

        for mapping_data in snapshot.get("repo_mappings", []):
            mapping = self._mapping(mapping_data)
            if self.conflicts.should_apply(self.mapping_repository.get(mapping.id), mapping):
                self.mapping_repository.upsert_snapshot(mapping)

        for task_data in snapshot.get("tasks", []):
            task = self._task(task_data)
            if self.conflicts.should_apply(self.task_repository.get(task.id), task):
                self.task_repository.upsert_snapshot(task)

        for active_data in snapshot.get("active_tasks", []):
            active = ActiveTask(**active_data)
            if self.conflicts.should_apply(self.active_repository.get(active.id), active):
                self.active_repository.upsert_snapshot(active)

        for session_data in snapshot.get("pomodoros", []):
            session = self._pomodoro(session_data)
            if self.conflicts.should_apply(self.pomodoro_repository.get(session.id), session):
                self.pomodoro_repository.upsert_snapshot(session)

        for work_data in snapshot.get("work_sessions", []):
            session = WorkSession(**work_data)
            if self.conflicts.should_apply(self.work_session_repository.get(session.id), session):
                self.work_session_repository.upsert_snapshot(session)

        for punch_data in snapshot.get("punches", []):
            punch = self._punch(punch_data)
            self.punch_repository.upsert_snapshot(punch)

        events_dir = sync_repo_path / "workpulse-sync" / "events"
        if events_dir.exists():
            for file_path in sorted(events_dir.glob("*.jsonl")):
                for line in file_path.read_text(encoding="utf-8").splitlines():
                    if not line.strip():
                        continue
                    payload = json.loads(line)
                    self.event_repository.upsert_snapshot(EventLog(**payload))

    def _workspace(self, data: dict) -> Workspace:
        return Workspace(
            id=data["id"],
            name=data["name"],
            sync_enabled=bool(data["sync_enabled"]),
            sync_repo_local_path=data.get("sync_repo_local_path"),
            sync_remote_url=data.get("sync_remote_url"),
            sync_branch=data.get("sync_branch", "main"),
            created_at=data["created_at"],
            updated_at=data["updated_at"],
        )

    def _user(self, data: dict) -> User:
        return User(
            id=data["id"],
            workspace_id=data["workspace_id"],
            display_name=data["display_name"],
            is_current_local_user=bool(data["is_current_local_user"]),
            created_at=data["created_at"],
            updated_at=data["updated_at"],
        )

    def _repo(self, data: dict) -> Repo:
        return Repo(**data)

    def _mapping(self, data: dict) -> RepoLocalMapping:
        return RepoLocalMapping(**data)

    def _task(self, data: dict) -> Task:
        return Task(
            id=data["id"],
            workspace_id=data["workspace_id"],
            title=data["title"],
            description=data.get("description", ""),
            assignee_user_id=data.get("assignee_user_id"),
            status=TaskStatus(data["status"]),
            priority=TaskPriority(data["priority"]),
            tags_json=data.get("tags_json", "[]"),
            repo_id=data.get("repo_id"),
            branch_name=data.get("branch_name"),
            commit_policy=CommitPolicy(data["commit_policy"]),
            completion_commit_hash=data.get("completion_commit_hash"),
            completion_commit_message=data.get("completion_commit_message"),
            completion_timestamp=data.get("completion_timestamp"),
            created_at=data["created_at"],
            updated_at=data["updated_at"],
        )

    def _pomodoro(self, data: dict) -> PomodoroSession:
        return PomodoroSession(
            id=data["id"],
            user_id=data["user_id"],
            task_id=data.get("task_id"),
            started_at=data["started_at"],
            ended_at=data.get("ended_at"),
            duration_minutes=int(data["duration_minutes"]),
            state=PomodoroState(data["state"]),
            planned_end_at=data.get("planned_end_at"),
            paused_remaining_seconds=int(data.get("paused_remaining_seconds", 0)),
            created_at=data["created_at"],
            updated_at=data["updated_at"],
        )

    def _punch(self, data: dict) -> PunchRecord:
        return PunchRecord(
            id=data["id"],
            user_id=data["user_id"],
            punch_type=PunchType(data["punch_type"]),
            created_at=data["created_at"],
        )
