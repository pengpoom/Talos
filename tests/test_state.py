import research_assistant.state as state


def test_research_home_from_env(tmp_path, monkeypatch):
    monkeypatch.setenv("RESEARCH_HOME", str(tmp_path))
    assert state.research_home() == tmp_path
    assert state.seen_path() == tmp_path / "state" / "papers" / "seen.jsonl"
    assert state.digest_path("2026-05-30") == tmp_path / "state" / "papers" / "digest-2026-05-30.md"


def test_atomic_write_and_read_json(tmp_path, monkeypatch):
    monkeypatch.setenv("RESEARCH_HOME", str(tmp_path))
    target = tmp_path / "state" / "today.json"
    state.atomic_write_json(target, {"a": 1})
    assert state.read_json(target, default=None) == {"a": 1}


def test_read_json_missing_returns_default(tmp_path):
    assert state.read_json(tmp_path / "missing.json", default=[]) == []


def test_read_json_corrupt_backs_up_and_returns_default(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("{not json", encoding="utf-8")
    assert state.read_json(bad, default={}) == {}
    assert (tmp_path / "bad.json.corrupt").exists()


def test_today_str_uses_timezone():
    s = state.today_str("Asia/Shanghai")
    assert len(s) == 10 and s[4] == "-" and s[7] == "-"


def test_load_seen_missing_returns_empty(tmp_path):
    assert state.load_seen(tmp_path / "seen.jsonl") == set()


def test_append_then_load_seen(tmp_path):
    p = tmp_path / "seen.jsonl"
    state.append_seen(p, ["id-a", "id-b"], "2026-05-30")
    state.append_seen(p, ["id-c"], "2026-05-31")
    assert state.load_seen(p) == {"id-a", "id-b", "id-c"}


def test_load_seen_skips_corrupt_lines(tmp_path):
    p = tmp_path / "seen.jsonl"
    p.write_text('{"id": "ok"}\nGARBAGE\n{"nope": 1}\n', encoding="utf-8")
    assert state.load_seen(p) == {"ok"}
