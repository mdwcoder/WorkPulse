from __future__ import annotations

import flet as ft

from app.ui.theme import PANEL_RAISED, badge, commit_policy_badge
from core.enums import CommitPolicy
from core.models import TaskCompletionContext


class CompletionDialog:
    def __init__(self, page: ft.Page, context: TaskCompletionContext, on_submit) -> None:
        self.page = page
        self.context = context
        self.on_submit = on_submit

    def open(self) -> None:
        commit_message = ft.TextField(
            label="Commit message",
            value=self.context.suggested_commit_message or "",
            border_radius=14,
            bgcolor=PANEL_RAISED,
        )
        allow_close_only = self.context.task.commit_policy != CommitPolicy.REQUIRED
        summary = self.context.status_summary
        summary_controls = []
        if summary:
            summary_controls.extend(
                [
                    ft.Row([badge(f"Branch {summary.branch or 'unknown'}"), commit_policy_badge(self.context.task.commit_policy)], wrap=True),
                    ft.Text(f"Modified files: {len(summary.modified_files)}", size=13),
                    ft.Text(f"Staged: {len(summary.staged_files)}", size=13),
                    ft.Text(f"Unstaged: {len(summary.unstaged_files)}", size=13),
                    ft.Text("\n".join(summary.modified_files[:10]) or "No modified files", size=12),
                ]
            )
        if self.context.warning:
            summary_controls.insert(0, badge(self.context.warning, fg="#FBBF24", bg="#342A10"))
        if self.context.error:
            summary_controls.insert(0, badge(self.context.error, fg="#F87171", bg="#33191B"))

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Complete Task"),
            content=ft.Container(
                width=560,
                content=ft.Column(
                    [
                        ft.Text(self.context.task.title, size=20, weight=ft.FontWeight.W_700),
                        ft.Text("Review Git state before closing the task.", size=13),
                        ft.Divider(),
                        *summary_controls,
                        ft.Divider(),
                        commit_message,
                    ],
                    tight=True,
                    spacing=12,
                    scroll=ft.ScrollMode.AUTO,
                ),
            ),
            actions=[
                ft.TextButton("Cancel", on_click=lambda _e: self._close(dialog)),
                ft.OutlinedButton(
                    "Close only",
                    disabled=not allow_close_only,
                    on_click=lambda _e: self._submit(dialog, True, commit_message.value),
                ),
                ft.ElevatedButton(
                    "Close + Commit",
                    icon=ft.Icons.DONE_ALL,
                    on_click=lambda _e: self._submit(dialog, False, commit_message.value),
                ),
            ],
        )
        self.page.open(dialog)

    def _close(self, dialog: ft.AlertDialog) -> None:
        self.page.close(dialog)

    def _submit(self, dialog: ft.AlertDialog, close_only: bool, commit_message: str | None) -> None:
        self.on_submit(close_only, commit_message)
        self._close(dialog)
