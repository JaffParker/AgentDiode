from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from agentdiode.constants import STATE_PRIORITY


def now_iso() -> str:
    return datetime.now(UTC).astimezone().isoformat()


@dataclass(slots=True)
class Session:
    session_id: str
    agent_id: str
    agent_name: str
    state: str
    reliability: str = "partial"
    project_name: str = ""
    cwd: str = ""
    started_at: str = field(default_factory=now_iso)
    updated_at: str = field(default_factory=now_iso)
    completed_at: str | None = None
    pid: int | None = None
    parent_pid: int | None = None
    terminal: str | None = None
    editor: str | None = None
    window_identifier: str | None = None
    summary: str | None = None
    error_message: str | None = None
    source: str = "manual"
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def duration_seconds(self) -> int:
        start = datetime.fromisoformat(self.started_at)
        end = datetime.fromisoformat(self.completed_at) if self.completed_at else datetime.now(start.tzinfo)
        return max(0, int((end - start).total_seconds()))

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["duration_seconds"] = self.duration_seconds
        return data


def project_name(cwd: str) -> str:
    return Path(cwd).name if cwd else ""


def aggregate_state(sessions: list[Session]) -> str:
    if not sessions:
        return "idle"
    return max(sessions, key=lambda item: STATE_PRIORITY[item.state]).state
