from __future__ import annotations

from typing import Any

STATE_MAP = {
    "SessionStart": "starting",
    "UserPromptSubmit": "running",
    "PreToolUse": "running",
    "PostToolUse": "running",
    "PostToolUseFailure": "running",
    "PermissionRequest": "waiting_approval",
    "Stop": "completed",
    "SessionEnd": "idle",
}


def normalize(payload: dict[str, Any]) -> tuple[str, str, str, dict[str, Any]]:
    event = payload.get("hook_event_name")
    session_id = payload.get("session_id")
    cwd = payload.get("cwd", "")
    if not isinstance(event, str):
        raise TypeError("Claude hook has no hook_event_name")
    if event == "Notification":
        notification_type = str(payload.get("notification_type", ""))
        state = (
            "waiting_approval"
            if "permission" in notification_type.lower()
            else "waiting_input"
        )
    elif event in STATE_MAP:
        state = STATE_MAP[event]
    else:
        raise ValueError(f"unsupported Claude hook event: {event}")
    if not isinstance(session_id, str) or not session_id:
        raise ValueError("Claude hook has no session_id")
    if not isinstance(cwd, str):
        raise TypeError("Claude hook cwd must be a string")
    metadata = {
        "hook_event_name": event,
        "notification_type": payload.get("notification_type"),
        "permission_mode": payload.get("permission_mode"),
        "tool_name": payload.get("tool_name"),
        "model": payload.get("model"),
    }
    return state, session_id, cwd, metadata
