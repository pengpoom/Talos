import json
from pathlib import Path
from research_assistant import cli, arxiv


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
