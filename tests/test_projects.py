import pytest
import research_assistant.projects as projects


# --- CRUD ---

def test_add_project_assigns_incremental_ids(tmp_path, monkeypatch):
    monkeypatch.setenv("RESEARCH_HOME", str(tmp_path))
    ps = []
    a = projects.add_project(ps, "lunwen2", created="2026-06-02")
    b = projects.add_project(ps, "A项目", created="2026-06-02", domain="work")
    assert a["id"] == "p1" and b["id"] == "p2"
    assert a["domain"] == "research" and b["domain"] == "work"
    assert a["status"] == "active" and a["docs"] == [] and a["people"] == []


def test_save_load_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setenv("RESEARCH_HOME", str(tmp_path))
    ps = []
    projects.add_project(ps, "lunwen2", created="2026-06-02", goal="投 NeurIPS")
    projects.save_projects(ps)
    loaded = projects.load_projects()
    assert loaded[0]["name"] == "lunwen2" and loaded[0]["goal"] == "投 NeurIPS"


def test_load_projects_backfills_old_schema(tmp_path, monkeypatch):
    monkeypatch.setenv("RESEARCH_HOME", str(tmp_path))
    projects.save_projects([{"id": "p1", "name": "老项目", "created": "2026-05-30"}])
    p = projects.load_projects()[0]
    assert p["domain"] == "research" and p["status"] == "active"
    assert p["goal"] == "" and p["docs"] == [] and p["people"] == [] and p["next_milestone"] is None


def test_find_project_by_name_and_id(tmp_path, monkeypatch):
    monkeypatch.setenv("RESEARCH_HOME", str(tmp_path))
    ps = []
    projects.add_project(ps, "lunwen2", created="2026-06-02")
    assert projects.find_project(ps, "p1")["name"] == "lunwen2"
    assert projects.find_project(ps, "LunWen2")["id"] == "p1"
    assert projects.find_project(ps, "不存在") is None


def test_update_project_fields_and_lists(tmp_path, monkeypatch):
    monkeypatch.setenv("RESEARCH_HOME", str(tmp_path))
    ps = []
    projects.add_project(ps, "lunwen2", created="2026-06-02")
    p = projects.update_project(ps, "lunwen2", updated="2026-06-03", status="paused",
                                goal="改投 ICLR", next_milestone="补实验",
                                add_doc="https://x/doc1", add_person="bobo")
    assert p["status"] == "paused" and p["goal"] == "改投 ICLR"
    assert p["next_milestone"] == "补实验" and p["updated"] == "2026-06-03"
    assert p["docs"] == ["https://x/doc1"] and p["people"] == ["bobo"]


def test_update_project_dedupes_doc_and_person(tmp_path, monkeypatch):
    monkeypatch.setenv("RESEARCH_HOME", str(tmp_path))
    ps = []
    projects.add_project(ps, "x", created="2026-06-02")
    projects.update_project(ps, "x", updated="2026-06-03", add_doc="d1", add_person="bobo")
    projects.update_project(ps, "x", updated="2026-06-03", add_doc="d1", add_person="bobo")
    assert ps[0]["docs"] == ["d1"] and ps[0]["people"] == ["bobo"]


def test_update_project_missing_raises(tmp_path, monkeypatch):
    monkeypatch.setenv("RESEARCH_HOME", str(tmp_path))
    with pytest.raises(KeyError):
        projects.update_project([], "无", updated="2026-06-03", status="done")


# --- project_status 聚合 ---

def _loop(id, project, status="open", priority="medium", due=None, created="2026-06-01",
          next_action=None, owner=None):
    return {"id": id, "desc": id, "project": project, "status": status,
            "priority": priority, "due": due, "created": created,
            "next_action": next_action, "owner": owner, "last_nudged": None}


def test_status_matches_loops_by_name_and_id():
    ps = [{"id": "p1", "name": "lunwen2", "domain": "research", "status": "active",
           "goal": "", "next_milestone": None, "docs": [], "people": [], "created": "2026-06-01"}]
    loops = [_loop("o1", "lunwen2"), _loop("o2", "p1"), _loop("o3", "别的项目"),
             _loop("o4", None), _loop("o5", "lunwen2", status="done")]
    out = projects.project_status("lunwen2", ps, loops, [], "2026-06-02")
    assert out["project"]["id"] == "p1"
    assert out["open_count"] == 2  # o1 + o2（o5 已 done，o3/o4 不匹配）
    assert out["done_count"] == 1
    assert {l["id"] for l in out["open_loops"]} == {"o1", "o2"}


def test_status_open_loops_sorted_overdue_then_priority():
    loops = [
        _loop("o1", "x", priority="low"),
        _loop("o2", "x", priority="urgent"),
        _loop("o3", "x", priority="medium", due="2026-05-29"),
    ]
    out = projects.project_status("x", [], loops, [], "2026-06-02")
    # 逾期(o3)排第一，其余按优先级 urgent>low
    assert [l["id"] for l in out["open_loops"]] == ["o3", "o2", "o1"]
    assert out["overdue_count"] == 1
    assert out["next_actions"][0]["overdue"] is True


def test_status_aggregates_focus_minutes():
    log = [
        {"task": "a", "project": "lunwen2", "elapsed_min": 40},
        {"task": "b", "project": "lunwen2", "elapsed_min": 50},
        {"task": "c", "project": "别的", "elapsed_min": 30},
        {"task": "d", "project": None, "elapsed_min": 20},
    ]
    out = projects.project_status("lunwen2", [], [], log, "2026-06-02")
    assert out["focus"] == {"sessions": 2, "total_min": 90}


def test_status_unknown_project_still_aggregates_tagged():
    # 没有项目记录，但有挂了这个名字的 loop / focus，仍要能聚合
    loops = [_loop("o1", "野项目")]
    log = [{"task": "a", "project": "野项目", "elapsed_min": 15}]
    out = projects.project_status("野项目", [], loops, log, "2026-06-02")
    assert out["project"] is None
    assert out["open_count"] == 1 and out["focus"]["total_min"] == 15
