from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from core.utils.logger import get_logger
from core.utils.platform_utils import get_db_path

LOGGER = get_logger("workpulse.db")


class Database:
    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = db_path or get_db_path()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        conn = self._connect()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def fetch_all(self, sql: str, params: tuple | dict | None = None) -> list[sqlite3.Row]:
        with self.transaction() as conn:
            cursor = conn.execute(sql, params or ())
            return list(cursor.fetchall())

    def fetch_one(self, sql: str, params: tuple | dict | None = None) -> sqlite3.Row | None:
        with self.transaction() as conn:
            cursor = conn.execute(sql, params or ())
            return cursor.fetchone()

    def execute(self, sql: str, params: tuple | dict | None = None) -> None:
        with self.transaction() as conn:
            conn.execute(sql, params or ())

    def executemany(self, sql: str, params: list[tuple]) -> None:
        with self.transaction() as conn:
            conn.executemany(sql, params)

    def _init_db(self) -> None:
        LOGGER.info("Initializing database at %s", self.db_path)
        with self.transaction() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS workspaces (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    sync_enabled INTEGER NOT NULL DEFAULT 0,
                    sync_repo_local_path TEXT,
                    sync_remote_url TEXT,
                    sync_branch TEXT NOT NULL DEFAULT 'main',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    workspace_id TEXT NOT NULL,
                    display_name TEXT NOT NULL,
                    is_current_local_user INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY(workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS repos (
                    id TEXT PRIMARY KEY,
                    workspace_id TEXT NOT NULL,
                    display_name TEXT NOT NULL,
                    canonical_remote TEXT NOT NULL,
                    default_branch TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY(workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS repo_local_mappings (
                    id TEXT PRIMARY KEY,
                    repo_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    local_path TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    UNIQUE(repo_id, user_id),
                    FOREIGN KEY(repo_id) REFERENCES repos(id) ON DELETE CASCADE,
                    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    workspace_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL DEFAULT '',
                    assignee_user_id TEXT,
                    status TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    tags_json TEXT NOT NULL DEFAULT '[]',
                    repo_id TEXT,
                    branch_name TEXT,
                    commit_policy TEXT NOT NULL,
                    completion_commit_hash TEXT,
                    completion_commit_message TEXT,
                    completion_timestamp TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY(workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE,
                    FOREIGN KEY(assignee_user_id) REFERENCES users(id) ON DELETE SET NULL,
                    FOREIGN KEY(repo_id) REFERENCES repos(id) ON DELETE SET NULL
                );

                CREATE TABLE IF NOT EXISTS active_tasks (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL UNIQUE,
                    task_id TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY(task_id) REFERENCES tasks(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS pomodoro_sessions (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    task_id TEXT,
                    started_at TEXT NOT NULL,
                    ended_at TEXT,
                    duration_minutes INTEGER NOT NULL,
                    state TEXT NOT NULL,
                    planned_end_at TEXT,
                    paused_remaining_seconds INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY(task_id) REFERENCES tasks(id) ON DELETE SET NULL
                );

                CREATE TABLE IF NOT EXISTS work_sessions (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    task_id TEXT,
                    started_at TEXT NOT NULL,
                    ended_at TEXT,
                    notes TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY(task_id) REFERENCES tasks(id) ON DELETE SET NULL
                );

                CREATE TABLE IF NOT EXISTS punch_records (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    punch_type TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS event_logs (
                    event_id TEXT PRIMARY KEY,
                    workspace_id TEXT NOT NULL,
                    actor_user_id TEXT,
                    event_type TEXT NOT NULL,
                    entity_type TEXT NOT NULL,
                    entity_id TEXT,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    synced_at TEXT
                );

                CREATE INDEX IF NOT EXISTS idx_users_workspace ON users(workspace_id);
                CREATE INDEX IF NOT EXISTS idx_repos_workspace ON repos(workspace_id);
                CREATE INDEX IF NOT EXISTS idx_tasks_workspace_status ON tasks(workspace_id, status);
                CREATE INDEX IF NOT EXISTS idx_tasks_assignee ON tasks(assignee_user_id);
                CREATE INDEX IF NOT EXISTS idx_events_workspace_created ON event_logs(workspace_id, created_at);
                CREATE INDEX IF NOT EXISTS idx_events_unsynced ON event_logs(workspace_id, synced_at);
                CREATE INDEX IF NOT EXISTS idx_pomodoro_user_state ON pomodoro_sessions(user_id, state);
                CREATE INDEX IF NOT EXISTS idx_work_sessions_user_open ON work_sessions(user_id, ended_at);
                CREATE INDEX IF NOT EXISTS idx_punch_user_created ON punch_records(user_id, created_at);
                """
            )
