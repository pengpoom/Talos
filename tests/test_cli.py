import json
from pathlib import Path
from research_assistant import cli, arxiv, daily


def test_fetch_prints_json(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("RESEARCH_HOME", str(tmp_path))
    prefs = tmp_path / "prefs.yaml"
    prefs.write_text("timezone: UTC\narxiv:\n  categories: [cs.RO]\n", encoding="utf-8")
    monkeypatch.setattr(arxiv, "fetch_candidates",
                        lambda *a, **k: [arxiv.Paper("id1", "T", "S", ["A"], "L", "P")])
    rc = cli.main(["fetch", "--prefs", str(prefs)])
    out = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert out[0]["id"] == "id1"


def test_fetch_returns_nonzero_on_failure(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("RESEARCH_HOME", str(tmp_path))
    prefs = tmp_path / "prefs.yaml"
    prefs.write_text("timezone: UTC\narxiv:\n  categories: [cs.RO]\n", encoding="utf-8")

    def boom(*a, **k):
        raise RuntimeError("arXiv down")

    monkeypatch.setattr(arxiv, "fetch_candidates", boom)
    rc = cli.main(["fetch", "--prefs", str(prefs)])
    assert rc == 1
    assert "arXiv down" in capsys.readouterr().err


def test_commit_archives_and_marks_seen(tmp_path, monkeypatch):
    monkeypatch.setenv("RESEARCH_HOME", str(tmp_path))
    digest = tmp_path / "d.md"
    digest.write_text("# digest body", encoding="utf-8")
    rc = cli.main([
        "commit", "--ids", "idA,idB",
        "--digest-file", str(digest),
        "--date", "2026-05-30",
    ])
    assert rc == 0
    from research_assistant import state
    assert state.load_seen(state.seen_path()) == {"idA", "idB"}
    assert state.digest_path("2026-05-30").read_text(encoding="utf-8") == "# digest body"


def test_today_set_plan_and_show(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("RESEARCH_HOME", str(tmp_path))
    items = json.dumps([{"task": "写 intro", "next_action": "开 overleaf"}])
    assert cli.main(["today-set-plan", "--tz", "UTC", "--json", items]) == 0
    capsys.readouterr()
    assert cli.main(["today-show", "--tz", "UTC"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["plan"][0]["task"] == "写 intro"


def test_today_mark_done(tmp_path, monkeypatch):
    monkeypatch.setenv("RESEARCH_HOME", str(tmp_path))
    cli.main(["today-set-plan", "--tz", "UTC", "--json", json.dumps([{"task": "A"}])])
    assert cli.main(["today-mark-done", "--tz", "UTC", "--id", "t1"]) == 0
    assert daily.load_today("UTC")["plan"][0]["done"] is True


def test_today_mark_done_bad_id_returns_1(tmp_path, monkeypatch):
    monkeypatch.setenv("RESEARCH_HOME", str(tmp_path))
    cli.main(["today-set-plan", "--tz", "UTC", "--json", json.dumps([{"task": "A"}])])
    assert cli.main(["today-mark-done", "--tz", "UTC", "--id", "tX"]) == 1


def test_today_rollover(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("RESEARCH_HOME", str(tmp_path))
    daily.save_today({"date": "2000-01-01",
                      "plan": [{"id": "t1", "task": "悬着的事", "next_action": "", "done": False}],
                      "unplanned_done": [], "logged": False})
    assert cli.main(["today-rollover", "--tz", "UTC"]) == 0
    assert json.loads(capsys.readouterr().out) == ["悬着的事"]


def test_loops_add_and_list(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("RESEARCH_HOME", str(tmp_path))
    assert cli.main(["loops-add", "--tz", "UTC", "--desc", "回审稿人邮件", "--source", "碎念"]) == 0
    capsys.readouterr()
    assert cli.main(["loops-list"]) == 0
    loops = json.loads(capsys.readouterr().out)
    assert loops[0]["desc"] == "回审稿人邮件"
    assert loops[0]["id"] == "o1"
    assert loops[0]["status"] == "open"


def test_timeline_append(tmp_path, monkeypatch):
    monkeypatch.setenv("RESEARCH_HOME", str(tmp_path))
    assert cli.main(["timeline-append", "--date", "2026-05-30", "--text", "09:30 写 intro ✅"]) == 0
    assert "写 intro ✅" in daily.timeline_path("2026-05-30").read_text(encoding="utf-8")
