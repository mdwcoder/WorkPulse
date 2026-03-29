from __future__ import annotations

from core.enums import SyncState
from core.models import SyncResult, User, Workspace
from core.services.event_service import EventService
from core.services.git_service import GitService
from core.sync.exporter import SyncExporter
from core.sync.importer import SyncImporter
from core.utils.logger import get_logger
from core.utils.path_utils import expand_path
from core.utils.time_utils import utc_now_iso
from storage.settings_store import SettingsStore

LOGGER = get_logger("workpulse.sync.service")


class SyncService:
    def __init__(
        self,
        git_service: GitService,
        exporter: SyncExporter,
        importer: SyncImporter,
        event_service: EventService,
        settings_store: SettingsStore,
    ) -> None:
        self.git_service = git_service
        self.exporter = exporter
        self.importer = importer
        self.event_service = event_service
        self.settings_store = settings_store

    def _validate_workspace_sync(self, workspace: Workspace) -> tuple[bool, SyncResult | None, object | None]:
        if not workspace.sync_enabled:
            return False, SyncResult(False, state=SyncState.OFFLINE, message="Sync is disabled for this workspace."), None
        sync_path = expand_path(workspace.sync_repo_local_path)
        if not sync_path or not sync_path.exists():
            return False, SyncResult(False, state=SyncState.ERROR, message="Sync repository path is missing or invalid."), None
        if not self.git_service.repo_exists(sync_path):
            return False, SyncResult(False, state=SyncState.ERROR, message="Sync path is not a valid Git repository."), None
        return True, None, sync_path

    def init_sync_repo(self, workspace: Workspace) -> SyncResult:
        sync_path = expand_path(workspace.sync_repo_local_path)
        if not sync_path:
            return SyncResult(False, state=SyncState.ERROR, message="Sync repository path is missing.")
        init_ok, init_message = self.git_service.init_repo(sync_path, workspace.sync_branch)
        if not init_ok:
            return SyncResult(False, state=SyncState.ERROR, message=init_message)
        branch_ok, branch_message = self.git_service.ensure_branch(sync_path, workspace.sync_branch)
        if not branch_ok:
            return SyncResult(False, state=SyncState.ERROR, message=branch_message)
        if workspace.sync_remote_url:
            remote_ok, remote_message = self.git_service.set_remote_origin(sync_path, workspace.sync_remote_url)
            if not remote_ok:
                return SyncResult(False, state=SyncState.ERROR, message=remote_message)
        return SyncResult(True, state=SyncState.SYNCED, message="Sync repository initialized.")

    def pull_only(self, workspace: Workspace) -> SyncResult:
        valid, failure, sync_path = self._validate_workspace_sync(workspace)
        if not valid:
            return failure
        pull_ok, pull_message = self.git_service.sync_pull_rebase(sync_path, workspace.sync_branch)
        if not pull_ok:
            return SyncResult(False, state=SyncState.ERROR, message=f"Pull failed: {pull_message}")
        self.importer.import_workspace(workspace.id, sync_path)
        return SyncResult(True, state=SyncState.SYNCED, message="Pull completed and snapshot imported.")

    def push_only(self, workspace: Workspace) -> SyncResult:
        valid, failure, sync_path = self._validate_workspace_sync(workspace)
        if not valid:
            return failure
        self.exporter.export_workspace(workspace.id, sync_path)
        add_ok, add_message = self.git_service.add_all(sync_path)
        if not add_ok:
            return SyncResult(False, state=SyncState.ERROR, message=f"git add failed: {add_message}")
        if self.git_service.has_index_changes(sync_path) or self.git_service.has_worktree_changes(sync_path):
            commit_ok, commit_message, _ = self.git_service.commit(
                sync_path,
                f"chore(sync): workspace {workspace.name} at {utc_now_iso()}",
            )
            if not commit_ok:
                return SyncResult(False, state=SyncState.ERROR, message=commit_message)
        push_ok, push_message = self.git_service.push(sync_path, workspace.sync_branch)
        if not push_ok:
            return SyncResult(False, state=SyncState.ERROR, message=f"Push failed: {push_message}")
        synced_at = utc_now_iso()
        self.event_service.mark_workspace_synced(workspace.id, synced_at)
        settings = self.settings_store.load()
        settings.last_sync_at = synced_at
        self.settings_store.save(settings)
        return SyncResult(True, state=SyncState.SYNCED, message="Push completed successfully.", last_sync_at=synced_at)

    def full_sync(self, workspace: Workspace, actor_user: User | None) -> SyncResult:
        valid, failure, sync_path = self._validate_workspace_sync(workspace)
        if not valid:
            return failure

        pull_ok, pull_message = self.git_service.sync_pull_rebase(sync_path, workspace.sync_branch)
        if not pull_ok:
            LOGGER.error("Sync pull failed: %s", pull_message)
            return SyncResult(False, state=SyncState.ERROR, message=f"Pull failed: {pull_message}")

        self.importer.import_workspace(workspace.id, sync_path)
        self.exporter.export_workspace(workspace.id, sync_path)

        add_ok, add_message = self.git_service.add_all(sync_path)
        if not add_ok:
            return SyncResult(False, state=SyncState.ERROR, message=f"git add failed: {add_message}")

        if self.git_service.has_index_changes(sync_path) or self.git_service.has_worktree_changes(sync_path):
            commit_ok, commit_message, _ = self.git_service.commit(
                sync_path,
                f"chore(sync): workspace {workspace.name} at {utc_now_iso()}",
            )
            if not commit_ok:
                return SyncResult(False, state=SyncState.ERROR, message=commit_message)
            push_ok, push_message = self.git_service.push(sync_path, workspace.sync_branch)
            if not push_ok:
                return SyncResult(False, state=SyncState.ERROR, message=f"Push failed: {push_message}")

        synced_at = utc_now_iso()
        self.event_service.mark_workspace_synced(workspace.id, synced_at)
        settings = self.settings_store.load()
        settings.last_sync_at = synced_at
        self.settings_store.save(settings)
        return SyncResult(True, state=SyncState.SYNCED, message="Sync completed successfully.", last_sync_at=synced_at)
