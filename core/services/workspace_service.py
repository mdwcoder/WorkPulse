from __future__ import annotations

from core.enums import EntityType, EventType
from core.models import User, Workspace
from core.repositories import UserRepository, WorkspaceRepository
from core.services.event_service import EventService
from core.utils.validators import require_non_empty
from storage.settings_store import SettingsStore


class WorkspaceService:
    def __init__(
        self,
        workspace_repository: WorkspaceRepository,
        user_repository: UserRepository,
        event_service: EventService,
        settings_store: SettingsStore,
    ) -> None:
        self.workspace_repository = workspace_repository
        self.user_repository = user_repository
        self.event_service = event_service
        self.settings_store = settings_store

    def list_workspaces(self) -> list[Workspace]:
        return self.workspace_repository.list_all()

    def create_workspace(self, name: str, owner_display_name: str | None = None) -> Workspace:
        require_non_empty(name, "Workspace name")
        workspace = self.workspace_repository.create(name=name)
        self.event_service.emit(
            workspace_id=workspace.id,
            actor_user_id=None,
            event_type=EventType.WORKSPACE_CREATED,
            entity_type=EntityType.WORKSPACE,
            entity_id=workspace.id,
            payload=workspace.to_dict(),
        )
        settings = self.settings_store.load()
        settings.last_workspace_id = workspace.id
        self.settings_store.save(settings)
        if owner_display_name:
            self.create_user(workspace.id, owner_display_name, make_current=True)
        return workspace

    def get_workspace(self, workspace_id: str | None) -> Workspace | None:
        if not workspace_id:
            return None
        return self.workspace_repository.get(workspace_id)

    def get_current_workspace(self) -> Workspace | None:
        settings = self.settings_store.load()
        if settings.restore_last_workspace and settings.last_workspace_id:
            current = self.get_workspace(settings.last_workspace_id)
            if current:
                return current
        workspaces = self.list_workspaces()
        return workspaces[0] if workspaces else None

    def select_workspace(self, workspace_id: str) -> Workspace | None:
        workspace = self.get_workspace(workspace_id)
        if not workspace:
            return None
        settings = self.settings_store.load()
        settings.last_workspace_id = workspace_id
        self.settings_store.save(settings)
        return workspace

    def update_sync_settings(
        self,
        workspace_id: str,
        *,
        sync_enabled: bool,
        sync_repo_local_path: str | None,
        sync_remote_url: str | None,
        sync_branch: str,
    ) -> Workspace:
        return self.workspace_repository.update(
            workspace_id,
            sync_enabled=int(sync_enabled),
            sync_repo_local_path=sync_repo_local_path,
            sync_remote_url=sync_remote_url,
            sync_branch=sync_branch,
        )

    def list_users(self, workspace_id: str) -> list[User]:
        return self.user_repository.list_by_workspace(workspace_id)

    def create_user(self, workspace_id: str, display_name: str, make_current: bool = False) -> User:
        require_non_empty(display_name, "User name")
        user = self.user_repository.create(workspace_id, display_name, is_current_local_user=make_current)
        if make_current:
            self.user_repository.set_current(workspace_id, user.id)
            settings = self.settings_store.load()
            settings.current_user_id = user.id
            self.settings_store.save(settings)
        self.event_service.emit(
            workspace_id=workspace_id,
            actor_user_id=user.id if make_current else None,
            event_type=EventType.USER_CREATED,
            entity_type=EntityType.USER,
            entity_id=user.id,
            payload=user.to_dict(),
        )
        return user

    def get_current_user(self, workspace_id: str) -> User | None:
        settings = self.settings_store.load()
        if settings.current_user_id:
            users = {user.id: user for user in self.list_users(workspace_id)}
            saved = users.get(settings.current_user_id)
            if saved:
                return saved
        current = self.user_repository.get_current(workspace_id)
        if current:
            return current
        users = self.list_users(workspace_id)
        return users[0] if users else None

    def set_current_user(self, workspace_id: str, user_id: str) -> None:
        self.user_repository.set_current(workspace_id, user_id)
        settings = self.settings_store.load()
        settings.current_user_id = user_id
        self.settings_store.save(settings)
