from __future__ import annotations

import re
import shutil
import subprocess
from dataclasses import dataclass


@dataclass(frozen=True)
class CodexDetection:
    installed: bool
    executable: str | None
    version: str | None
    hooks_supported: bool
    reliability: str


def detect() -> CodexDetection:
    executable = shutil.which("codex")
    if not executable:
        return CodexDetection(False, None, None, False, "unavailable")
    result = subprocess.run(
        [executable, "--version"],
        check=False,
        capture_output=True,
        text=True,
        timeout=5,
    )
    match = re.search(r"(\d+\.\d+\.\d+)", result.stdout + result.stderr)
    version = match.group(1) if match else None
    features = subprocess.run(
        [executable, "features", "list"],
        check=False,
        capture_output=True,
        text=True,
        timeout=10,
    )
    hooks = any(line.split()[:1] == ["hooks"] for line in features.stdout.splitlines())
    return CodexDetection(True, executable, version, hooks, "partial" if hooks else "heuristic")
