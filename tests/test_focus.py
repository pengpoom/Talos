import pytest
from research_assistant import state
import research_assistant.focus as focus


def test_now_iso_shape():
    s = state.now_iso("UTC")
    assert len(s) == 16 and s[10] == "T"


def test_start_and_load_focus(tmp_path, monkeypatch):
    monkeypatch.setenv("RESEARCH_HOME", str(tmp_path))
    sess = focus.start_focus("写 intro", started="2026-06-01T14:00", planned_min=30)
    assert sess["active"] is True and sess["task"] == "写 intro"
    loaded = focus.load_focus()
    assert loaded["task"] == "写 intro" and loaded["planned_min"] == 30


def test_load_focus_none_when_missing(tmp_path, monkeypatch):
    monkeypatch.setenv("RESEARCH_HOME", str(tmp_path))
    assert focus.load_focus() is None


def test_end_focus_marks_inactive(tmp_path, monkeypatch):
    monkeypatch.setenv("RESEARCH_HOME", str(tmp_path))
    focus.start_focus("x", started="2026-06-01T14:00")
    sess = focus.end_focus(ended="2026-06-01T14:30")
    assert sess["active"] is False and sess["ended"] == "2026-06-01T14:30"


def test_end_focus_without_active_raises(tmp_path, monkeypatch):
    monkeypatch.setenv("RESEARCH_HOME", str(tmp_path))
    with pytest.raises(RuntimeError):
        focus.end_focus(ended="2026-06-01T14:30")


def test_elapsed_minutes():
    assert focus.elapsed_minutes("2026-06-01T14:00", "2026-06-01T14:45") == 45
    assert focus.elapsed_minutes("2026-06-01T14:00", "2026-06-01T15:30") == 90
