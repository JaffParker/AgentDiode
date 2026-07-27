from agentdiode.tray.tooltip import build_tooltip, duration


def test_duration() -> None:
    assert duration(57) == "0:57"
    assert duration(3672) == "1:01:12"


def test_empty_tooltip() -> None:
    assert build_tooltip({"sessions": []}) == "AgentDiode\nNo active AI agents"
