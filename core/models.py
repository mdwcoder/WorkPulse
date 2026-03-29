from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from core.enums import CommitPolicy, PomodoroState, PresenceStatus, PunchType, SyncState, TaskPriority, TaskStatus


@dataclass(slots=True)
class Workspace:
    id: str
    name: str
    sync_enabled: bool
    sync_repo_local_path: str | None
    sync_remote_url: str | None
    sync_branch: str
    created_at: str
    updated_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class User:
    id: str
    workspace_id: str
    display_name: str
    is_current_local_user: bool
    created_at: str
    updated_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class Repo:
    id: str
    workspace_id: str
    display_name: str
    canonical_remote: str
    default_branch: str
    created_at: str
    updated_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class RepoLocalMapping:
    id: str
    repo_id: str
    user_id: str
    local_path: str
    created_at: str
    updated_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class Task:
    id: str
    workspace_id: str
    title: str
    description: str
    assignee_user_id: str | None
    status: TaskStatus
    priority: TaskPriority
    tags_json: str
    repo_id: str | None
    branch_name: str | None
    commit_policy: CommitPolicy
    completion_commit_hash: str | None
    completion_commit_message: str | None
    completion_timestamp: str | None
    created_at: str
    updated_at: str

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["status"] = self.status.value
        payload["priority"] = self.priority.value
        payload["commit_policy"] = self.commit_policy.value
        return payload


@dataclass(slots=True)
class ActiveTask:
    id: str
    user_id: str
    task_id: str
    started_at: str
    updated_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class PomodoroSession:
    id: str
    user_id: str
    task_id: str | None
    started_at: str
    ended_at: str | None
    duration_minutes: int
    state: PomodoroState
    planned_end_at: str | None
    paused_remaining_seconds: int
    created_at: str
    updated_at: str

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["state"] = self.state.value
        return payload


@dataclass(slots=True)
class WorkSession:
    id: str
    user_id: str
    task_id: str | None
    started_at: str
    ended_at: str | None
    notes: str | None
    created_at: str
    updated_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class PunchRecord:
    id: str
    user_id: str
    punch_type: PunchType
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["punch_type"] = self.punch_type.value
        return payload


@dataclass(slots=True)
class EventLog:
    event_id: str
    workspace_id: str
    actor_user_id: str | None
    event_type: str
    entity_type: str
    entity_id: str | None
    payload_json: str
    created_at: str
    synced_at: str | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class WindowGeometry:
    width: float | None = None
    height: float | None = None
    left: float | None = None
    top: float | None = None
    always_on_top: bool = False


@dataclass(slots=True)
class AppSettings:
    dark_theme: bool = True
    remember_window_geometry: bool = True
    restore_last_workspace: bool = True
    start_always_on_top: bool = False
    compact_mode: bool = False
    manual_only_sync: bool = True
    auto_sync_on_startup: bool = False
    auto_sync_on_task_changes: bool = False
    pomodoro_work_minutes: int = 25
    pomodoro_short_break_minutes: int = 5
    pomodoro_long_break_minutes: int = 15
    pomodoro_auto_start_next: bool = False
    last_workspace_id: str | None = None
    current_user_id: str | None = None
    last_sync_at: str | None = None
    window_geometry: WindowGeometry = field(default_factory=WindowGeometry)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["window_geometry"] = asdict(self.window_geometry)
        return payload


@dataclass(slots=True)
class GitStatusSummary:
    valid_repo: bool
    branch: str | None
    modified_files: list[str]
    staged_files: list[str]
    unstaged_files: list[str]
    has_changes: bool
    error: str | None = None


@dataclass(slots=True)
class TaskCompletionContext:
    task: Task
    repo: Repo | None
    mapping: RepoLocalMapping | None
    status_summary: GitStatusSummary | None
    warning: str | None = None
    error: str | None = None
    suggested_commit_message: str | None = None


@dataclass(slots=True)
class TeamMemberSnapshot:
    user: User
    presence: PresenceStatus
    last_activity_at: str | None
    active_task: Task | None
    last_punch: PunchRecord | None
    last_completed_task: Task | None


@dataclass(slots=True)
class SyncResult:
    ok: bool
    state: SyncState
    message: str
    last_sync_at: str | None = None
