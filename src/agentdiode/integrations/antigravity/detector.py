from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass


@dataclass(frozen=True)
class AntigravityDetection:
    installed: bool
    executable: str | None
    version: str | None
    reliability: str


def detect() -> AntigravityDetection:
    executable = shutil.which("agy")
    if not executable:
        return AntigravityDetection(False, None, None, "unavailable")
    result = subprocess.run(
        [executable, "--version"], check=False, capture_output=True, text=True, timeout=5
    )
    version = (result.stdout or result.stderr).strip().splitlines()[0]
    return AntigravityDetection(True, executable, version, "partial")
