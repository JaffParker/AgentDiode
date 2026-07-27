from __future__ import annotations

from pathlib import Path


def process_start_ticks(pid: int, proc_root: Path = Path("/proc")) -> int | None:
    try:
        content = (proc_root / str(pid) / "stat").read_text(encoding="utf-8")
    except (FileNotFoundError, PermissionError, OSError):
        return None
    closing = content.rfind(")")
    if closing < 0:
        return None
    fields = content[closing + 2 :].split()
    try:
        return int(fields[19])
    except (IndexError, ValueError):
        return None


def process_matches(pid: int, expected_start_ticks: int | None) -> bool:
    actual = process_start_ticks(pid)
    return actual is not None and (
        expected_start_ticks is None or actual == expected_start_ticks
    )
