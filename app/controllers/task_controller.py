from __future__ import annotations

from core.enums import CommitPolicy, TaskPriority, TaskStatus


class TaskController:
    def __init__(self, app: "AppController") -> None:
        self.app = app

    def create_task(
        self,
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
    ) -> None:
        workspace = self.app.current_workspace
        user = self.app.current_user
        if not workspace:
            raise ValueError("Create a workspace before creating tasks.")
        self.app.task_service.create_task(
            workspace.id,
            title=title,
            description=description,
            assignee_user_id=assignee_user_id,
            status=status,
            priority=priority,
            tags=tags,
            repo_id=repo_id,
            branch_name=branch_name,
            commit_policy=commit_policy,
            actor_user_id=user.id if user else None,
        )

    def update_task(self, task_id: str, **fields_to_update: object) -> None:
        user = self.app.current_user
        self.app.task_service.update_task(task_id, actor_user_id=user.id if user else None, **fields_to_update)

    def complete_task(self, task_id: str, close_only: bool, commit_message: str | None) -> tuple[bool, str]:
        workspace = self.app.current_workspace
        user = self.app.current_user
        if not workspace or not user:
            return False, "Select a workspace and user first."
        return self.app.task_service.complete_task(
            task_id=task_id,
            workspace_id=workspace.id,
            user_id=user.id,
            close_only=close_only,
            commit_message=commit_message,
        )

    def completion_context(self, task_id: str):
        user = self.app.current_user
        if not user:
            raise ValueError("No current user selected.")
        return self.app.task_service.build_completion_context(task_id, user.id)
