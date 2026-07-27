from agentdiode.config import Config, NotificationConfig
from agentdiode.models import Session
from agentdiode.notifications.manager import NotificationManager


def test_notifications_are_deduplicated(monkeypatch) -> None:
    manager = NotificationManager()
    manager.executable = None
    session = Session("one", "codex", "Codex", "completed")
    assert manager.notify(session) is False
    assert manager.notify(session) is False


def test_notifications_respect_configuration(monkeypatch) -> None:
    manager = NotificationManager()
    manager.executable = "/usr/bin/notify-send"
    monkeypatch.setattr(
        "agentdiode.notifications.manager.load_config",
        lambda: Config(notifications=NotificationConfig(enabled=False)),
    )
    called = False

    def unexpected_call(*_args: object, **_kwargs: object) -> None:
        nonlocal called
        called = True

    monkeypatch.setattr("subprocess.Popen", unexpected_call)
    session = Session("disabled", "codex", "Codex", "completed")
    assert manager.notify(session) is False
    assert called is False
