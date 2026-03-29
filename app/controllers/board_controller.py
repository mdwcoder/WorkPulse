from __future__ import annotations

from dataclasses import dataclass

from core.enums import CommitPolicy, TaskStatus
from core.models import Task


@dataclass(slots=True)
class BoardFilters:
    assigned_to_me: bool = False
    repo_id: str | None = None
    status: str | None = None
    commit_policy: str | None = None
    active_only: bool = False


class BoardController:
    def __init__(self, app: "AppController") -> None:
        self.app = app
        self.filters = BoardFilters()
        self.selected_task_id: str | None = None

    def set_selected_task(self, task_id: str | None) -> None:
        self.selected_task_id = task_id

    def selected_task(self) -> Task | None:
        return self.app.task_service.get_task(self.selected_task_id)

    def tasks(self) -> list[Task]:
        workspace = self.app.current_workspace
        user = self.app.current_user
        if not workspace:
            return []
        tasks = self.app.task_service.list_tasks(workspace.id)
        current_active = self.app.task_service.get_active_task(user.id) if user else None
        active_task_id = current_active.id if current_active else None
        filtered: list[Task] = []
        for task in tasks:
            if self.filters.assigned_to_me and (not user or task.assignee_user_id != user.id):
                continue
            if self.filters.repo_id and task.repo_id != self.filters.repo_id:
                continue
            if self.filters.status and task.status.value != self.filters.status:
                continue
            if self.filters.commit_policy and task.commit_policy.value != self.filters.commit_policy:
                continue
            if self.filters.active_only and task.id != active_task_id:
                continue
            filtered.append(task)
        return filtered

    def column_tasks(self, status: TaskStatus) -> list[Task]:
        return [task for task in self.tasks() if task.status == status]

    def move(self, task_id: str, status: TaskStatus) -> None:
        user = self.app.current_user
        self.app.task_service.move_task(task_id, status, actor_user_id=user.id if user else None)

    def set_active(self, task_id: str) -> None:
        workspace = self.app.current_workspace
        user = self.app.current_user
        if not workspace or not user:
            raise ValueError("Workspace or current user is missing.")
        self.app.task_service.set_active_task(workspace.id, user.id, task_id)

    def clear_active(self) -> None:
        workspace = self.app.current_workspace
        user = self.app.current_user
        if workspace and user:
            self.app.task_service.clear_active_task(workspace.id, user.id)
