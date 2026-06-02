import pytest
import research_assistant.daily as daily


# --- today 模型 ---

def test_load_today_fresh_when_missing(tmp_path, monkeypatch):
    monkeypatch.setenv("RESEARCH_HOME", str(tmp_path))
    t = daily.load_today("UTC")
    assert t["plan"] == [] and t["unplanned_done"] == [] and t["logged"] is False
    assert len(t["date"]) == 10


def test_save_then_load_today_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setenv("RESEARCH_HOME", str(tmp_path))
    t = daily.load_today("UTC")
    daily.set_plan(t, [{"task": "写 intro", "next_action": "开 overleaf 写第一句"}])
    daily.save_today(t)
    again = daily.load_today("UTC")
    assert again["plan"][0]["task"] == "写 intro"
    assert again["plan"][0]["id"] == "t1"
    assert again["plan"][0]["done"] is False


def test_load_today_fresh_when_stale(tmp_path, monkeypatch):
    monkeypatch.setenv("RESEARCH_HOME", str(tmp_path))
    daily.save_today({"date": "2000-01-01", "plan": [{"id": "t1", "task": "x",
                     "next_action": "", "done": False}], "unplanned_done": [], "logged": False})
    t = daily.load_today("UTC")
    assert t["date"] != "2000-01-01"
    assert t["plan"] == []


def test_mark_done_and_undone_items(tmp_path, monkeypatch):
    monkeypatch.setenv("RESEARCH_HOME", str(tmp_path))
    t = daily.load_today("UTC")
    daily.set_plan(t, [{"task": "A"}, {"task": "B"}])
    daily.mark_done(t, "t1")
    assert [i["task"] for i in daily.undone_items(t)] == ["B"]


def test_add_unplanned_and_log(tmp_path, monkeypatch):
    monkeypatch.setenv("RESEARCH_HOME", str(tmp_path))
    t = daily.load_today("UTC")
    daily.add_unplanned(t, "回了导师邮件")
    daily.mark_logged(t)
    assert t["unplanned_done"] == ["回了导师邮件"]
    assert t["logged"] is True


# --- open_loops 模型 ---

def test_loops_add_assigns_incremental_ids(tmp_path, monkeypatch):
    monkeypatch.setenv("RESEARCH_HOME", str(tmp_path))
    loops = []
    a = daily.add_loop(loops, "回审稿人邮件", source="碎念", created="2026-05-30")
    b = daily.add_loop(loops, "查文献", source="复盘", created="2026-05-30")
    assert a["id"] == "o1" and b["id"] == "o2"
    assert a["status"] == "open" and a["last_nudged"] is None


def test_loops_save_load_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setenv("RESEARCH_HOME", str(tmp_path))
    loops = []
    daily.add_loop(loops, "x", source="碎念", created="2026-05-30")
    daily.save_loops(loops)
    assert daily.load_loops()[0]["desc"] == "x"


def test_update_loop_status_and_nudged(tmp_path, monkeypatch):
    monkeypatch.setenv("RESEARCH_HOME", str(tmp_path))
    loops = []
    daily.add_loop(loops, "x", source="碎念", created="2026-05-30")
    daily.update_loop(loops, "o1", status="done", nudged_date="2026-05-31")
    assert loops[0]["status"] == "done"
    assert loops[0]["last_nudged"] == "2026-05-31"


def test_update_loop_missing_raises(tmp_path):
    with pytest.raises(KeyError):
        daily.update_loop([], "oX", status="done")


# --- 结转 + 时间轴 ---

def test_rollover_stale_moves_undone_to_loops(tmp_path, monkeypatch):
    monkeypatch.setenv("RESEARCH_HOME", str(tmp_path))
    daily.save_today({"date": "2000-01-01",
                      "plan": [{"id": "t1", "task": "调实验参数", "next_action": "", "done": False},
                               {"id": "t2", "task": "已完成的", "next_action": "", "done": True}],
                      "unplanned_done": [], "logged": False})
    moved = daily.rollover_stale("UTC")
    assert moved == ["调实验参数"]
    assert [l["desc"] for l in daily.load_loops()] == ["调实验参数"]
    assert daily.load_loops()[0]["source"] == "未完成"


def test_rollover_noop_when_today_is_current(tmp_path, monkeypatch):
    monkeypatch.setenv("RESEARCH_HOME", str(tmp_path))
    t = daily.load_today("UTC")
    daily.set_plan(t, [{"task": "A"}])
    daily.save_today(t)
    assert daily.rollover_stale("UTC") == []


