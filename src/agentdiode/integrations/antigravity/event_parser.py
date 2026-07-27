from __future__ import annotations

from typing import Any

STATE_MAP = {
    "PreInvocation": "running",
    "PreToolUse": "running",
    "PostToolUse": "running",
    "PostInvocation": "running",
    "Stop": "completed",
}


def normalize(
    event: str, payload: dict[str, Any]
) -> tuple[str, str, str, dict[str, Any]]:
    if event not in STATE_MAP:
        raise ValueError(f"unsupported Antigravity hook event: {event}")
    state = STATE_MAP[event]
    if payload.get("error"):
        state = "error"
    session_id = payload.get("conversationId")
    if not isinstance(session_id, str) or not session_id:
        raise ValueError("Antigravity hook has no conversationId")
    workspace_paths = payload.get("workspacePaths", [])
    cwd = workspace_paths[0] if isinstance(workspace_paths, list) and workspace_paths else ""
    if not isinstance(cwd, str):
        cwd = ""
    tool_call = payload.get("toolCall")
    tool_name = tool_call.get("name") if isinstance(tool_call, dict) else None
    metadata = {
        "hook_event_name": event,
        "tool_name": tool_name,
        "termination_reason": payload.get("terminationReason"),
    }
    return state, session_id, cwd, metadata
