from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass


@dataclass(frozen=True)
class ClaudeDetection:
    installed: bool
    executable: str | None
    version: str | None
    reliability: str
    detail: str


def detect() -> ClaudeDetection:
    executable = shutil.which("claude")
    if not executable:
        return ClaudeDetection(False, None, None, "unavailable", "Claude Code is not installed")
    result = subprocess.run(
        [executable, "--version"], check=False, capture_output=True, text=True, timeout=5
    )
    version = (result.stdout or result.stderr).strip().splitlines()[0]
    return ClaudeDetection(
        True,
        executable,
        version,
        "partial",
        "Official lifecycle hooks are available",
    )
