from __future__ import annotations

from dataclasses import replace

from app.controllers.board_controller import BoardController
from app.controllers.settings_controller import SettingsController
from app.controllers.sync_controller import SyncController
from app.controllers.task_controller import TaskController
from app.controllers.team_controller import TeamController
from app.controllers.time_controller import TimeController
from core.db import Database
from core.enums import SyncState
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
from core.services.event_service import EventService
from core.services.git_service import GitService
from core.services.pomodoro_service import PomodoroService
from core.services.punch_service import PunchService
from core.services.repo_service import RepoService
from core.services.sync_service import SyncService
from core.services.task_service import TaskService
from core.services.window_service import WindowService
from core.services.workspace_service import WorkspaceService
from core.sync.exporter import SyncExporter
from core.sync.importer import SyncImporter
from core.utils.logger import configure_logging, get_logger
from storage.settings_store import SettingsStore

LOGGER = get_logger("workpulse.app")


class AppController:
    def __init__(self) -> None:
        configure_logging()
        self.db = Database()
        self.settings_store = SettingsStore()
        self.settings = self.settings_store.load()

        workspace_repository = WorkspaceRepository(self.db)
        user_repository = UserRepository(self.db)
        repo_repository = RepoRepository(self.db)
        mapping_repository = RepoLocalMappingRepository(self.db)
        task_repository = TaskRepository(self.db)
        active_task_repository = ActiveTaskRepository(self.db)
        pomodoro_repository = PomodoroRepository(self.db)
        work_session_repository = WorkSessionRepository(self.db)
        punch_repository = PunchRepository(self.db)
        event_repository = EventRepository(self.db)

        self.event_service = EventService(event_repository)
        self.workspace_service = WorkspaceService(
            workspace_repository=workspace_repository,
            user_repository=user_repository,
            event_service=self.event_service,
            settings_store=self.settings_store,
        )
        self.repo_service = RepoService(
            repo_repository=repo_repository,
            mapping_repository=mapping_repository,
            event_service=self.event_service,
        )
        self.git_service = GitService()
        self.task_service = TaskService(
            task_repository=task_repository,
            active_task_repository=active_task_repository,
            repo_service=self.repo_service,
            git_service=self.git_service,
            event_service=self.event_service,
        )
        self.pomodoro_service = PomodoroService(pomodoro_repository, self.event_service)
        self.punch_service = PunchService(punch_repository, work_session_repository, self.event_service)
        self.sync_service = SyncService(
            git_service=self.git_service,
            exporter=SyncExporter(self.db),
            importer=SyncImporter(self.db),
            event_service=self.event_service,
            settings_store=self.settings_store,
        )
        self.window_service = WindowService(self.settings_store)

        self.board = BoardController(self)
        self.task = TaskController(self)
        self.time = TimeController(self)
        self.team = TeamController(self)
        self.sync = SyncController(self)
        self.settings_controller = SettingsController(self)

    def reload_settings(self) -> None:
        self.settings = self.settings_store.load()

    def save_settings(self) -> None:
        self.settings_store.save(self.settings)

    @property
    def current_workspace(self):
        return self.workspace_service.get_current_workspace()

    @property
    def current_user(self):
        workspace = self.current_workspace
        if not workspace:
            return None
        return self.workspace_service.get_current_user(workspace.id)

    def set_current_workspace(self, workspace_id: str) -> None:
        self.workspace_service.select_workspace(workspace_id)
        self.reload_settings()

    def set_current_user(self, user_id: str) -> None:
        workspace = self.current_workspace
        if not workspace:
            raise ValueError("No active workspace.")
        self.workspace_service.set_current_user(workspace.id, user_id)
        self.reload_settings()

    def sync_state(self) -> SyncState:
        workspace = self.current_workspace
        if not workspace or not workspace.sync_enabled:
            return SyncState.OFFLINE
        if self.sync.last_result and not self.sync.last_result.ok:
            return SyncState.ERROR
        if self.event_service.pending_count(workspace.id) > 0:
            return SyncState.PENDING
        return SyncState.SYNCED

    def footer_status(self) -> dict[str, str]:
        workspace = self.current_workspace
        user = self.current_user
        active_task = self.task_service.get_active_task(user.id) if user else None
        pending = self.event_service.pending_count(workspace.id) if workspace else 0
        pending_label = "Sync off"
        if workspace and workspace.sync_enabled:
            pending_label = str(pending)
        return {
            "last_sync": self.settings.last_sync_at or "Never",
            "pending": pending_label,
            "active_task": active_task.title if active_task else "None",
            "current_user": user.display_name if user else "No user",
        }

    def create_workspace(self, name: str, owner_name: str | None = None) -> None:
        workspace = self.workspace_service.create_workspace(name, owner_name)
        self.workspace_service.select_workspace(workspace.id)
        self.reload_settings()

    def ensure_defaults_after_first_workspace(self) -> None:
        workspace = self.current_workspace
        if not workspace:
            return
        users = self.workspace_service.list_users(workspace.id)
        if users and not self.current_user:
            self.set_current_user(users[0].id)

    def toggle_always_on_top_default(self, enabled: bool) -> None:
        self.settings = replace(self.settings, start_always_on_top=enabled)
        self.save_settings()
