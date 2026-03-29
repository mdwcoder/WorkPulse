from __future__ import annotations


class SyncController:
    def __init__(self, app: "AppController") -> None:
        self.app = app
        self.last_result = None

    def manual_sync(self):
        workspace = self.app.current_workspace
        user = self.app.current_user
        if not workspace:
            raise ValueError("Create or select a workspace first.")
        self.last_result = self.app.sync_service.full_sync(workspace, user)
        if self.last_result.ok:
            self.app.reload_settings()
        return self.last_result

    def init_repo(self):
        workspace = self.app.current_workspace
        if not workspace:
            raise ValueError("Create or select a workspace first.")
        self.last_result = self.app.sync_service.init_sync_repo(workspace)
        return self.last_result

    def pull_only(self):
        workspace = self.app.current_workspace
        if not workspace:
            raise ValueError("Create or select a workspace first.")
        self.last_result = self.app.sync_service.pull_only(workspace)
        return self.last_result

    def push_only(self):
        workspace = self.app.current_workspace
        if not workspace:
            raise ValueError("Create or select a workspace first.")
        self.last_result = self.app.sync_service.push_only(workspace)
        if self.last_result.ok:
            self.app.reload_settings()
        return self.last_result
