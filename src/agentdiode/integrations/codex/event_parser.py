from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class NormalizedCodexEvent:
    state: str
    session_id: str
    cwd: str
    metadata: dict[str, Any]


STATE_MAP = {
    "SessionStart": "starting",
    "UserPromptSubmit": "running",
    "PreToolUse": "running",
    "PostToolUse": "running",
    "PermissionRequest": "waiting_approval",
    "Stop": "completed",
    "SessionEnd": "idle",
}


def normalize(payload: dict[str, Any]) -> NormalizedCodexEvent:
    event_name = payload.get("hook_event_name")
    session_id = payload.get("session_id")
    cwd = payload.get("cwd", "")
    if event_name not in STATE_MAP:
        raise ValueError(f"unsupported Codex hook event: {event_name!r}")
    if not isinstance(session_id, str) or not session_id:
        raise ValueError("Codex hook has no session_id")
    if not isinstance(cwd, str):
        raise TypeError("Codex hook cwd must be a string")
    safe_metadata = {
        "hook_event_name": event_name,
        "turn_id": payload.get("turn_id"),
        "model": payload.get("model"),
        "permission_mode": payload.get("permission_mode"),
    }
    return NormalizedCodexEvent(STATE_MAP[event_name], session_id, cwd, safe_metadata)
