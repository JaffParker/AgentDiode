from __future__ import annotations

import os
from pathlib import Path


def runtime_dir() -> Path:
    base = Path(os.environ.get("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}"))
    return base / "agentdiode"


def socket_path() -> Path:
    override = os.environ.get("AGENTDIODE_SOCKET")
    return Path(override) if override else runtime_dir() / "agentdiode.sock"


def state_dir() -> Path:
    base = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local/state"))
    return base / "agentdiode"


def database_path() -> Path:
    override = os.environ.get("AGENTDIODE_DATABASE")
    return Path(override) if override else state_dir() / "history.sqlite3"


def ensure_private_directory(path: Path) -> None:
    path.mkdir(mode=0o700, parents=True, exist_ok=True)
    path.chmod(0o700)
