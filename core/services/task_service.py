from __future__ import annotations

import json

from core.enums import CommitPolicy, EntityType, EventType, TaskPriority, TaskStatus
from core.models import Task, TaskCompletionContext
from core.repositories import ActiveTaskRepository, TaskRepository
from core.services.event_service import EventService
from core.services.git_service import GitService
from core.services.repo_service import RepoService
from core.utils.path_utils import is_existing_directory
from core.utils.time_utils import utc_now_iso
from core.utils.validators import require_non_empty


class TaskService:
    def __init__(
        self,
        task_repository: TaskRepository,
        active_task_repository: ActiveTaskRepository,
        repo_service: RepoService,
        git_service: GitService,
        event_service: EventService,
    ) -> None:
        self.task_repository = task_repository
        self.active_task_repository = active_task_repository
        self.repo_service = repo_service
        self.git_service = git_service
        self.event_service = event_service

    def list_tasks(self, workspace_id: str) -> list[Task]:
        return self.task_repository.list_by_workspace(workspace_id)

    def get_task(self, task_id: str | None) -> Task | None:
        if not task_id:
            return None
        return self.task_repository.get(task_id)

    def create_task(
        self,
        workspace_id: str,
        *,
        title: str,
        description: str,
        assignee_user_id: str | None,
        status: TaskStatus,
        priority: TaskPriority,
        tags: list[str],
        repo_id: str | None,
        branch_name: str | None,
        commit_policy: CommitPolicy,
        actor_user_id: str | None,
    ) -> Task:
        require_non_empty(title, "Task title")
        task = self.task_repository.create(
            workspace_id=workspace_id,
            title=title,
            description=description,
            assignee_user_id=assignee_user_id,
            status=status,
            priority=priority,
            tags=tags,
            repo_id=repo_id,
            branch_name=branch_name,
            commit_policy=commit_policy,
        )
        self.event_service.emit(
            workspace_id=workspace_id,
            actor_user_id=actor_user_id,
            event_type=EventType.TASK_CREATED,
            entity_type=EntityType.TASK,
            entity_id=task.id,
            payload=task.to_dict(),
        )
        return task

    def update_task(self, task_id: str, actor_user_id: str | None, **fields_to_update: object) -> Task:
        task = self.task_repository.update(task_id, **fields_to_update)
        event_type = EventType.TASK_ASSIGNED if "assignee_user_id" in fields_to_update else EventType.TASK_UPDATED
        self.event_service.emit(
            workspace_id=task.workspace_id,
            actor_user_id=actor_user_id,
            event_type=event_type,
            entity_type=EntityType.TASK,
            entity_id=task.id,
            payload=task.to_dict(),
        )
        return task

    def move_task(self, task_id: str, status: TaskStatus, actor_user_id: str | None) -> Task:
        task = self.task_repository.update(task_id, status=status)
        self.event_service.emit(
            workspace_id=task.workspace_id,
            actor_user_id=actor_user_id,
            event_type=EventType.TASK_MOVED,
            entity_type=EntityType.TASK,
            entity_id=task.id,
            payload={"status": task.status.value},
        )
        return task

    def set_active_task(self, workspace_id: str, user_id: str, task_id: str) -> None:
        active = self.active_task_repository.set(user_id, task_id)
        self.event_service.emit(
            workspace_id=workspace_id,
            actor_user_id=user_id,
            event_type=EventType.TASK_SET_ACTIVE,
            entity_type=EntityType.ACTIVE_TASK,
            entity_id=active.id,
            payload=active.to_dict(),
        )

    def clear_active_task(self, workspace_id: str, user_id: str) -> None:
        self.active_task_repository.clear(user_id)
        self.event_service.emit(
            workspace_id=workspace_id,
            actor_user_id=user_id,
            event_type=EventType.TASK_CLEARED_ACTIVE,
            entity_type=EntityType.ACTIVE_TASK,
            entity_id=user_id,
            payload={"user_id": user_id},
        )

    def get_active_task(self, user_id: str) -> Task | None:
        active = self.active_task_repository.get_for_user(user_id)
        return self.get_task(active.task_id) if active else None

    def build_completion_context(self, task_id: str, user_id: str) -> TaskCompletionContext:
        task = self.get_task(task_id)
        if task is None:
            raise ValueError("Task not found.")
        repo = self.repo_service.get_repo(task.repo_id)
        mapping = self.repo_service.get_mapping(task.repo_id, user_id) if task.repo_id else None
        suggested_message = f'feat(task): complete "{task.title}"'

        if not repo:
            return TaskCompletionContext(task=task, repo=None, mapping=None, status_summary=None, warning=None, error=None, suggested_commit_message=suggested_message)

        if not mapping:
            warning = "No local path mapping configured for the current user."
            return TaskCompletionContext(
                task=task,
                repo=repo,
                mapping=None,
                status_summary=None,
                warning=warning,
                suggested_commit_message=suggested_message,
            )

        if not is_existing_directory(mapping.local_path):
            return TaskCompletionContext(
                task=task,
                repo=repo,
                mapping=mapping,
                status_summary=None,
                error="Configured local path does not exist.",
                suggested_commit_message=suggested_message,
            )

        status_summary = self.git_service.get_status_summary(mapping.local_path)
        return TaskCompletionContext(
            task=task,
            repo=repo,
            mapping=mapping,
            status_summary=status_summary,
            warning=None if status_summary.valid_repo else status_summary.error,
            error=None if status_summary.valid_repo else status_summary.error,
            suggested_commit_message=suggested_message,
        )

    def complete_task(
        self,
        task_id: str,
        workspace_id: str,
        user_id: str,
        *,
        close_only: bool,
        commit_message: str | None,
    ) -> tuple[bool, str]:
        context = self.build_completion_context(task_id, user_id)
        task = context.task
        if task.commit_policy == CommitPolicy.REQUIRED and close_only:
            return False, "This task requires a commit before closing."

        commit_hash: str | None = None
        commit_text: str | None = None
        if not close_only and task.repo_id:
            if not context.mapping or not context.status_summary or not context.status_summary.valid_repo:
                return False, "A valid local Git repository is required to complete this task with commit."
            if not context.status_summary.has_changes:
                return False, "There are no Git changes to commit. Empty commits are blocked by default."
            ok, message = self.git_service.add_all(context.mapping.local_path)
            if not ok:
                return False, message
            commit_ok, commit_feedback, commit_hash = self.git_service.commit(
                context.mapping.local_path,
                commit_message or context.suggested_commit_message or f'feat(task): complete "{task.title}"',
            )
            if not commit_ok:
                return False, commit_feedback
            commit_text = commit_message or context.suggested_commit_message
        elif task.commit_policy == CommitPolicy.REQUIRED:
            return False, "Commit policy is required for this task."

        completed = self.task_repository.update(
            task.id,
            status=TaskStatus.DONE,
            completion_commit_hash=commit_hash,
            completion_commit_message=commit_text,
            completion_timestamp=utc_now_iso(),
        )
        active = self.active_task_repository.get_for_user(user_id)
        if active and active.task_id == task.id:
            self.active_task_repository.clear(user_id)

        self.event_service.emit(
            workspace_id=workspace_id,
            actor_user_id=user_id,
            event_type=EventType.TASK_COMPLETED,
            entity_type=EntityType.TASK,
            entity_id=completed.id,
            payload=completed.to_dict(),
        )
        if close_only:
            return True, "Task marked as done."
        return True, f"Task completed and commit {commit_hash or 'created'} recorded."

    def task_tags(self, task: Task) -> list[str]:
        try:
            return json.loads(task.tags_json)
        except json.JSONDecodeError:
            return []
