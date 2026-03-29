from __future__ import annotations

import logging
from pathlib import Path

from core.utils.platform_utils import get_log_dir


def configure_logging() -> None:
    log_dir = get_log_dir()
    log_dir.mkdir(parents=True, exist_ok=True)
    root = logging.getLogger()
    if root.handlers:
        return
    root.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = logging.FileHandler(log_dir / "workpulse.log", encoding="utf-8")
    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)

    sync_handler = logging.FileHandler(log_dir / "sync.log", encoding="utf-8")
    sync_handler.setFormatter(formatter)
    sync_handler.setLevel(logging.INFO)
    sync_handler.addFilter(lambda record: record.name.startswith("workpulse.sync"))
    root.addHandler(sync_handler)


def get_logger(name: str) -> logging.Logger:
    configure_logging()
    return logging.getLogger(name)
