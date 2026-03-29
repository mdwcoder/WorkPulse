from __future__ import annotations

import flet as ft

from app.ui.main_window import WorkPulseWindow


def main(page: ft.Page) -> None:
    window = WorkPulseWindow(page)
    window.mount()


if __name__ == "__main__":
    ft.app(target=main, assets_dir="assets")
