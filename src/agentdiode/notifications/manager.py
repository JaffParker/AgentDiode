from __future__ import annotations

import shutil
import subprocess

from agentdiode.config import load as load_config
from agentdiode.models import Session

NOTIFIABLE = {"completed", "error", "waiting_input", "waiting_approval"}
TITLES = {
    "completed": "{agent} completed",
    "error": "{agent} failed",
    "waiting_input": "{agent} needs your response",
    "waiting_approval": "{agent} needs approval",
}
CONFIG_KEYS = {
    "completed": "on_completed",
    "error": "on_error",
    "waiting_input": "on_waiting_input",
    "waiting_approval": "on_waiting_approval",
}


class NotificationManager:
    def __init__(self) -> None:
        self.last_state: dict[str, str] = {}
        self.executable = shutil.which("notify-send")

    def notify(self, session: Session) -> bool:
        previous = self.last_state.get(session.session_id)
        self.last_state[session.session_id] = session.state
        if previous == session.state or session.state not in NOTIFIABLE or not self.executable:
            return False
        config = load_config().notifications
        if not config.enabled or not getattr(config, CONFIG_KEYS[session.state]):
            return False
        title = TITLES[session.state].format(agent=session.agent_name)
        detail = session.project_name or "Unknown project"
        if session.error_message:
            detail = f"{detail} · {session.error_message[:160]}"
        subprocess.Popen(
            [self.executable, "--app-name=AgentDiode", title, detail],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        return True
