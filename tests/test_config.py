from pathlib import Path
import pytest
from research_assistant.config import load_prefs, style_prefs, feature_enabled, schedule_for


def _write(tmp_path: Path, text: str) -> Path:
    p = tmp_path / "prefs.yaml"
    p.write_text(text, encoding="utf-8")
    return p


def test_load_prefs_reads_arxiv_and_timezone(tmp_path):
    p = _write(tmp_path, """
timezone: Asia/Shanghai
arxiv:
  categories: [cs.RO, cs.LG]
  keywords: ["robotic manipulation", "LLM agent"]
  max_per_day: 5
""")
    prefs = load_prefs(p)
    assert prefs.timezone == "Asia/Shanghai"
    assert prefs.arxiv.categories == ["cs.RO", "cs.LG"]
    assert prefs.arxiv.keywords == ["robotic manipulation", "LLM agent"]
    assert prefs.arxiv.max_per_day == 5


def test_load_prefs_defaults_when_fields_missing(tmp_path):
    p = _write(tmp_path, "arxiv: {}\n")
    prefs = load_prefs(p)
    assert prefs.timezone == "UTC"
    assert prefs.arxiv.categories == []
    assert prefs.arxiv.max_per_day == 5


def test_load_prefs_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_prefs(tmp_path / "nope.yaml")


def test_style_prefs_defaults(tmp_path):
    p = _write(tmp_path, "arxiv: {}\n")
    s = style_prefs(load_prefs(p))
    assert s.proactivity == "high"
    assert s.accountability == "gentle"
    assert s.celebrate_wins is True


def test_style_prefs_reads_values(tmp_path):
    p = _write(tmp_path, "style:\n  accountability: savage\n  celebrate_wins: false\n")
    s = style_prefs(load_prefs(p))
    assert s.accountability == "savage"
    assert s.celebrate_wins is False


def test_feature_enabled_default_true_and_override(tmp_path):
    p = _write(tmp_path, "features:\n  morning_plan: false\n")
    prefs = load_prefs(p)
    assert feature_enabled(prefs, "morning_plan") is False
    assert feature_enabled(prefs, "evening_review") is True


def test_schedule_for(tmp_path):
    p = _write(tmp_path, "schedule:\n  morning_plan: \"08:30\"\n")
    assert schedule_for(load_prefs(p), "morning_plan") == "08:30"
    assert schedule_for(load_prefs(p), "evening_review") is None
