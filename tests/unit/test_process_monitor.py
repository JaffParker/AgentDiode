from pathlib import Path

from agentdiode.daemon.process_monitor import process_start_ticks


def test_process_start_ticks_handles_spaces_in_name(tmp_path: Path) -> None:
    process_dir = tmp_path / "42"
    process_dir.mkdir()
    # Fields after the command start at field 3. starttime is field 22.
    process_dir.joinpath("stat").write_text(
        "42 (name with spaces) S 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 999 20\n",
        encoding="utf-8",
    )
    assert process_start_ticks(42, tmp_path) == 999


def test_missing_process(tmp_path: Path) -> None:
    assert process_start_ticks(404, tmp_path) is None
