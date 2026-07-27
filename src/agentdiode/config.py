from __future__ import annotations

import os
import re
import tomllib
from dataclasses import dataclass, field, fields
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class GeneralConfig:
    store_history: bool = True
    history_retention_days: int = 30
    completed_display_seconds: int = 8
    stale_timeout_seconds: int = 300
    heartbeat_interval_seconds: int = 30


@dataclass(frozen=True)
class NotificationConfig:
    enabled: bool = True
    on_completed: bool = True
    on_error: bool = True
    on_waiting_input: bool = True
    on_waiting_approval: bool = True


@dataclass(frozen=True)
class TrayConfig:
    blink_running: bool = True
    blink_waiting: bool = True
    animation_interval_ms: int = 650


@dataclass(frozen=True)
class PrivacyConfig:
    store_prompt_content: bool = False
    store_agent_messages: bool = False
    store_last_message_summary: bool = False
    maximum_summary_length: int = 240


@dataclass(frozen=True)
class Config:
    general: GeneralConfig = field(default_factory=GeneralConfig)
    notifications: NotificationConfig = field(default_factory=NotificationConfig)
    tray: TrayConfig = field(default_factory=TrayConfig)
    privacy: PrivacyConfig = field(default_factory=PrivacyConfig)


def config_path() -> Path:
    base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return base / "agentdiode/config.toml"


def _section(data: dict[str, Any], name: str) -> dict[str, Any]:
    value = data.get(name, {})
    if not isinstance(value, dict):
        raise TypeError(f"[{name}] must be a TOML table")
    return value


def _known(data: dict[str, Any], allowed: set[str], section: str) -> None:
    unknown = set(data) - allowed
    if unknown:
        raise ValueError(f"unknown setting in [{section}]: {min(unknown)}")


def load(path: Path | None = None) -> Config:
    target = path or config_path()
    if not target.exists():
        return Config()
    with target.open("rb") as handle:
        raw = tomllib.load(handle)
    general = _section(raw, "general")
    notifications = _section(raw, "notifications")
    tray = _section(raw, "tray")
    privacy = _section(raw, "privacy")
    _known(general, set(GeneralConfig.__dataclass_fields__), "general")
    _known(notifications, set(NotificationConfig.__dataclass_fields__), "notifications")
    _known(tray, set(TrayConfig.__dataclass_fields__), "tray")
    _known(privacy, set(PrivacyConfig.__dataclass_fields__), "privacy")
    config = Config(
        general=GeneralConfig(**general),
        notifications=NotificationConfig(**notifications),
        tray=TrayConfig(**tray),
        privacy=PrivacyConfig(**privacy),
    )
    validate(config)
    return config


def validate(config: Config) -> None:
    numeric = {
        "history_retention_days": (config.general.history_retention_days, 1, 3650),
        "completed_display_seconds": (config.general.completed_display_seconds, 0, 3600),
        "stale_timeout_seconds": (config.general.stale_timeout_seconds, 10, 86400),
        "heartbeat_interval_seconds": (config.general.heartbeat_interval_seconds, 5, 3600),
        "animation_interval_ms": (config.tray.animation_interval_ms, 100, 10000),
        "maximum_summary_length": (config.privacy.maximum_summary_length, 0, 4096),
    }
    for name, (value, minimum, maximum) in numeric.items():
        if isinstance(value, bool) or not isinstance(value, int):
            raise TypeError(f"{name} must be an integer")
        if not minimum <= value <= maximum:
            raise ValueError(f"{name} must be between {minimum} and {maximum}")
    for section in (config.general, config.notifications, config.tray, config.privacy):
        for item in fields(section):
            name = item.name
            value = getattr(section, name)
            if name not in numeric and not isinstance(value, bool):
                raise TypeError(f"{name} must be true or false")


def set_value(path: Path, dotted_key: str, value_text: str) -> None:
    match = re.fullmatch(r"(general|notifications|tray|privacy)\.([a-z_]+)", dotted_key)
    if not match:
        raise ValueError("setting must be SECTION.KEY")
    section, key = match.groups()
    allowed = {
        "general": set(GeneralConfig.__dataclass_fields__),
        "notifications": set(NotificationConfig.__dataclass_fields__),
        "tray": set(TrayConfig.__dataclass_fields__),
        "privacy": set(PrivacyConfig.__dataclass_fields__),
    }
    if key not in allowed[section]:
        raise ValueError(f"unknown setting: {dotted_key}")
    tomllib.loads(f"value = {value_text}\n")
    original = path.read_text(encoding="utf-8") if path.exists() else ""
    lines = original.splitlines()
    section_start = None
    section_end = len(lines)
    for index, line in enumerate(lines):
        if line.strip() == f"[{section}]":
            section_start = index
            continue
        if section_start is not None and index > section_start and line.lstrip().startswith("["):
            section_end = index
            break
    replacement = f"{key} = {value_text}"
    if section_start is None:
        if lines and lines[-1].strip():
            lines.append("")
        lines.extend([f"[{section}]", replacement])
    else:
        setting_pattern = re.compile(rf"^\s*{re.escape(key)}\s*=")
        for index in range(section_start + 1, section_end):
            if setting_pattern.match(lines[index]):
                lines[index] = replacement
                break
        else:
            lines.insert(section_end, replacement)
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    temporary = path.with_suffix(".toml.tmp")
    temporary.write_text("\n".join(lines) + "\n", encoding="utf-8")
    try:
        loaded = load(temporary)
        validate(loaded)
    except (TypeError, ValueError, tomllib.TOMLDecodeError):
        temporary.unlink(missing_ok=True)
        raise
    os.chmod(temporary, 0o600)
    temporary.replace(path)
