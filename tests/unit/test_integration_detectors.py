from agentdiode.integrations.antigravity.detector import detect as detect_antigravity
from agentdiode.integrations.claude.detector import detect as detect_claude


def test_missing_integrations_are_unavailable(monkeypatch) -> None:
    monkeypatch.setattr("shutil.which", lambda _name: None)
    assert detect_claude().reliability == "unavailable"
    assert detect_antigravity().reliability == "unavailable"
