from __future__ import annotations

import subprocess

from core.enums import EntityType, EventType
from core.models import Repo, RepoLocalMapping
from core.repositories import RepoLocalMappingRepository, RepoRepository
from core.services.event_service import EventService
from core.utils.path_utils import expand_path
from core.utils.platform_utils import is_macos
from core.utils.validators import coerce_optional_str, require_non_empty


class RepoService:
    def __init__(
        self,
        repo_repository: RepoRepository,
        mapping_repository: RepoLocalMappingRepository,
        event_service: EventService,
    ) -> None:
        self.repo_repository = repo_repository
        self.mapping_repository = mapping_repository
        self.event_service = event_service

    def list_repos(self, workspace_id: str) -> list[Repo]:
        return self.repo_repository.list_by_workspace(workspace_id)

    def get_repo(self, repo_id: str | None) -> Repo | None:
        if not repo_id:
            return None
        return self.repo_repository.get(repo_id)

    def create_repo(
        self,
        workspace_id: str,
        display_name: str,
        canonical_remote: str,
        default_branch: str = "main",
        actor_user_id: str | None = None,
    ) -> Repo:
        require_non_empty(display_name, "Repo display name")
        require_non_empty(canonical_remote, "Canonical remote")
        repo = self.repo_repository.create(workspace_id, display_name, canonical_remote, default_branch)
        self.event_service.emit(
            workspace_id=workspace_id,
            actor_user_id=actor_user_id,
            event_type=EventType.REPO_CREATED,
            entity_type=EntityType.REPO,
            entity_id=repo.id,
            payload=repo.to_dict(),
        )
        return repo

    def update_repo(self, repo_id: str, actor_user_id: str | None = None, **fields_to_update: str) -> Repo:
        repo = self.repo_repository.update(repo_id, **fields_to_update)
        self.event_service.emit(
            workspace_id=repo.workspace_id,
            actor_user_id=actor_user_id,
            event_type=EventType.REPO_UPDATED,
            entity_type=EntityType.REPO,
            entity_id=repo.id,
            payload=repo.to_dict(),
        )
        return repo

    def get_mapping(self, repo_id: str | None, user_id: str | None) -> RepoLocalMapping | None:
        if not repo_id or not user_id:
            return None
        return self.mapping_repository.get_for_repo_user(repo_id, user_id)

    def list_mappings(self, workspace_id: str) -> list[RepoLocalMapping]:
        return self.mapping_repository.list_by_workspace(workspace_id)

    def upsert_mapping(self, workspace_id: str, repo_id: str, user_id: str, local_path: str) -> RepoLocalMapping:
        require_non_empty(local_path, "Local path")
        mapping = self.mapping_repository.upsert(repo_id, user_id, local_path)
        self.event_service.emit(
            workspace_id=workspace_id,
            actor_user_id=user_id,
            event_type=EventType.REPO_MAPPING_UPDATED,
            entity_type=EntityType.REPO_MAPPING,
            entity_id=mapping.id,
            payload=mapping.to_dict(),
        )
        return mapping

    def open_local_path(self, local_path: str | None) -> tuple[bool, str]:
        resolved = expand_path(coerce_optional_str(local_path))
        if not resolved or not resolved.exists():
            return False, "Local path is not configured or does not exist."
        command = ["open", str(resolved)] if is_macos() else ["xdg-open", str(resolved)]
        try:
            subprocess.Popen(command)
        except Exception as exc:
            return False, f"Unable to open path: {exc}"
        return True, f"Opened {resolved}"
