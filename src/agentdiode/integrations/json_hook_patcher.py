from __future__ import annotations

import json
import os
import shutil
import stat
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class PatchResult:
    changed: bool
    backup: Path | None
    path: Path


def _validate_target(path: Path) -> None:
    if path.is_symlink():
        raise ValueError(f"refusing to modify symlink: {path}")
    if path.exists() and not stat.S_ISREG(path.stat().st_mode):
        raise ValueError(f"not a regular file: {path}")


def _read(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise TypeError(f"{path} must contain a JSON object")
    return data


def _agentdiode_handler(value: object) -> bool:
    return (
        isinstance(value, dict)
        and value.get("type") == "command"
        and (
            str(value.get("name", "")).startswith("agentdiode-")
            or "agentdiode" in str(value.get("command", "")).lower()
        )
    )


def _backup(path: Path) -> Path:
    stamp = datetime.now().astimezone().strftime("%Y%m%d-%H%M%S-%f")
    target = path.with_name(f"{path.name}.agentdiode-backup-{stamp}")
    shutil.copy2(path, target, follow_symlinks=False)
    return target


def _write(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.agentdiode-{os.getpid()}.tmp")
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.chmod(temporary, 0o600)
    json.loads(temporary.read_text(encoding="utf-8"))
    temporary.replace(path)


def install(
    path: Path,
    command: str,
    events: tuple[str, ...],
    integration: str,
) -> PatchResult:
    _validate_target(path)
    current = _read(path)
    updated = json.loads(json.dumps(current))
    hooks = updated.setdefault("hooks", {})
    if not isinstance(hooks, dict):
        raise TypeError("existing hooks value must be an object")
    changed = False
    desired_handler = {
        "name": f"agentdiode-{integration}",
        "type": "command",
        "command": command,
        "timeout": 3,
    }
    for event in events:
        groups = hooks.setdefault(event, [])
        if not isinstance(groups, list):
            raise TypeError(f"existing hooks.{event} must be an array")
        found = False
        for group in groups:
            handlers = group.get("hooks", []) if isinstance(group, dict) else []
            if not isinstance(handlers, list):
                continue
            for handler in handlers:
                if _agentdiode_handler(handler):
                    found = True
                    if handler != desired_handler:
                        handler.clear()
                        handler.update(desired_handler)
                        changed = True
        if not found:
            groups.append({"hooks": [dict(desired_handler)]})
            changed = True
    if not changed:
        return PatchResult(False, None, path)
    backup = _backup(path) if path.exists() else None
    _write(path, updated)
    return PatchResult(True, backup, path)

def remove(path: Path) -> PatchResult:
    _validate_target(path)
    current = _read(path)
    updated = json.loads(json.dumps(current))
    hooks = updated.get("hooks")
    if not isinstance(hooks, dict):
        return PatchResult(False, None, path)
    changed = False
    for event in list(hooks):
        groups = hooks[event]
        if not isinstance(groups, list):
            continue
        clean_groups = []
        for group in groups:
            if not isinstance(group, dict) or not isinstance(group.get("hooks"), list):
                clean_groups.append(group)
                continue
            handlers = group["hooks"]
            clean_handlers = [handler for handler in handlers if not _agentdiode_handler(handler)]
            if len(clean_handlers) != len(handlers):
                changed = True
            if clean_handlers:
                clean_group = dict(group)
                clean_group["hooks"] = clean_handlers
                clean_groups.append(clean_group)
        if clean_groups:
            hooks[event] = clean_groups
        else:
            hooks.pop(event)
    if not changed:
        return PatchResult(False, None, path)
    backup = _backup(path)
    _write(path, updated)
    return PatchResult(True, backup, path)
