from __future__ import annotations

import json
import uuid
from dataclasses import fields
from sqlite3 import Row
from typing import Any, TypeVar

from core.db import Database
from core.enums import CommitPolicy, PomodoroState, PunchType, TaskPriority, TaskStatus
from core.models import (
    ActiveTask,
    EventLog,
    PomodoroSession,
    PunchRecord,
    Repo,
    RepoLocalMapping,
    Task,
    User,
    WorkSession,
    Workspace,
)
from core.utils.time_utils import utc_now_iso

T = TypeVar("T")


def new_id() -> str:
    return str(uuid.uuid4())


def _base_payload(model_cls: type[T], row: Row | None) -> T | None:
    if row is None:
        return None
    keys = {field.name for field in fields(model_cls)}
    payload = {key: row[key] for key in row.keys() if key in keys}
    if model_cls is Workspace:
        payload["sync_enabled"] = bool(payload["sync_enabled"])
    if model_cls is User:
        payload["is_current_local_user"] = bool(payload["is_current_local_user"])
    if model_cls is Task:
        payload["status"] = TaskStatus(payload["status"])
        payload["priority"] = TaskPriority(payload["priority"])
        payload["commit_policy"] = CommitPolicy(payload["commit_policy"])
    if model_cls is PomodoroSession:
        payload["state"] = PomodoroState(payload["state"])
    if model_cls is PunchRecord:
        payload["punch_type"] = PunchType(payload["punch_type"])
    return model_cls(**payload)


class BaseRepository:
    table_name: str = ""
    model_cls: type

    def __init__(self, db: Database) -> None:
        self.db = db

    def get(self, entity_id: str) -> Any | None:
        row = self.db.fetch_one(f"SELECT * FROM {self.table_name} WHERE id = ?", (entity_id,))
        return _base_payload(self.model_cls, row)

    def delete(self, entity_id: str) -> None:
        self.db.execute(f"DELETE FROM {self.table_name} WHERE id = ?", (entity_id,))


