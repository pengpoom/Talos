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
    assert focus.elapsed_minutes("2026-06-01T16:27", "2026-06-01T08:31") == 0


# --- 历史存档 ---

def test_end_focus_appends_to_log_with_elapsed(tmp_path, monkeypatch):
    monkeypatch.setenv("RESEARCH_HOME", str(tmp_path))
    focus.start_focus("写 intro", started="2026-06-01T14:00", planned_min=25)
    sess = focus.end_focus(ended="2026-06-01T14:25")
    assert sess["elapsed_min"] == 25
    log = focus.load_focus_log()
    assert len(log) == 1
    assert log[0]["task"] == "写 intro" and log[0]["elapsed_min"] == 25
    assert log[0]["ended"] == "2026-06-01T14:25"


def test_focus_log_accumulates(tmp_path, monkeypatch):
    monkeypatch.setenv("RESEARCH_HOME", str(tmp_path))
    focus.start_focus("a", started="2026-06-01T09:00", planned_min=20)
    focus.end_focus(ended="2026-06-01T09:20")
    focus.start_focus("b", started="2026-06-01T10:00", planned_min=30)
    focus.end_focus(ended="2026-06-01T10:30")
    assert [r["task"] for r in focus.load_focus_log()] == ["a", "b"]


def test_focus_stats_totals_and_since(tmp_path, monkeypatch):
    monkeypatch.setenv("RESEARCH_HOME", str(tmp_path))
    focus.start_focus("a", started="2026-05-30T09:00")
    focus.end_focus(ended="2026-05-30T09:20")
    focus.start_focus("b", started="2026-06-01T10:00")
    focus.end_focus(ended="2026-06-01T10:30")
    log = focus.load_focus_log()
    assert focus.focus_stats(log) == {"count": 2, "total_min": 50}
    assert focus.focus_stats(log, since="2026-06-01") == {"count": 1, "total_min": 30}
