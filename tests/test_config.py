from pathlib import Path
import pytest
from research_assistant.config import load_prefs


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
