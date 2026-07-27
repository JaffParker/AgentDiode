from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from agentdiode.constants import EVENTS, MAX_METADATA_BYTES, PROTOCOL_VERSION
from agentdiode.models import now_iso

IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
RELIABILITIES = {"exact", "partial", "heuristic", "unavailable"}


class ProtocolError(ValueError):
    pass


@dataclass(slots=True)
class Event:
    event: str
    agent_id: str
    session_id: str
    timestamp: str = field(default_factory=now_iso)
    protocol_version: int = PROTOCOL_VERSION
    cwd: str = ""
    agent_name: str | None = None
    reliability: str = "partial"
    pid: int | None = None
    parent_pid: int | None = None
    source: str = "manual"
    summary: str | None = None
    error_message: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Event:
        allowed = set(cls.__dataclass_fields__)
        event = cls(**{key: value for key, value in data.items() if key in allowed})
        event.validate()
        return event

    def validate(self) -> None:
        if self.protocol_version != PROTOCOL_VERSION:
            raise ProtocolError(f"unsupported protocol version: {self.protocol_version}")
        if self.event not in EVENTS:
            raise ProtocolError(f"unknown event: {self.event}")
        for label, value in (("agent_id", self.agent_id), ("session_id", self.session_id)):
            if not isinstance(value, str) or not IDENTIFIER.fullmatch(value):
                raise ProtocolError(f"invalid {label}")
        if self.reliability not in RELIABILITIES:
            raise ProtocolError("invalid reliability")
        try:
            datetime.fromisoformat(self.timestamp)
        except (TypeError, ValueError) as exc:
            raise ProtocolError("invalid timestamp") from exc
        if self.pid is not None and (not isinstance(self.pid, int) or self.pid <= 0):
            raise ProtocolError("invalid pid")
        if len(self.cwd) > 4096:
            raise ProtocolError("cwd is too long")
        if len(json.dumps(self.metadata, ensure_ascii=False).encode()) > MAX_METADATA_BYTES:
            raise ProtocolError("metadata is too large")
        for text in (self.agent_name, self.summary, self.error_message, self.source):
            if text is not None and (not isinstance(text, str) or len(text) > 4096):
                raise ProtocolError("text field is invalid or too long")

    def to_dict(self) -> dict[str, Any]:
        return {name: getattr(self, name) for name in self.__dataclass_fields__}


def decode_event(line: bytes) -> Event:
    try:
        value = json.loads(line)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProtocolError("invalid JSON") from exc
    if not isinstance(value, dict):
        raise ProtocolError("event must be a JSON object")
    return Event.from_dict(value)
