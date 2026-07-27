from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler

from agentdiode.paths import ensure_private_directory, state_dir


class PrivacyFilter(logging.Filter):
    SENSITIVE = ("token", "api_key", "apikey", "password", "authorization", "secret")

    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage().lower()
        if any(value in message for value in self.SENSITIVE):
            record.msg = "[sensitive log message suppressed]"
            record.args = ()
        return True


def configure_logging(component: str, debug: bool = False) -> None:
    log_dir = state_dir() / "logs"
    ensure_private_directory(log_dir)
    handler = RotatingFileHandler(
        log_dir / f"{component}.log",
        maxBytes=2 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    handler.addFilter(PrivacyFilter())
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s %(levelname)s %(name)s %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S%z",
        )
    )
    root = logging.getLogger()
    root.setLevel(logging.DEBUG if debug else logging.INFO)
    root.handlers.clear()
    root.addHandler(handler)
