from pathlib import Path

import pytest

from agentdiode.config import load, set_value


def test_config_set_preserves_comments_and_other_sections(tmp_path: Path) -> None:
    path = tmp_path / "config.toml"
    path.write_text(
        "# user comment\n[general]\nstale_timeout_seconds = 300\n\n[tray]\nblink_running = true\n",
        encoding="utf-8",
    )
    set_value(path, "general.stale_timeout_seconds", "600")
    text = path.read_text(encoding="utf-8")
    assert "# user comment" in text
    assert "[tray]\nblink_running = true" in text
    assert load(path).general.stale_timeout_seconds == 600


def test_invalid_config_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "config.toml"
    path.write_text("[general]\nstale_timeout_seconds = 2\n", encoding="utf-8")
    with pytest.raises(ValueError):
        load(path)


def test_invalid_update_does_not_replace_config(tmp_path: Path) -> None:
    path = tmp_path / "config.toml"
    path.write_text("[general]\nstale_timeout_seconds = 300\n", encoding="utf-8")
    with pytest.raises(ValueError):
        set_value(path, "general.stale_timeout_seconds", "2")
    assert "300" in path.read_text(encoding="utf-8")
