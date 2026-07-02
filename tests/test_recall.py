import json

from research_assistant import cli, daily, focus, projects, recall, state


def test_recall_searches_local_state_sources(tmp_path, monkeypatch):
    monkeypatch.setenv("RESEARCH_HOME", str(tmp_path))

    daily.append_timeline("2026-06-01", "[研究·决定] agent memory 先做本地 recall")
    loops = []
    daily.add_loop(loops, "补 agent memory recall 测试", source="开发", created="2026-06-01",
                   project="Talos", next_action="写 pytest")
    daily.save_loops(loops)
    ps = []
    projects.add_project(ps, "Talos", created="2026-06-01", goal="个人执行系统")
    projects.save_projects(ps)
    focus.start_focus("写 recall", started="2026-06-01T09:00", project="Talos")
    focus.end_focus(ended="2026-06-01T09:30")
    state.atomic_write_text(state.digest_path("2026-06-01"),
                            "# 论文日报\nagent memory paper\n")

    hits = recall.search("agent memory", limit=10)
    kinds = {h.kind for h in hits}
    assert {"timeline", "open_loop", "paper_digest"} <= kinds
    assert hits[0].score >= hits[-1].score
    assert all(h.text for h in hits)


def test_recall_prefers_title_and_structured_state(tmp_path, monkeypatch):
    monkeypatch.setenv("RESEARCH_HOME", str(tmp_path))

    daily.append_timeline("2026-06-01", "读了一点 Talos 的背景")
    loops = []
    daily.add_loop(loops, "催张三确认接口字段", source="会议", created="2026-06-01",
                   domain="work", owner="张三", next_action="发消息问字段")
    daily.save_loops(loops)

    hits = recall.search("张三接口", limit=2)
    assert hits[0].kind == "open_loop"
    assert "张三" in hits[0].text


def test_recall_empty_state_returns_empty(tmp_path, monkeypatch):
    monkeypatch.setenv("RESEARCH_HOME", str(tmp_path))
    assert recall.search("anything") == []


def test_recall_cli_prints_json(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("RESEARCH_HOME", str(tmp_path))
    daily.append_timeline("2026-06-01", "[研究·想通] recall 应该先只读本地状态")

    assert cli.main(["recall", "--query", "recall", "--limit", "1"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert len(out) == 1
    assert out[0]["kind"] == "timeline"
