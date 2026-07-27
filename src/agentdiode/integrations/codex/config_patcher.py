from __future__ import annotations

import json
import os
import shutil
import stat
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

EVENTS = (
    "SessionStart",
    "UserPromptSubmit",
    "PreToolUse",
    "PostToolUse",
    "PermissionRequest",
    "Stop",
    "SessionEnd",
)
DESCRIPTION = "AgentDiode lifecycle hooks. Managed by agentdiode."


@dataclass(frozen=True)
class PatchResult:
    changed: bool
    backup: Path | None
    path: Path


def hook_entry(command: str) -> dict[str, Any]:
    return {"hooks": [{"type": "command", "command": command, "timeout": 3}]}


def build_hooks(command: str) -> dict[str, Any]:
    return {
        "description": DESCRIPTION,
        "hooks": {event: [hook_entry(command)] for event in EVENTS},
    }


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


def _is_agentdiode_handler(handler: object) -> bool:
    return (
        isinstance(handler, dict)
        and isinstance(handler.get("command"), str)
        and "agentdiode" in handler["command"].lower()
    )


def install(path: Path, command: str) -> PatchResult:
    _validate_target(path)
    current = _read(path)
    updated = json.loads(json.dumps(current))
    hooks = updated.setdefault("hooks", {})
    if not isinstance(hooks, dict):
        raise TypeError("existing hooks value must be an object")
    desired = build_hooks(command)["hooks"]
    changed = False
    for event in EVENTS:
        groups = hooks.setdefault(event, [])
        if not isinstance(groups, list):
            raise TypeError(f"existing hooks.{event} must be an array")
        found = False
        for group in groups:
            handlers = group.get("hooks", []) if isinstance(group, dict) else []
            for handler in handlers:
                if _is_agentdiode_handler(handler):
                    found = True
                    if handler != desired[event][0]["hooks"][0]:
                        handler.clear()
                        handler.update(desired[event][0]["hooks"][0])
                        changed = True
        if not found:
            groups.append(desired[event][0])
            changed = True
    if not changed:
        return PatchResult(False, None, path)
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    backup = None
    if path.exists():
        stamp = datetime.now().astimezone().strftime("%Y%m%d-%H%M%S")
        backup = path.with_name(f"{path.name}.agentdiode-backup-{stamp}")
        shutil.copy2(path, backup, follow_symlinks=False)
    temporary = path.with_name(f".{path.name}.agentdiode-{os.getpid()}.tmp")
    temporary.write_text(json.dumps(updated, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.chmod(temporary, 0o600)
    json.loads(temporary.read_text(encoding="utf-8"))
    temporary.replace(path)
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
        kept = []
        for group in groups:
            if not isinstance(group, dict):
                kept.append(group)
                continue
            handlers = group.get("hooks")
            if not isinstance(handlers, list):
                kept.append(group)
                continue
            clean_handlers = [item for item in handlers if not _is_agentdiode_handler(item)]
            if len(clean_handlers) != len(handlers):
                changed = True
            if clean_handlers:
                clean_group = dict(group)
                clean_group["hooks"] = clean_handlers
                kept.append(clean_group)
        if kept:
            hooks[event] = kept
        else:
            hooks.pop(event)
    if not changed:
        return PatchResult(False, None, path)
    backup = path.with_name(
        f"{path.name}.agentdiode-backup-{datetime.now().astimezone():%Y%m%d-%H%M%S}"
    )
    shutil.copy2(path, backup, follow_symlinks=False)
    path.write_text(json.dumps(updated, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.chmod(path, 0o600)
    return PatchResult(True, backup, path)
