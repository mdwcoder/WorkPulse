from __future__ import annotations

from pathlib import Path


def expand_path(path_value: str | None) -> Path | None:
    if not path_value:
        return None
    return Path(path_value).expanduser().resolve()


def is_existing_directory(path_value: str | None) -> bool:
    path = expand_path(path_value)
    return bool(path and path.exists() and path.is_dir())


def is_git_repo_path(path_value: str | None) -> bool:
    path = expand_path(path_value)
    return bool(path and (path / ".git").exists())
