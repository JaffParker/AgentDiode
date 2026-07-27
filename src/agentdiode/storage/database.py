from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from agentdiode.models import Session
from agentdiode.paths import ensure_private_directory

SCHEMA = """
CREATE TABLE IF NOT EXISTS schema_version(version INTEGER NOT NULL);
INSERT INTO schema_version(version)
SELECT 1 WHERE NOT EXISTS (SELECT 1 FROM schema_version);
CREATE TABLE IF NOT EXISTS sessions(
 session_id TEXT PRIMARY KEY, agent_id TEXT NOT NULL, agent_name TEXT NOT NULL,
 state TEXT NOT NULL, reliability TEXT NOT NULL, project_name TEXT NOT NULL,
 cwd TEXT NOT NULL, started_at TEXT NOT NULL, updated_at TEXT NOT NULL,
 completed_at TEXT, pid INTEGER, parent_pid INTEGER, source TEXT NOT NULL,
 error_message TEXT, metadata_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS session_events(
 id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT NOT NULL,
 event TEXT NOT NULL, timestamp TEXT NOT NULL, payload_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS integration_status(
 agent_id TEXT PRIMARY KEY, status TEXT NOT NULL, reliability TEXT NOT NULL,
 details_json TEXT NOT NULL, updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS application_settings(
 key TEXT PRIMARY KEY, value_json TEXT NOT NULL
);
"""


class Database:
    def __init__(self, path: Path) -> None:
        ensure_private_directory(path.parent)
        self.connection = sqlite3.connect(path)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA journal_mode=WAL")
        self.connection.executescript(SCHEMA)

    def save(self, session: Session, event: str, payload: dict[str, Any]) -> None:
        values = session.to_dict()
        self.connection.execute(
            """INSERT INTO sessions(session_id,agent_id,agent_name,state,reliability,
            project_name,cwd,started_at,updated_at,completed_at,pid,parent_pid,source,
            error_message,metadata_json) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(session_id) DO UPDATE SET state=excluded.state,
            updated_at=excluded.updated_at,completed_at=excluded.completed_at,
            pid=excluded.pid,parent_pid=excluded.parent_pid,error_message=excluded.error_message,
            metadata_json=excluded.metadata_json""",
            (
                values["session_id"], values["agent_id"], values["agent_name"], values["state"],
                values["reliability"], values["project_name"], values["cwd"],
                values["started_at"], values["updated_at"], values["completed_at"], values["pid"],
                values["parent_pid"], values["source"], values["error_message"],
                json.dumps(values["metadata"], ensure_ascii=False),
            ),
        )
        self.connection.execute(
            "INSERT INTO session_events(session_id,event,timestamp,payload_json) VALUES(?,?,?,?)",
            (session.session_id, event, session.updated_at, json.dumps(payload, ensure_ascii=False)),
        )
        self.connection.commit()

    def remove(self, session_id: str) -> None:
        self.connection.execute("DELETE FROM sessions WHERE session_id=?", (session_id,))
        self.connection.commit()

    def load_current(self) -> list[Session]:
        rows = self.connection.execute("SELECT * FROM sessions").fetchall()
        return [
            Session(
                session_id=row["session_id"], agent_id=row["agent_id"],
                agent_name=row["agent_name"], state=row["state"],
                reliability=row["reliability"], project_name=row["project_name"],
                cwd=row["cwd"], started_at=row["started_at"], updated_at=row["updated_at"],
                completed_at=row["completed_at"], pid=row["pid"], parent_pid=row["parent_pid"],
                source=row["source"], error_message=row["error_message"],
                metadata=json.loads(row["metadata_json"]),
            )
            for row in rows
        ]

    def history(self, limit: int = 100) -> list[dict[str, Any]]:
        rows = self.connection.execute(
            "SELECT * FROM sessions ORDER BY updated_at DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(row) for row in rows]

    def prune(self, retention_days: int) -> int:
        cutoff = (datetime.now().astimezone() - timedelta(days=retention_days)).isoformat()
        cursor = self.connection.execute(
            "DELETE FROM sessions WHERE completed_at IS NOT NULL AND completed_at < ?", (cutoff,)
        )
        self.connection.execute(
            "DELETE FROM session_events WHERE session_id NOT IN (SELECT session_id FROM sessions)"
        )
        self.connection.commit()
        return cursor.rowcount
