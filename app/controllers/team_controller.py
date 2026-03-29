from __future__ import annotations

from dataclasses import dataclass

from core.enums import PresenceStatus
from core.models import TeamMemberSnapshot
from core.utils.time_utils import format_relative, parse_iso, utc_now


@dataclass(slots=True)
class TeamSummary:
    active_members: int
    idle_members: int
    offline_members: int
    completed_with_commit_today: int
    recent_highlights: list[str]


class TeamController:
    def __init__(self, app: "AppController") -> None:
        self.app = app

    def snapshot(self) -> list[TeamMemberSnapshot]:
        workspace = self.app.current_workspace
        if not workspace:
            return []
        users = self.app.workspace_service.list_users(workspace.id)
        tasks = {task.id: task for task in self.app.task_service.list_tasks(workspace.id)}
        snapshots: list[TeamMemberSnapshot] = []
        events = self.app.event_service.list_workspace_events(workspace.id)
        last_event_by_user: dict[str, str] = {}
        for event in events:
            if event.actor_user_id:
                last_event_by_user[event.actor_user_id] = event.created_at

        for user in users:
            active_task = self.app.task_service.get_active_task(user.id)
            last_punch = self.app.punch_service.last_punch(user.id)
            last_completed = self.app.task_service.task_repository.list_completed_by_user(workspace.id, user.id)
            work_session = self.app.punch_service.current_work_session(user.id)
            pomodoro = self.app.pomodoro_service.current(user.id)
            last_activity = last_event_by_user.get(user.id)
            presence = PresenceStatus.OFFLINE
            parsed = parse_iso(last_activity)
            if work_session or pomodoro:
                presence = PresenceStatus.ACTIVE
            elif parsed and (utc_now() - parsed).total_seconds() < 4 * 3600:
                presence = PresenceStatus.IDLE

            snapshots.append(
                TeamMemberSnapshot(
                    user=user,
                    presence=presence,
                    last_activity_at=last_activity,
                    active_task=active_task,
                    last_punch=last_punch,
                    last_completed_task=last_completed[0] if last_completed else None,
                )
            )
        return snapshots

    def summary(self) -> TeamSummary:
        workspace = self.app.current_workspace
        if not workspace:
            return TeamSummary(0, 0, 0, 0, [])

        snapshots = self.snapshot()
        today = utc_now().date()
        completed_with_commit_today = 0
        highlights: list[tuple[str | None, str]] = []

        for task in self.app.task_service.list_tasks(workspace.id):
            completed_at = parse_iso(task.completion_timestamp)
            if completed_at and completed_at.date() == today and task.completion_commit_hash:
                completed_with_commit_today += 1

        for snapshot in snapshots:
            if snapshot.active_task:
                highlights.append((snapshot.last_activity_at, f"{snapshot.user.display_name} active on {snapshot.active_task.title}"))
            elif snapshot.last_completed_task:
                relative = format_relative(snapshot.last_completed_task.completion_timestamp)
                highlights.append((snapshot.last_completed_task.completion_timestamp, f"{snapshot.user.display_name} completed {snapshot.last_completed_task.title} ({relative})"))
            elif snapshot.last_punch:
                relative = format_relative(snapshot.last_punch.created_at)
                highlights.append((snapshot.last_punch.created_at, f"{snapshot.user.display_name} {snapshot.last_punch.punch_type.value.replace('_', ' ')} ({relative})"))

        highlights.sort(key=lambda item: item[0] or "", reverse=True)
        return TeamSummary(
            active_members=sum(1 for item in snapshots if item.presence == PresenceStatus.ACTIVE),
            idle_members=sum(1 for item in snapshots if item.presence == PresenceStatus.IDLE),
            offline_members=sum(1 for item in snapshots if item.presence == PresenceStatus.OFFLINE),
            completed_with_commit_today=completed_with_commit_today,
            recent_highlights=[text for _ts, text in highlights[:5]],
        )
