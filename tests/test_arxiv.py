from pathlib import Path
import pytest
from research_assistant.arxiv import (
    build_query, fetch_raw, parse_entries, dedup, fetch_candidates, Paper,
)
from research_assistant.config import ArxivPrefs

FIXTURE = Path(__file__).parent / "fixtures" / "arxiv_sample.xml"


def test_build_query_combines_categories_and_keywords():
    q = build_query(["cs.RO", "cs.LG"], ["robotic manipulation"])
    assert q == '(cat:cs.RO OR cat:cs.LG) AND (all:"robotic manipulation")'


def test_build_query_categories_only():
    assert build_query(["eess.SY"], []) == "(cat:eess.SY)"


class _Resp:
    def __init__(self, text, ok=True):
        self.text = text
        self._ok = ok

    def raise_for_status(self):
        if not self._ok:
            raise RuntimeError("http 500")


def test_fetch_raw_returns_body():
    calls = []

    def fake_get(url, params=None, timeout=None):
        calls.append((url, params))
        return _Resp("<feed/>")

    body = fetch_raw("cat:cs.RO", 10, http_get=fake_get)
    assert body == "<feed/>"
    assert calls[0][1]["search_query"] == "cat:cs.RO"
    assert calls[0][1]["max_results"] == 10


def test_fetch_raw_retries_then_raises():
    attempts = {"n": 0}

    def flaky_get(url, params=None, timeout=None):
        attempts["n"] += 1
        raise ConnectionError("boom")

    with pytest.raises(RuntimeError):
        fetch_raw("cat:cs.RO", 10, http_get=flaky_get, retries=3, backoff=0)
    assert attempts["n"] == 3


def test_parse_entries():
    papers = parse_entries(FIXTURE.read_text(encoding="utf-8"))
    assert len(papers) == 2
    assert papers[0].id == "http://arxiv.org/abs/2401.00001v1"
    assert papers[0].title == "A Sample Paper on Robotic Manipulation"
    assert papers[0].authors == ["Alice Smith", "Bob Jones"]
    assert "robotic manipulation" in papers[0].summary.lower()


def test_parse_entries_empty_feed():
    assert parse_entries("<feed xmlns='http://www.w3.org/2005/Atom'/>") == []


def test_dedup_filters_seen():
    papers = parse_entries(FIXTURE.read_text(encoding="utf-8"))
    out = dedup(papers, {"http://arxiv.org/abs/2401.00001v1"})
    assert [p.id for p in out] == ["http://arxiv.org/abs/2401.00002v1"]


def test_fetch_candidates_dedups():
    def fake_get(url, params=None, timeout=None):
        class R:
            text = FIXTURE.read_text(encoding="utf-8")

            def raise_for_status(self):
                pass

        return R()

    prefs = ArxivPrefs(categories=["cs.RO"], keywords=[], max_per_day=5)
    out = fetch_candidates(prefs, {"http://arxiv.org/abs/2401.00002v1"}, http_get=fake_get)
    assert [p.id for p in out] == ["http://arxiv.org/abs/2401.00001v1"]
