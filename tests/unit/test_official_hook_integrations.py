import json
from pathlib import Path

from agentdiode.integrations.antigravity.event_parser import normalize as normalize_antigravity
from agentdiode.integrations.antigravity.hook_patcher import (
    install as install_antigravity,
)
from agentdiode.integrations.antigravity.hook_patcher import remove as remove_antigravity
from agentdiode.integrations.claude.event_parser import normalize as normalize_claude
from agentdiode.integrations.json_hook_patcher import install, remove


def test_claude_events_and_privacy() -> None:
    state, session, cwd, metadata = normalize_claude(
        {
            "hook_event_name": "PermissionRequest",
            "session_id": "claude-1",
            "cwd": "/work",
            "tool_name": "Bash",
            "tool_input": {"command": "secret"},
            "prompt": "private",
        }
    )
    assert (state, session, cwd) == ("waiting_approval", "claude-1", "/work")
    assert "tool_input" not in metadata
    assert "prompt" not in metadata


def test_antigravity_events_and_privacy() -> None:
    state, session, cwd, metadata = normalize_antigravity(
        "PreToolUse",
        {
            "conversationId": "agy-1",
            "workspacePaths": ["/work"],
            "toolCall": {"name": "run_command", "args": {"secret": "private"}},
            "prompt": "private",
        }
    )
    assert state == "running"
    assert session == "agy-1"
    assert cwd == "/work"
    assert metadata["tool_name"] == "run_command"
    assert "prompt" not in metadata


def test_antigravity_named_hook_schema(tmp_path: Path) -> None:
    path = tmp_path / "hooks.json"
    path.write_text(json.dumps({"user-hook": {"enabled": False}}), encoding="utf-8")
    first = install_antigravity(path, "/opt/agentdiode/antigravity-hook")
    second = install_antigravity(path, "/opt/agentdiode/antigravity-hook")
    assert first.changed is True
    assert second.changed is False
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["user-hook"] == {"enabled": False}
    assert data["agentdiode"]["PreToolUse"][0]["matcher"] == "*"
    assert data["agentdiode"]["PreInvocation"][0]["command"].endswith(" PreInvocation")
    assert remove_antigravity(path).changed is True
    assert json.loads(path.read_text(encoding="utf-8")) == {
        "user-hook": {"enabled": False}
    }


def test_antigravity_migrates_old_agentdiode_layout(tmp_path: Path) -> None:
    path = tmp_path / "hooks.json"
    path.write_text(
        json.dumps(
            {
                "hooks": {
                    "BeforeAgent": [
                        {
                            "hooks": [
                                {
                                    "name": "agentdiode-antigravity",
                                    "type": "command",
                                    "command": "/old/antigravity-hook",
                                }
                            ]
                        }
                    ]
                }
            }
        ),
        encoding="utf-8",
    )
    install_antigravity(path, "/new/antigravity-hook")
    data = json.loads(path.read_text(encoding="utf-8"))
    assert "hooks" not in data
    assert "agentdiode" in data


def test_json_hook_patcher_preserves_settings(tmp_path: Path) -> None:
    path = tmp_path / "settings.json"
    path.write_text(
        json.dumps(
            {
                "theme": "dark",
                "hooks": {
                    "Stop": [{"hooks": [{"type": "command", "command": "/tmp/user-hook"}]}]
                },
            }
        ),
        encoding="utf-8",
    )
    events = ("SessionStart", "Stop")
    first = install(path, "/opt/agentdiode/claude-hook", events, "claude")
    second = install(path, "/opt/agentdiode/claude-hook", events, "claude")
    assert first.changed is True
    assert first.backup is not None
    assert second.changed is False
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["theme"] == "dark"
    assert data["hooks"]["Stop"][0]["hooks"][0]["command"] == "/tmp/user-hook"
    result = remove(path)
    assert result.changed is True
    clean = json.loads(path.read_text(encoding="utf-8"))
    assert clean["theme"] == "dark"
    assert clean["hooks"]["Stop"] == [
        {"hooks": [{"type": "command", "command": "/tmp/user-hook"}]}
    ]
