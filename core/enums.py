from __future__ import annotations

from enum import StrEnum


class TaskStatus(StrEnum):
    BACKLOG = "backlog"
    DOING = "doing"
    REVIEW = "review"
    DONE = "done"


class TaskPriority(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class CommitPolicy(StrEnum):
    NONE = "none"
    OPTIONAL = "optional"
    REQUIRED = "required"


class PomodoroState(StrEnum):
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    FINISHED = "finished"
    CANCELLED = "cancelled"


class PresenceStatus(StrEnum):
    ACTIVE = "active"
    IDLE = "idle"
    OFFLINE = "offline"


class SyncState(StrEnum):
    OFFLINE = "offline"
    PENDING = "pending"
    SYNCED = "synced"
    ERROR = "error"


class PunchType(StrEnum):
    CLOCK_IN = "clock_in"
    CLOCK_OUT = "clock_out"


class EventType(StrEnum):
    WORKSPACE_CREATED = "workspace_created"
    USER_CREATED = "user_created"
    REPO_CREATED = "repo_created"
    REPO_UPDATED = "repo_updated"
    REPO_MAPPING_UPDATED = "repo_mapping_updated"
    TASK_CREATED = "task_created"
    TASK_UPDATED = "task_updated"
    TASK_MOVED = "task_moved"
    TASK_ASSIGNED = "task_assigned"
    TASK_SET_ACTIVE = "task_set_active"
    TASK_CLEARED_ACTIVE = "task_cleared_active"
    TASK_COMPLETED = "task_completed"
    POMODORO_STARTED = "pomodoro_started"
    POMODORO_PAUSED = "pomodoro_paused"
    POMODORO_RESUMED = "pomodoro_resumed"
    POMODORO_FINISHED = "pomodoro_finished"
    WORK_SESSION_STARTED = "work_session_started"
    WORK_SESSION_ENDED = "work_session_ended"
    CLOCK_IN = "clock_in"
    CLOCK_OUT = "clock_out"
    SYNC_COMPLETED = "sync_completed"


class EntityType(StrEnum):
    WORKSPACE = "workspace"
    USER = "user"
    REPO = "repo"
    REPO_MAPPING = "repo_mapping"
    TASK = "task"
    ACTIVE_TASK = "active_task"
    POMODORO = "pomodoro"
    WORK_SESSION = "work_session"
    PUNCH = "punch"
