import csv
import json
from pathlib import Path

from agentdiode.storage.exports import export_csv, export_json


def test_exports(tmp_path: Path) -> None:
    rows = [{"session_id": "one", "agent_id": "codex", "state": "completed"}]
    json_path = tmp_path / "history.json"
    csv_path = tmp_path / "history.csv"
    export_json(rows, json_path)
    export_csv(rows, csv_path)
    assert json.loads(json_path.read_text())[0]["session_id"] == "one"
    with csv_path.open(newline="") as handle:
        assert next(csv.DictReader(handle))["agent_id"] == "codex"
