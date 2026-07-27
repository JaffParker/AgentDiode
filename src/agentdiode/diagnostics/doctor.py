from __future__ import annotations

import importlib.util
import os
import shutil
import sqlite3
import sys
from dataclasses import dataclass

from agentdiode.paths import database_path, socket_path, state_dir


@dataclass(frozen=True)
class Check:
    name: str
    ok: bool
    detail: str


def run_checks() -> list[Check]:
    sock = socket_path()
    database = database_path()
    checks = [
        Check("Python", sys.version_info >= (3, 11), sys.version.split()[0]),
        Check(
            "PySide6",
            importlib.util.find_spec("PySide6") is not None,
            "available" if importlib.util.find_spec("PySide6") else "not installed",
        ),
        Check("Session", bool(os.environ.get("KDE_FULL_SESSION")), "KDE Plasma" if os.environ.get("KDE_FULL_SESSION") else "not KDE"),
        Check("Display", bool(os.environ.get("WAYLAND_DISPLAY") or os.environ.get("DISPLAY")), os.environ.get("XDG_SESSION_TYPE", "unknown")),
        Check("Socket", sock.exists(), str(sock)),
        Check("Notifications", shutil.which("notify-send") is not None, shutil.which("notify-send") or "unavailable"),
        Check("Codex", shutil.which("codex") is not None, shutil.which("codex") or "not installed"),
        Check("Claude", shutil.which("claude") is not None, shutil.which("claude") or "not installed"),
        Check(
            "Antigravity",
            shutil.which("agy") is not None,
            shutil.which("agy") or "not installed",
        ),
        Check("VS Code", shutil.which("code") is not None, shutil.which("code") or "not installed"),
        Check("State directory", os.access(state_dir().parent, os.W_OK), str(state_dir())),
    ]
    if database.exists():
        try:
            with sqlite3.connect(database) as connection:
                result = connection.execute("PRAGMA quick_check").fetchone()
            checks.append(Check("Database", result == ("ok",), str(database)))
        except sqlite3.Error as exc:
            checks.append(Check("Database", False, str(exc)))
    else:
        checks.append(Check("Database", True, "not created yet"))
    return checks


def format_checks(checks: list[Check]) -> str:
    return "\n".join(
        f"{'OK' if check.ok else 'WARN':<4} {check.name:<18} {check.detail}" for check in checks
    )
