from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

EXPORT_FIELDS = (
    "session_id",
    "agent_id",
    "agent_name",
    "state",
    "reliability",
    "project_name",
    "cwd",
    "started_at",
    "updated_at",
    "completed_at",
    "source",
    "error_message",
)


def export_json(rows: list[dict[str, Any]], target: Path) -> None:
    target.write_text(json.dumps(rows, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def export_csv(rows: list[dict[str, Any]], target: Path) -> None:
    with target.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=EXPORT_FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
