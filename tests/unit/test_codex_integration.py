import json
from pathlib import Path

from agentdiode.integrations.codex.config_patcher import EVENTS, install, remove
from agentdiode.integrations.codex.event_parser import normalize


def test_codex_event_normalization_is_privacy_safe() -> None:
    event = normalize(
        {
            "hook_event_name": "PermissionRequest",
            "session_id": "abc",
            "cwd": "/work/project",
            "prompt": "must not survive",
            "tool_input": {"secret": "must not survive"},
        }
    )
    assert event.state == "waiting_approval"
    assert "prompt" not in event.metadata
    assert "tool_input" not in event.metadata


def test_hook_install_is_idempotent_and_preserves_user_hooks(tmp_path: Path) -> None:
    path = tmp_path / "hooks.json"
    user = {
        "hooks": {
            "Stop": [
                {"hooks": [{"type": "command", "command": "/home/user/my-hook", "timeout": 2}]}
            ]
        }
    }
    path.write_text(json.dumps(user), encoding="utf-8")
    command = "/home/user/.local/share/agentdiode/integrations/codex-hook"
    first = install(path, command)
    second = install(path, command)
    assert first.changed is True
    assert first.backup is not None
    assert second.changed is False
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["hooks"]["Stop"][0] == user["hooks"]["Stop"][0]
    for event in EVENTS:
        assert len(data["hooks"][event]) >= 1


def test_hook_removal_preserves_user_hooks(tmp_path: Path) -> None:
    path = tmp_path / "hooks.json"
    path.write_text(
        json.dumps(
            {
                "hooks": {
                    "Stop": [
                        {"hooks": [{"type": "command", "command": "/tmp/user-hook"}]},
                        {"hooks": [{"type": "command", "command": "/opt/agentdiode/codex-hook"}]},
                    ]
                }
            }
        ),
        encoding="utf-8",
    )
    result = remove(path)
    assert result.changed is True
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["hooks"]["Stop"] == [
        {"hooks": [{"type": "command", "command": "/tmp/user-hook"}]}
    ]