class WorkspaceRepository(BaseRepository):
    table_name = "workspaces"
    model_cls = Workspace

    def list_all(self) -> list[Workspace]:
        return [_base_payload(Workspace, row) for row in self.db.fetch_all("SELECT * FROM workspaces ORDER BY name")]

    def create(self, name: str, sync_branch: str = "main") -> Workspace:
        now = utc_now_iso()
        workspace = Workspace(
            id=new_id(),
            name=name,
            sync_enabled=False,
            sync_repo_local_path=None,
            sync_remote_url=None,
            sync_branch=sync_branch,
            created_at=now,
            updated_at=now,
        )
        self.db.execute(
            """
            INSERT INTO workspaces (
                id, name, sync_enabled, sync_repo_local_path, sync_remote_url, sync_branch, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                workspace.id,
                workspace.name,
                int(workspace.sync_enabled),
                workspace.sync_repo_local_path,
                workspace.sync_remote_url,
                workspace.sync_branch,
                workspace.created_at,
                workspace.updated_at,
            ),
        )
        return workspace

    def update(self, workspace_id: str, **fields_to_update: Any) -> Workspace:
        fields_to_update["updated_at"] = utc_now_iso()
        set_clause = ", ".join(f"{key} = ?" for key in fields_to_update.keys())
        params = list(fields_to_update.values()) + [workspace_id]
        self.db.execute(f"UPDATE workspaces SET {set_clause} WHERE id = ?", tuple(params))
        workspace = self.get(workspace_id)
        if workspace is None:
            raise ValueError("Workspace not found after update.")
        return workspace

    def upsert_snapshot(self, workspace: Workspace) -> None:
        self.db.execute(
            """
            INSERT INTO workspaces (
                id, name, sync_enabled, sync_repo_local_path, sync_remote_url, sync_branch, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                name = excluded.name,
                sync_enabled = excluded.sync_enabled,
                sync_repo_local_path = excluded.sync_repo_local_path,
                sync_remote_url = excluded.sync_remote_url,
                sync_branch = excluded.sync_branch,
                updated_at = excluded.updated_at
            """,
            (
                workspace.id,
                workspace.name,
                int(workspace.sync_enabled),
                workspace.sync_repo_local_path,
                workspace.sync_remote_url,
                workspace.sync_branch,
                workspace.created_at,
                workspace.updated_at,
            ),
        )


class UserRepository(BaseRepository):
    table_name = "users"
    model_cls = User

    def list_by_workspace(self, workspace_id: str) -> list[User]:
        return [
            _base_payload(User, row)
            for row in self.db.fetch_all("SELECT * FROM users WHERE workspace_id = ? ORDER BY display_name", (workspace_id,))
        ]

    def create(self, workspace_id: str, display_name: str, is_current_local_user: bool = False) -> User:
        now = utc_now_iso()
        user = User(
            id=new_id(),
            workspace_id=workspace_id,
            display_name=display_name,
            is_current_local_user=is_current_local_user,
            created_at=now,
            updated_at=now,
        )
        self.db.execute(
            """
            INSERT INTO users (id, workspace_id, display_name, is_current_local_user, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                user.id,
                user.workspace_id,
                user.display_name,
                int(user.is_current_local_user),
                user.created_at,
                user.updated_at,
            ),
        )
        return user

    def set_current(self, workspace_id: str, user_id: str) -> None:
        with self.db.transaction() as conn:
            conn.execute("UPDATE users SET is_current_local_user = 0 WHERE workspace_id = ?", (workspace_id,))
            conn.execute(
                "UPDATE users SET is_current_local_user = 1, updated_at = ? WHERE id = ?",
                (utc_now_iso(), user_id),
            )

    def get_current(self, workspace_id: str) -> User | None:
        row = self.db.fetch_one(
            "SELECT * FROM users WHERE workspace_id = ? AND is_current_local_user = 1 LIMIT 1",
            (workspace_id,),
        )
        return _base_payload(User, row)

    def upsert_snapshot(self, user: User) -> None:
        self.db.execute(
            """
            INSERT INTO users (id, workspace_id, display_name, is_current_local_user, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                workspace_id = excluded.workspace_id,
                display_name = excluded.display_name,
                is_current_local_user = excluded.is_current_local_user,
                updated_at = excluded.updated_at
            """,
            (user.id, user.workspace_id, user.display_name, int(user.is_current_local_user), user.created_at, user.updated_at),
        )


class RepoRepository(BaseRepository):
    table_name = "repos"
    model_cls = Repo

    def list_by_workspace(self, workspace_id: str) -> list[Repo]:
        return [
            _base_payload(Repo, row)
            for row in self.db.fetch_all("SELECT * FROM repos WHERE workspace_id = ? ORDER BY display_name", (workspace_id,))
        ]

    def create(self, workspace_id: str, display_name: str, canonical_remote: str, default_branch: str) -> Repo:
        now = utc_now_iso()
        repo = Repo(
            id=new_id(),
            workspace_id=workspace_id,
            display_name=display_name,
            canonical_remote=canonical_remote,
            default_branch=default_branch,
            created_at=now,
            updated_at=now,
        )
        self.db.execute(
            """
            INSERT INTO repos (id, workspace_id, display_name, canonical_remote, default_branch, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (repo.id, repo.workspace_id, repo.display_name, repo.canonical_remote, repo.default_branch, repo.created_at, repo.updated_at),
        )
        return repo

    def update(self, repo_id: str, **fields_to_update: Any) -> Repo:
        fields_to_update["updated_at"] = utc_now_iso()
        set_clause = ", ".join(f"{key} = ?" for key in fields_to_update.keys())
        params = list(fields_to_update.values()) + [repo_id]
        self.db.execute(f"UPDATE repos SET {set_clause} WHERE id = ?", tuple(params))
        repo = self.get(repo_id)
        if repo is None:
            raise ValueError("Repo not found after update.")
        return repo

    def upsert_snapshot(self, repo: Repo) -> None:
        self.db.execute(
            """
            INSERT INTO repos (id, workspace_id, display_name, canonical_remote, default_branch, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                workspace_id = excluded.workspace_id,
                display_name = excluded.display_name,
                canonical_remote = excluded.canonical_remote,
                default_branch = excluded.default_branch,
                updated_at = excluded.updated_at
            """,
            (repo.id, repo.workspace_id, repo.display_name, repo.canonical_remote, repo.default_branch, repo.created_at, repo.updated_at),
        )


class RepoLocalMappingRepository(BaseRepository):
    table_name = "repo_local_mappings"
    model_cls = RepoLocalMapping

    def list_by_user(self, user_id: str) -> list[RepoLocalMapping]:
        return [
            _base_payload(RepoLocalMapping, row)
            for row in self.db.fetch_all("SELECT * FROM repo_local_mappings WHERE user_id = ? ORDER BY updated_at DESC", (user_id,))
        ]

    def list_by_workspace(self, workspace_id: str) -> list[RepoLocalMapping]:
        return [
            _base_payload(RepoLocalMapping, row)
            for row in self.db.fetch_all(
                """
                SELECT m.*
                FROM repo_local_mappings m
                JOIN repos r ON r.id = m.repo_id
                WHERE r.workspace_id = ?
                ORDER BY m.updated_at DESC
                """,
                (workspace_id,),
            )
        ]

    def get_for_repo_user(self, repo_id: str, user_id: str) -> RepoLocalMapping | None:
        row = self.db.fetch_one(
            "SELECT * FROM repo_local_mappings WHERE repo_id = ? AND user_id = ? LIMIT 1",
            (repo_id, user_id),
        )
        return _base_payload(RepoLocalMapping, row)

    def upsert(self, repo_id: str, user_id: str, local_path: str) -> RepoLocalMapping:
        now = utc_now_iso()
        existing = self.get_for_repo_user(repo_id, user_id)
        mapping_id = existing.id if existing else new_id()
        self.db.execute(
            """
            INSERT INTO repo_local_mappings (id, repo_id, user_id, local_path, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(repo_id, user_id) DO UPDATE SET
                local_path = excluded.local_path,
                updated_at = excluded.updated_at
            """,
            (mapping_id, repo_id, user_id, local_path, existing.created_at if existing else now, now),
        )
        mapping = self.get_for_repo_user(repo_id, user_id)
        if mapping is None:
            raise ValueError("Repo mapping not found after upsert.")
        return mapping

    def upsert_snapshot(self, mapping: RepoLocalMapping) -> None:
        self.db.execute(
            """
            INSERT INTO repo_local_mappings (id, repo_id, user_id, local_path, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                repo_id = excluded.repo_id,
                user_id = excluded.user_id,
                local_path = excluded.local_path,
                updated_at = excluded.updated_at
            """,
            (mapping.id, mapping.repo_id, mapping.user_id, mapping.local_path, mapping.created_at, mapping.updated_at),
        )


class TaskRepository(BaseRepository):
    table_name = "tasks"
    model_cls = Task

    def list_by_workspace(self, workspace_id: str) -> list[Task]:
        return [
            _base_payload(Task, row)
            for row in self.db.fetch_all("SELECT * FROM tasks WHERE workspace_id = ? ORDER BY updated_at DESC", (workspace_id,))
        ]

    def create(
        self,
        workspace_id: str,
        title: str,
        description: str,
        assignee_user_id: str | None,
        status: TaskStatus,
        priority: TaskPriority,
        tags: list[str],
        repo_id: str | None,
        branch_name: str | None,
        commit_policy: CommitPolicy,
    ) -> Task:
        now = utc_now_iso()
        task = Task(
            id=new_id(),
            workspace_id=workspace_id,
            title=title,
            description=description,
            assignee_user_id=assignee_user_id,
            status=status,
            priority=priority,
            tags_json=json.dumps(tags),
            repo_id=repo_id,
            branch_name=branch_name,
            commit_policy=commit_policy,
            completion_commit_hash=None,
            completion_commit_message=None,
            completion_timestamp=None,
            created_at=now,
            updated_at=now,
        )
        self._upsert(task, insert_only=True)
        return task

    def update(self, task_id: str, **fields_to_update: Any) -> Task:
        if "tags" in fields_to_update:
            fields_to_update["tags_json"] = json.dumps(fields_to_update.pop("tags"))
        for key in ("status", "priority", "commit_policy"):
            if key in fields_to_update and hasattr(fields_to_update[key], "value"):
                fields_to_update[key] = fields_to_update[key].value
        fields_to_update["updated_at"] = utc_now_iso()
        set_clause = ", ".join(f"{key} = ?" for key in fields_to_update.keys())
        params = list(fields_to_update.values()) + [task_id]
        self.db.execute(f"UPDATE tasks SET {set_clause} WHERE id = ?", tuple(params))
        task = self.get(task_id)
        if task is None:
            raise ValueError("Task not found after update.")
        return task

    def list_completed_by_user(self, workspace_id: str, user_id: str) -> list[Task]:
        return [
            _base_payload(Task, row)
            for row in self.db.fetch_all(
                """
                SELECT * FROM tasks
                WHERE workspace_id = ? AND assignee_user_id = ? AND status = ?
                ORDER BY completion_timestamp DESC
                """,
                (workspace_id, user_id, TaskStatus.DONE.value),
            )
        ]

    def _upsert(self, task: Task, insert_only: bool = False) -> None:
        sql = """
            INSERT INTO tasks (
                id, workspace_id, title, description, assignee_user_id, status, priority, tags_json,
                repo_id, branch_name, commit_policy, completion_commit_hash, completion_commit_message,
                completion_timestamp, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            task.id,
            task.workspace_id,
            task.title,
            task.description,
            task.assignee_user_id,
            task.status.value,
            task.priority.value,
            task.tags_json,
            task.repo_id,
            task.branch_name,
            task.commit_policy.value,
            task.completion_commit_hash,
            task.completion_commit_message,
            task.completion_timestamp,
            task.created_at,
            task.updated_at,
        )
        if insert_only:
            self.db.execute(sql, params)
            return
        self.db.execute(
            sql
            + """
            ON CONFLICT(id) DO UPDATE SET
                workspace_id = excluded.workspace_id,
                title = excluded.title,
                description = excluded.description,
                assignee_user_id = excluded.assignee_user_id,
                status = excluded.status,
                priority = excluded.priority,
                tags_json = excluded.tags_json,
                repo_id = excluded.repo_id,
                branch_name = excluded.branch_name,
                commit_policy = excluded.commit_policy,
                completion_commit_hash = excluded.completion_commit_hash,
                completion_commit_message = excluded.completion_commit_message,
                completion_timestamp = excluded.completion_timestamp,
                updated_at = excluded.updated_at
            """,
            params,
        )

    def upsert_snapshot(self, task: Task) -> None:
        self._upsert(task, insert_only=False)


class ActiveTaskRepository(BaseRepository):
    table_name = "active_tasks"
    model_cls = ActiveTask

    def get_for_user(self, user_id: str) -> ActiveTask | None:
        row = self.db.fetch_one("SELECT * FROM active_tasks WHERE user_id = ? LIMIT 1", (user_id,))
        return _base_payload(ActiveTask, row)

    def set(self, user_id: str, task_id: str) -> ActiveTask:
        now = utc_now_iso()
        existing = self.get_for_user(user_id)
        active = ActiveTask(
            id=existing.id if existing else new_id(),
            user_id=user_id,
            task_id=task_id,
            started_at=existing.started_at if existing else now,
            updated_at=now,
        )
        self.db.execute(
            """
            INSERT INTO active_tasks (id, user_id, task_id, started_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                task_id = excluded.task_id,
                updated_at = excluded.updated_at
            """,
            (active.id, active.user_id, active.task_id, active.started_at, active.updated_at),
        )
        refreshed = self.get_for_user(user_id)
        if refreshed is None:
            raise ValueError("Active task not found after update.")
        return refreshed

    def clear(self, user_id: str) -> None:
        self.db.execute("DELETE FROM active_tasks WHERE user_id = ?", (user_id,))

    def list_all(self) -> list[ActiveTask]:
        return [_base_payload(ActiveTask, row) for row in self.db.fetch_all("SELECT * FROM active_tasks")]

    def upsert_snapshot(self, active: ActiveTask) -> None:
        self.db.execute(
            """
            INSERT INTO active_tasks (id, user_id, task_id, started_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                user_id = excluded.user_id,
                task_id = excluded.task_id,
                started_at = excluded.started_at,
                updated_at = excluded.updated_at
            """,
            (active.id, active.user_id, active.task_id, active.started_at, active.updated_at),
        )


class PomodoroRepository(BaseRepository):
    table_name = "pomodoro_sessions"
    model_cls = PomodoroSession

    def list_recent(self, user_id: str, limit: int = 12) -> list[PomodoroSession]:
        return [
            _base_payload(PomodoroSession, row)
            for row in self.db.fetch_all(
                "SELECT * FROM pomodoro_sessions WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
                (user_id, limit),
            )
        ]

    def get_current(self, user_id: str) -> PomodoroSession | None:
        row = self.db.fetch_one(
            """
            SELECT * FROM pomodoro_sessions
            WHERE user_id = ? AND state IN (?, ?)
            ORDER BY created_at DESC LIMIT 1
            """,
            (user_id, PomodoroState.RUNNING.value, PomodoroState.PAUSED.value),
        )
        return _base_payload(PomodoroSession, row)

    def create(self, user_id: str, task_id: str | None, duration_minutes: int, planned_end_at: str) -> PomodoroSession:
        now = utc_now_iso()
        session = PomodoroSession(
            id=new_id(),
            user_id=user_id,
            task_id=task_id,
            started_at=now,
            ended_at=None,
            duration_minutes=duration_minutes,
            state=PomodoroState.RUNNING,
            planned_end_at=planned_end_at,
            paused_remaining_seconds=0,
            created_at=now,
            updated_at=now,
        )
        self.upsert_snapshot(session)
        return session

    def update(self, session_id: str, **fields_to_update: Any) -> PomodoroSession:
        for key in ("state",):
            if key in fields_to_update and hasattr(fields_to_update[key], "value"):
                fields_to_update[key] = fields_to_update[key].value
        fields_to_update["updated_at"] = utc_now_iso()
        set_clause = ", ".join(f"{key} = ?" for key in fields_to_update.keys())
        params = list(fields_to_update.values()) + [session_id]
        self.db.execute(f"UPDATE pomodoro_sessions SET {set_clause} WHERE id = ?", tuple(params))
        session = self.get(session_id)
        if session is None:
            raise ValueError("Pomodoro not found after update.")
        return session

    def upsert_snapshot(self, session: PomodoroSession) -> None:
        self.db.execute(
            """
            INSERT INTO pomodoro_sessions (
                id, user_id, task_id, started_at, ended_at, duration_minutes, state, planned_end_at,
                paused_remaining_seconds, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                user_id = excluded.user_id,
                task_id = excluded.task_id,
                started_at = excluded.started_at,
                ended_at = excluded.ended_at,
                duration_minutes = excluded.duration_minutes,
                state = excluded.state,
                planned_end_at = excluded.planned_end_at,
                paused_remaining_seconds = excluded.paused_remaining_seconds,
                updated_at = excluded.updated_at
            """,
            (
                session.id,
                session.user_id,
                session.task_id,
                session.started_at,
                session.ended_at,
                session.duration_minutes,
                session.state.value,
                session.planned_end_at,
                session.paused_remaining_seconds,
                session.created_at,
                session.updated_at,
            ),
        )


class WorkSessionRepository(BaseRepository):
    table_name = "work_sessions"
    model_cls = WorkSession

    def get_current(self, user_id: str) -> WorkSession | None:
        row = self.db.fetch_one(
            "SELECT * FROM work_sessions WHERE user_id = ? AND ended_at IS NULL ORDER BY started_at DESC LIMIT 1",
            (user_id,),
        )
        return _base_payload(WorkSession, row)

    def list_recent(self, user_id: str, limit: int = 12) -> list[WorkSession]:
        return [
            _base_payload(WorkSession, row)
            for row in self.db.fetch_all(
                "SELECT * FROM work_sessions WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
                (user_id, limit),
            )
        ]

    def create(self, user_id: str, task_id: str | None, notes: str | None = None) -> WorkSession:
        now = utc_now_iso()
        session = WorkSession(
            id=new_id(),
            user_id=user_id,
            task_id=task_id,
            started_at=now,
            ended_at=None,
            notes=notes,
            created_at=now,
            updated_at=now,
        )
        self.upsert_snapshot(session)
        return session

    def update(self, session_id: str, **fields_to_update: Any) -> WorkSession:
        fields_to_update["updated_at"] = utc_now_iso()
        set_clause = ", ".join(f"{key} = ?" for key in fields_to_update.keys())
        params = list(fields_to_update.values()) + [session_id]
        self.db.execute(f"UPDATE work_sessions SET {set_clause} WHERE id = ?", tuple(params))
        session = self.get(session_id)
        if session is None:
            raise ValueError("Work session not found after update.")
        return session

    def upsert_snapshot(self, session: WorkSession) -> None:
        self.db.execute(
            """
            INSERT INTO work_sessions (id, user_id, task_id, started_at, ended_at, notes, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                user_id = excluded.user_id,
                task_id = excluded.task_id,
                started_at = excluded.started_at,
                ended_at = excluded.ended_at,
                notes = excluded.notes,
                updated_at = excluded.updated_at
            """,
            (
                session.id,
                session.user_id,
                session.task_id,
                session.started_at,
                session.ended_at,
                session.notes,
                session.created_at,
                session.updated_at,
            ),
        )


class PunchRepository(BaseRepository):
    table_name = "punch_records"
    model_cls = PunchRecord

    def create(self, user_id: str, punch_type: PunchType) -> PunchRecord:
        record = PunchRecord(id=new_id(), user_id=user_id, punch_type=punch_type, created_at=utc_now_iso())
        self.upsert_snapshot(record)
        return record

    def get_last(self, user_id: str) -> PunchRecord | None:
        row = self.db.fetch_one(
            "SELECT * FROM punch_records WHERE user_id = ? ORDER BY created_at DESC LIMIT 1",
            (user_id,),
        )
        return _base_payload(PunchRecord, row)

    def list_recent(self, user_id: str, limit: int = 12) -> list[PunchRecord]:
        return [
            _base_payload(PunchRecord, row)
            for row in self.db.fetch_all(
                "SELECT * FROM punch_records WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
                (user_id, limit),
            )
        ]

    def upsert_snapshot(self, record: PunchRecord) -> None:
        self.db.execute(
            """
            INSERT INTO punch_records (id, user_id, punch_type, created_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                user_id = excluded.user_id,
                punch_type = excluded.punch_type,
                created_at = excluded.created_at
            """,
            (record.id, record.user_id, record.punch_type.value, record.created_at),
        )


class EventRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def list_unsynced(self, workspace_id: str) -> list[EventLog]:
        return [
            _base_payload(EventLog, row)
            for row in self.db.fetch_all(
                "SELECT * FROM event_logs WHERE workspace_id = ? AND synced_at IS NULL ORDER BY created_at",
                (workspace_id,),
            )
        ]

    def list_all_by_workspace(self, workspace_id: str) -> list[EventLog]:
        return [
            _base_payload(EventLog, row)
            for row in self.db.fetch_all("SELECT * FROM event_logs WHERE workspace_id = ? ORDER BY created_at", (workspace_id,))
        ]

    def create(
        self,
        workspace_id: str,
        actor_user_id: str | None,
        event_type: str,
        entity_type: str,
        entity_id: str | None,
        payload: dict[str, Any],
    ) -> EventLog:
        event = EventLog(
            event_id=new_id(),
            workspace_id=workspace_id,
            actor_user_id=actor_user_id,
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            payload_json=json.dumps(payload, ensure_ascii=False),
            created_at=utc_now_iso(),
            synced_at=None,
        )
        self.upsert_snapshot(event)
        return event

    def mark_synced(self, workspace_id: str, synced_at: str) -> None:
        self.db.execute(
            "UPDATE event_logs SET synced_at = ? WHERE workspace_id = ? AND synced_at IS NULL",
            (synced_at, workspace_id),
        )

    def pending_count(self, workspace_id: str) -> int:
        row = self.db.fetch_one(
            "SELECT COUNT(*) AS total FROM event_logs WHERE workspace_id = ? AND synced_at IS NULL",
            (workspace_id,),
        )
        return int(row["total"]) if row else 0

    def upsert_snapshot(self, event: EventLog) -> None:
        self.db.execute(
            """
            INSERT INTO event_logs (
                event_id, workspace_id, actor_user_id, event_type, entity_type, entity_id, payload_json, created_at, synced_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(event_id) DO UPDATE SET
                workspace_id = excluded.workspace_id,
                actor_user_id = excluded.actor_user_id,
                event_type = excluded.event_type,
                entity_type = excluded.entity_type,
                entity_id = excluded.entity_id,
                payload_json = excluded.payload_json,
                created_at = excluded.created_at,
                synced_at = excluded.synced_at
            """,
            (
                event.event_id,
                event.workspace_id,
                event.actor_user_id,
                event.event_type,
                event.entity_type,
                event.entity_id,
                event.payload_json,
                event.created_at,
                event.synced_at,
            ),
        )