def test_append_timeline_creates_and_appends(tmp_path, monkeypatch):
    monkeypatch.setenv("RESEARCH_HOME", str(tmp_path))
    daily.append_timeline("2026-05-30", "09:30-11:00 写 intro ✅")
    daily.append_timeline("2026-05-30", "14:00-15:30 读论文")
    text = daily.timeline_path("2026-05-30").read_text(encoding="utf-8")
    assert text.startswith("# 2026-05-30 时间轴")
    assert "写 intro ✅" in text and "读论文" in text


# --- 巡检 due_for_nudge ---

def test_days_between_basic():
    assert daily._days_between("2026-05-30", "2026-06-01") == 2


def test_is_overdue():
    assert daily.is_overdue({"due": "2026-05-30"}, "2026-06-01") is True
    assert daily.is_overdue({"due": "2026-06-02"}, "2026-06-01") is False
    assert daily.is_overdue({"due": None}, "2026-06-01") is False


def test_due_for_nudge_includes_open_never_nudged():
    loops = [{"id": "o1", "status": "open", "last_nudged": None,
              "created": "2026-05-30", "due": None}]
    assert [l["id"] for l in daily.due_for_nudge(loops, "2026-06-01")] == ["o1"]


def test_due_for_nudge_excludes_closed_and_nudged_today():
    loops = [
        {"id": "o1", "status": "done", "last_nudged": None, "created": "2026-05-30", "due": None},
        {"id": "o2", "status": "open", "last_nudged": "2026-06-01", "created": "2026-05-30", "due": None},
    ]
    assert daily.due_for_nudge(loops, "2026-06-01") == []


def test_due_for_nudge_respects_cadence():
    loops = [{"id": "o1", "status": "open", "last_nudged": "2026-05-30",
              "created": "2026-05-30", "due": None}]
    assert daily.due_for_nudge(loops, "2026-06-01", cadence_days=3) == []
    assert [l["id"] for l in daily.due_for_nudge(loops, "2026-06-01", cadence_days=2)] == ["o1"]


def test_due_for_nudge_overdue_sorts_first():
    loops = [
        {"id": "o1", "status": "open", "last_nudged": None, "created": "2026-05-31", "due": None},
        {"id": "o2", "status": "open", "last_nudged": None, "created": "2026-05-30", "due": "2026-05-29"},
    ]
    assert [l["id"] for l in daily.due_for_nudge(loops, "2026-06-01")] == ["o2", "o1"]


# --- open_loops 富字段（domain/next_action/priority/owner/project）---

def test_add_loop_stores_new_fields(tmp_path, monkeypatch):
    monkeypatch.setenv("RESEARCH_HOME", str(tmp_path))
    loop = daily.add_loop([], "催张三确认接口", source="会议", created="2026-06-02",
                          domain="work", next_action="发消息问接口字段", priority="high",
                          owner="张三", project="A项目")
    assert loop["domain"] == "work" and loop["owner"] == "张三"
    assert loop["next_action"] == "发消息问接口字段" and loop["priority"] == "high"
    assert loop["project"] == "A项目"


def test_add_loop_defaults_new_fields():
    loop = daily.add_loop([], "x", source="碎念", created="2026-06-02")
    assert loop["domain"] == "research" and loop["priority"] == "medium"
    assert loop["next_action"] is None and loop["owner"] is None


def test_load_loops_backfills_old_schema(tmp_path, monkeypatch):
    monkeypatch.setenv("RESEARCH_HOME", str(tmp_path))
    daily.save_loops([{"id": "o1", "desc": "老条目", "created": "2026-05-30",
                       "last_nudged": None, "status": "open", "due": None, "source": "碎念"}])
    loop = daily.load_loops()[0]
    assert loop["domain"] == "research" and loop["priority"] == "medium"
    assert loop["next_action"] is None and loop["owner"] is None and loop["project"] is None


def test_update_loop_sets_new_fields(tmp_path, monkeypatch):
    monkeypatch.setenv("RESEARCH_HOME", str(tmp_path))
    loops = []
    daily.add_loop(loops, "x", source="碎念", created="2026-06-02")
    daily.update_loop(loops, "o1", next_action="先打开岗位列表", priority="urgent",
                      domain="work", owner="我")
    assert loops[0]["next_action"] == "先打开岗位列表"
    assert loops[0]["priority"] == "urgent" and loops[0]["domain"] == "work"


def test_due_for_nudge_priority_sorts_before_created():
    loops = [
        {"id": "o1", "status": "open", "last_nudged": None, "created": "2026-05-30",
         "due": None, "priority": "low"},
        {"id": "o2", "status": "open", "last_nudged": None, "created": "2026-05-31",
         "due": None, "priority": "urgent"},
    ]
    assert [l["id"] for l in daily.due_for_nudge(loops, "2026-06-02")] == ["o2", "o1"]
