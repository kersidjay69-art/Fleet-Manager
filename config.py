"""Лёгкие настройки приложения (геометрия окна, «поверх всех»).

Сохраняются в JSON рядом с exe/исходником. Это настройки окна, а не данные
флота — список пилотов по-прежнему живёт только в памяти.
"""
import json
import sys
from pathlib import Path

WINDOW_MIN_WIDTH = 680
WINDOW_MIN_HEIGHT = 600


def app_dir() -> Path:
    """Директория приложения: рядом с exe (PyInstaller) или с исходником."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).parent


CONFIG_PATH = app_dir() / "fleet_config.json"
_cfg: dict = {}


def load() -> None:
    global _cfg
    try:
        _cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except Exception:
        _cfg = {}


def save() -> None:
    try:
        CONFIG_PATH.write_text(
            json.dumps(_cfg, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    except Exception:
        pass


def get(key: str, default=None):
    return _cfg.get(key, default)


def set_value(key: str, value) -> None:
    _cfg[key] = value
    save()


def save_window_geometry(window) -> None:
    geo = window.geometry()
    _cfg["window_x"] = geo.x()
    _cfg["window_y"] = geo.y()
    _cfg["window_width"] = geo.width()
    _cfg["window_height"] = geo.height()
    save()


def restore_window_geometry(window) -> None:
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import QRect

    x = _cfg.get("window_x")
    y = _cfg.get("window_y")
    w = max(_cfg.get("window_width", 820), WINDOW_MIN_WIDTH)
    h = max(_cfg.get("window_height", 760), WINDOW_MIN_HEIGHT)

    if x is not None and y is not None:
        available = QRect()
        for screen in QApplication.screens():
            available = available.united(screen.availableGeometry())
        if available.contains(x + 50, y + 50):
            window.setGeometry(x, y, w, h)
            return

    screen = QApplication.primaryScreen().availableGeometry()
    window.setGeometry(
        screen.x() + (screen.width() - w) // 2,
        screen.y() + (screen.height() - h) // 2,
        w, h,
    )
