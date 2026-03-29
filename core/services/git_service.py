from __future__ import annotations

import shlex
import subprocess
from pathlib import Path

from core.models import GitStatusSummary
from core.utils.logger import get_logger
from core.utils.path_utils import expand_path

LOGGER = get_logger("workpulse.git")


class GitService:
    def _run(self, args: list[str], cwd: str | Path) -> subprocess.CompletedProcess[str]:
        resolved = expand_path(str(cwd))
        if resolved is None:
            raise ValueError("Invalid git path.")
        LOGGER.info("git %s (cwd=%s)", " ".join(shlex.quote(part) for part in args), resolved)
        return subprocess.run(
            ["git", *args],
            cwd=str(resolved),
            capture_output=True,
            text=True,
            check=False,
        )

    def repo_exists(self, repo_path: str | Path | None) -> bool:
        path = expand_path(str(repo_path)) if repo_path else None
        return bool(path and path.exists() and (path / ".git").exists())

    def get_status_summary(self, repo_path: str | Path | None) -> GitStatusSummary:
        if not repo_path:
            return GitStatusSummary(False, None, [], [], [], False, "Local path is not configured.")
        if not self.repo_exists(repo_path):
            return GitStatusSummary(False, None, [], [], [], False, "Configured path is not a valid Git repository.")

        branch_result = self._run(["branch", "--show-current"], repo_path)
        if branch_result.returncode != 0:
            return GitStatusSummary(False, None, [], [], [], False, branch_result.stderr.strip() or "Unable to read branch.")

        status_result = self._run(["status", "--short"], repo_path)
        if status_result.returncode != 0:
            return GitStatusSummary(False, branch_result.stdout.strip(), [], [], [], False, status_result.stderr.strip())

        staged: list[str] = []
        unstaged: list[str] = []
        modified: list[str] = []
        for line in status_result.stdout.splitlines():
            if len(line) < 4:
                continue
            index_state = line[0]
            worktree_state = line[1]
            file_name = line[3:].strip()
            modified.append(file_name)
            if index_state != " ":
                staged.append(file_name)
            if worktree_state != " ":
                unstaged.append(file_name)

        return GitStatusSummary(
            valid_repo=True,
            branch=branch_result.stdout.strip() or None,
            modified_files=modified,
            staged_files=staged,
            unstaged_files=unstaged,
            has_changes=bool(modified),
        )

    def current_branch(self, repo_path: str | Path) -> str | None:
        result = self._run(["branch", "--show-current"], repo_path)
        return result.stdout.strip() if result.returncode == 0 else None

    def sync_pull_rebase(self, repo_path: str | Path, branch: str) -> tuple[bool, str]:
        fetch = self._run(["fetch", "origin", branch], repo_path)
        if fetch.returncode != 0:
            return False, fetch.stderr.strip() or "git fetch failed"
        pull = self._run(["pull", "--rebase", "origin", branch], repo_path)
        if pull.returncode != 0:
            return False, pull.stderr.strip() or "git pull --rebase failed"
        return True, pull.stdout.strip() or "Pull completed"

    def init_repo(self, repo_path: str | Path, branch: str) -> tuple[bool, str]:
        path = expand_path(str(repo_path))
        if path is None:
            return False, "Invalid sync path."
        path.mkdir(parents=True, exist_ok=True)
        if (path / ".git").exists():
            return True, "Repository already initialized."
        result = self._run(["init", "-b", branch], path)
        if result.returncode != 0:
            fallback = self._run(["init"], path)
            if fallback.returncode != 0:
                return False, fallback.stderr.strip() or "git init failed"
            checkout = self._run(["checkout", "-b", branch], path)
            if checkout.returncode != 0:
                return False, checkout.stderr.strip() or "Unable to create sync branch"
            return True, "Repository initialized."
        return True, result.stdout.strip() or "Repository initialized."

    def set_remote_origin(self, repo_path: str | Path, remote_url: str) -> tuple[bool, str]:
        remotes = self._run(["remote"], repo_path)
        if remotes.returncode != 0:
            return False, remotes.stderr.strip() or "Unable to inspect remotes"
        existing = {line.strip() for line in remotes.stdout.splitlines() if line.strip()}
        if "origin" in existing:
            result = self._run(["remote", "set-url", "origin", remote_url], repo_path)
        else:
            result = self._run(["remote", "add", "origin", remote_url], repo_path)
        return (result.returncode == 0, result.stderr.strip() or result.stdout.strip() or "Remote updated")

    def ensure_branch(self, repo_path: str | Path, branch: str) -> tuple[bool, str]:
        result = self._run(["checkout", branch], repo_path)
        if result.returncode == 0:
            return True, result.stdout.strip() or f"Checked out {branch}"
        create = self._run(["checkout", "-b", branch], repo_path)
        return (create.returncode == 0, create.stderr.strip() or create.stdout.strip() or f"Checked out {branch}")

    def add_all(self, repo_path: str | Path) -> tuple[bool, str]:
        result = self._run(["add", "."], repo_path)
        return (result.returncode == 0, result.stderr.strip() or result.stdout.strip() or "git add completed")

    def has_index_changes(self, repo_path: str | Path) -> bool:
        result = self._run(["diff", "--cached", "--quiet"], repo_path)
        return result.returncode == 1

    def has_worktree_changes(self, repo_path: str | Path) -> bool:
        result = self._run(["diff", "--quiet"], repo_path)
        return result.returncode == 1

    def commit(self, repo_path: str | Path, message: str) -> tuple[bool, str, str | None]:
        commit_result = self._run(["commit", "-m", message], repo_path)
        if commit_result.returncode != 0:
            return False, commit_result.stderr.strip() or "git commit failed", None
        rev = self._run(["rev-parse", "HEAD"], repo_path)
        commit_hash = rev.stdout.strip() if rev.returncode == 0 else None
        return True, commit_result.stdout.strip() or "Commit completed", commit_hash

    def push(self, repo_path: str | Path, branch: str) -> tuple[bool, str]:
        result = self._run(["push", "origin", branch], repo_path)
        return (result.returncode == 0, result.stderr.strip() or result.stdout.strip() or "git push completed")
