from __future__ import annotations

import json
from pathlib import Path

from agentdiode.integrations.json_hook_patcher import (
    PatchResult,
    _agentdiode_handler,
    _backup,
    _read,
    _validate_target,
    _write,
)

EVENTS = ("PreToolUse", "PostToolUse", "PreInvocation", "PostInvocation", "Stop")


def _handler(command: str, event: str) -> dict[str, object]:
    return {
        "type": "command",
        "command": f"{command} {event}",
        "timeout": 3,
    }


def _remove_legacy_entries(config: dict[str, object]) -> None:
    """Remove the invalid pre-0.1 Antigravity layout created by AgentDiode."""
    hooks = config.get("hooks")
    if not isinstance(hooks, dict):
        return
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
            clean_handlers = [item for item in handlers if not _agentdiode_handler(item)]
            if clean_handlers:
                clean_group = dict(group)
                clean_group["hooks"] = clean_handlers
                clean_groups.append(clean_group)
        if clean_groups:
            hooks[event] = clean_groups
        else:
            hooks.pop(event)
    if not hooks:
        config.pop("hooks")


def install(path: Path, command: str) -> PatchResult:
    _validate_target(path)
    current = _read(path)
    updated = json.loads(json.dumps(current))
    _remove_legacy_entries(updated)
    desired: dict[str, object] = {"enabled": True}
    for event in EVENTS:
        handler = _handler(command, event)
        desired[event] = (
            [{"matcher": "*", "hooks": [handler]}]
            if event in {"PreToolUse", "PostToolUse"}
            else [handler]
        )
    if updated == current and updated.get("agentdiode") == desired:
        return PatchResult(False, None, path)
    updated["agentdiode"] = desired
    backup = _backup(path) if path.exists() else None
    _write(path, updated)
    return PatchResult(True, backup, path)


def remove(path: Path) -> PatchResult:
    _validate_target(path)
    current = _read(path)
    if "agentdiode" not in current:
        return PatchResult(False, None, path)
    updated = json.loads(json.dumps(current))
    updated.pop("agentdiode")
    backup = _backup(path)
    _write(path, updated)
    return PatchResult(True, backup, path)
