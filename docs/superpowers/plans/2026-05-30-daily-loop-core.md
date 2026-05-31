# 日循环核心 实施计划 (Plan 2)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 Plan 1 地基上做"每天早上规划、晚上复盘 + 记时间轴"的核心日循环，并建好 `today.json` / `open_loops.json` / `timeline` 三套日状态（供后续开放循环巡检、专注陪伴复用）。

**Architecture:** 沿用混合方案。日状态的读写与结转 = 可单测的 `daily.py` + CLI；规划/复盘的判断与对话 = `morning-plan` / `evening-review` 技能里的 agent。全程经飞书 home chat（cron deliver，Plan 1 已验证通道）。`feishucli` 原生任务/日历同步留作**可选增强**（待机器上确认其接口）。

**Tech Stack:** 沿用 Plan 1（Python 包 + pytest + Hermes 技能 / cron / 飞书）。

> **git:** 仓库已起（main，远程 `pengpoom/Talos`），每个任务末尾 `commit` 可直接用。
> **范围:** 本计划 = 日循环核心。**开放循环巡检、专注陪伴 = Plan 3**（复用本计划的 open_loops / today 模型）。`feishucli` 原生任务/日历 = 可选增强，见 §末。
> **承接 Plan 1:** 复用 `config.load_prefs`→`Prefs(timezone, arxiv, raw)`、`state.*`（原子读写/日期/read_json）。`SOUL.snippet.md` 人设已含主动/拆解/接住掉的事/夸/四档问责，**本计划不改 SOUL**。

---

## 关键设计：结转只走 open_loops 一条路

- 晚间复盘把**没做完**的计划项推进 `open_loops.json`（来源标"未完成"）。
- 早上规划从 `open_loops.json` 捞出来摆给你（而不是去翻昨天的 today.json）。
- 兜底：万一某天没复盘，第二天早上 `today-rollover` 会把**过期 today.json** 里的未完成项也补进 open_loops，再重置当天。
- 好处：只有一条"掉队→重提"通道，不需要保留历史 today 文件。

## 文件结构（本计划新建/修改）

```
src/research_assistant/
├── config.py          # Modify — 加 style/schedule/features 访问器
├── daily.py           # Create — today + open_loops + timeline 模型与结转
└── cli.py             # Modify — 加 today-* / loops-* / timeline-append 子命令
tests/
├── test_config.py     # Modify — 加访问器测试
├── test_daily.py      # Create
└── test_cli.py        # Modify — 加新子命令测试
pack/
├── skills/research/morning-plan/SKILL.md     # Create
├── skills/research/evening-review/SKILL.md   # Create
└── cron/jobs.snippet.json                    # Modify — 加晨/晚两个任务
install.sh             # Modify — 复制全部 research 技能、提示注册晨/晚 cron
README.md              # Modify — 加日循环说明
```

---

## Task 1: config 访问器（style / schedule / features）

**Files:**
- Modify: `src/research_assistant/config.py`
- Modify: `tests/test_config.py`

- [ ] **Step 1: 追加失败测试到 `tests/test_config.py`**

```python
from research_assistant.config import style_prefs, feature_enabled, schedule_for


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
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python3 -m pytest tests/test_config.py -v`
Expected: FAIL（`ImportError: cannot import name 'style_prefs'`）

- [ ] **Step 3: 在 `config.py` 末尾追加**

```python
@dataclass
class StylePrefs:
    proactivity: str = "high"
    accountability: str = "gentle"
    tone: str = "warm"
    celebrate_wins: bool = True


def style_prefs(prefs: Prefs) -> StylePrefs:
    s = prefs.raw.get("style") or {}
    return StylePrefs(
        proactivity=s.get("proactivity", "high"),
        accountability=s.get("accountability", "gentle"),
        tone=s.get("tone", "warm"),
        celebrate_wins=bool(s.get("celebrate_wins", True)),
    )


def feature_enabled(prefs: Prefs, name: str) -> bool:
    return bool((prefs.raw.get("features") or {}).get(name, True))


def schedule_for(prefs: Prefs, name: str):
    return (prefs.raw.get("schedule") or {}).get(name)
```

- [ ] **Step 4: 跑测试确认通过**

Run: `python3 -m pytest tests/test_config.py -v`
Expected: 7 passed（原 3 + 新 4）

- [ ] **Step 5: Commit**

```bash
git add src/research_assistant/config.py tests/test_config.py
git commit -m "feat: style/schedule/features prefs accessors"
```

---

## Task 2: daily.py — today 模型

**Files:**
- Create: `src/research_assistant/daily.py`
- Create: `tests/test_daily.py`

- [ ] **Step 1: 写失败测试**

```python
import research_assistant.daily as daily


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
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python3 -m pytest tests/test_daily.py -v`
Expected: FAIL（`ModuleNotFoundError: research_assistant.daily`）

- [ ] **Step 3: 实现 `daily.py`（today 部分）**

```python
from pathlib import Path
from . import state


def today_path() -> Path:
    return state.state_dir() / "today.json"


def open_loops_path() -> Path:
    return state.state_dir() / "open_loops.json"


def timeline_path(date: str) -> Path:
    return state.state_dir() / "timeline" / f"{date}.md"


def _new_today(date: str) -> dict:
    return {"date": date, "plan": [], "unplanned_done": [], "logged": False}


def load_today_raw():
    return state.read_json(today_path(), default=None)


def load_today(tz: str) -> dict:
    date = state.today_str(tz)
    data = load_today_raw()
    if not data or data.get("date") != date:
        return _new_today(date)
    return data


def save_today(data: dict) -> None:
    state.atomic_write_json(today_path(), data)


def set_plan(today: dict, items: list) -> dict:
    today["plan"] = [
        {"id": f"t{i + 1}", "task": it["task"],
         "next_action": it.get("next_action", ""), "done": False}
        for i, it in enumerate(items)
    ]
    return today


def mark_done(today: dict, item_id: str) -> dict:
    for it in today["plan"]:
        if it["id"] == item_id:
            it["done"] = True
            return it
    raise KeyError(item_id)


def add_unplanned(today: dict, text: str) -> None:
    today["unplanned_done"].append(text)


def mark_logged(today: dict) -> None:
    today["logged"] = True


def undone_items(today: dict) -> list:
    return [it for it in today["plan"] if not it["done"]]
```

- [ ] **Step 4: 跑测试确认通过**

Run: `python3 -m pytest tests/test_daily.py -v`
Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add src/research_assistant/daily.py tests/test_daily.py
git commit -m "feat: today.json model"
```

---

## Task 3: daily.py — open_loops 模型

**Files:**
- Modify: `src/research_assistant/daily.py`
- Modify: `tests/test_daily.py`

- [ ] **Step 1: 追加失败测试**

```python
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
    import pytest
    with pytest.raises(KeyError):
        daily.update_loop([], "oX", status="done")
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python3 -m pytest tests/test_daily.py -v`
Expected: FAIL（`AttributeError: ... has no attribute 'add_loop'`）

- [ ] **Step 3: 在 `daily.py` 末尾追加**

```python
def load_loops() -> list:
    return state.read_json(open_loops_path(), default=[])


def save_loops(loops: list) -> None:
    state.atomic_write_json(open_loops_path(), loops)


def _next_id(items: list, prefix: str) -> str:
    nums = [int(i["id"][len(prefix):]) for i in items
            if i.get("id", "").startswith(prefix) and i["id"][len(prefix):].isdigit()]
    return f"{prefix}{(max(nums) if nums else 0) + 1}"


def add_loop(loops: list, desc: str, *, source: str, created: str, due=None) -> dict:
    loop = {"id": _next_id(loops, "o"), "desc": desc, "created": created,
            "last_nudged": None, "status": "open", "due": due, "source": source}
    loops.append(loop)
    return loop


def update_loop(loops: list, loop_id: str, *, status=None, nudged_date=None) -> dict:
    for loop in loops:
        if loop["id"] == loop_id:
            if status:
                loop["status"] = status
            if nudged_date:
                loop["last_nudged"] = nudged_date
            return loop
    raise KeyError(loop_id)
```

- [ ] **Step 4: 跑测试确认通过**

Run: `python3 -m pytest tests/test_daily.py -v`
Expected: 9 passed

- [ ] **Step 5: Commit**

```bash
git add src/research_assistant/daily.py tests/test_daily.py
git commit -m "feat: open_loops model"
```

---

## Task 4: daily.py — 结转 + 时间轴

**Files:**
- Modify: `src/research_assistant/daily.py`
- Modify: `tests/test_daily.py`

- [ ] **Step 1: 追加失败测试**

```python
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
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python3 -m pytest tests/test_daily.py -v`
Expected: FAIL（`AttributeError: ... 'rollover_stale'`）

- [ ] **Step 3: 在 `daily.py` 末尾追加**

```python
def rollover_stale(tz: str) -> list:
    date = state.today_str(tz)
    raw = load_today_raw()
    if not raw or raw.get("date") == date:
        return []
    undone = [it["task"] for it in raw.get("plan", []) if not it["done"]]
    if undone:
        loops = load_loops()
        for task in undone:
            add_loop(loops, task, source="未完成", created=date)
        save_loops(loops)
    return undone


def append_timeline(date: str, line: str) -> None:
    path = timeline_path(date)
    existing = path.read_text(encoding="utf-8") if path.exists() else f"# {date} 时间轴\n"
    state.atomic_write_text(path, existing + line.rstrip("\n") + "\n")
```

- [ ] **Step 4: 跑测试确认通过**

Run: `python3 -m pytest tests/test_daily.py -v`
Expected: 12 passed

- [ ] **Step 5: Commit**

```bash
git add src/research_assistant/daily.py tests/test_daily.py
git commit -m "feat: stale rollover and timeline append"
```

---

## Task 5: CLI today-* 子命令

**Files:**
- Modify: `src/research_assistant/cli.py`
- Modify: `tests/test_cli.py`

- [ ] **Step 1: 追加失败测试到 `tests/test_cli.py`**

```python
import json as _json
from research_assistant import cli, daily


def test_today_set_plan_and_show(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("RESEARCH_HOME", str(tmp_path))
    items = _json.dumps([{"task": "写 intro", "next_action": "开 overleaf"}])
    assert cli.main(["today-set-plan", "--tz", "UTC", "--json", items]) == 0
    capsys.readouterr()
    assert cli.main(["today-show", "--tz", "UTC"]) == 0
    out = _json.loads(capsys.readouterr().out)
    assert out["plan"][0]["task"] == "写 intro"


def test_today_mark_done(tmp_path, monkeypatch):
    monkeypatch.setenv("RESEARCH_HOME", str(tmp_path))
    cli.main(["today-set-plan", "--tz", "UTC", "--json", _json.dumps([{"task": "A"}])])
    assert cli.main(["today-mark-done", "--tz", "UTC", "--id", "t1"]) == 0
    assert daily.load_today("UTC")["plan"][0]["done"] is True


def test_today_mark_done_bad_id_returns_1(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("RESEARCH_HOME", str(tmp_path))
    cli.main(["today-set-plan", "--tz", "UTC", "--json", _json.dumps([{"task": "A"}])])
    assert cli.main(["today-mark-done", "--tz", "UTC", "--id", "tX"]) == 1


def test_today_rollover(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("RESEARCH_HOME", str(tmp_path))
    daily.save_today({"date": "2000-01-01",
                      "plan": [{"id": "t1", "task": "悬着的事", "next_action": "", "done": False}],
                      "unplanned_done": [], "logged": False})
    assert cli.main(["today-rollover", "--tz", "UTC"]) == 0
    assert _json.loads(capsys.readouterr().out) == ["悬着的事"]
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python3 -m pytest tests/test_cli.py -v`
Expected: FAIL（argparse 不认 `today-set-plan`，报 SystemExit / 非 0）

- [ ] **Step 3: 在 `cli.py` 中加入 today-* 命令**

在 `cli.py` 顶部 import 增加 `daily`：

```python
from . import config, state, arxiv, daily
```

在 `main()` 的 `pc.set_defaults(...)` 之后、`args = parser.parse_args(...)` 之前，插入：

```python
    pts = sub.add_parser("today-show")
    pts.add_argument("--tz", default="UTC")
    pts.set_defaults(func=cmd_today_show)

    psp = sub.add_parser("today-set-plan")
    psp.add_argument("--tz", default="UTC")
    psp.add_argument("--json", required=True, help="[{task, next_action}] 的 JSON")
    psp.set_defaults(func=cmd_today_set_plan)

    pmd = sub.add_parser("today-mark-done")
    pmd.add_argument("--tz", default="UTC")
    pmd.add_argument("--id", required=True)
    pmd.set_defaults(func=cmd_today_mark_done)

    pau = sub.add_parser("today-add-unplanned")
    pau.add_argument("--tz", default="UTC")
    pau.add_argument("--text", required=True)
    pau.set_defaults(func=cmd_today_add_unplanned)

    plog = sub.add_parser("today-log")
    plog.add_argument("--tz", default="UTC")
    plog.set_defaults(func=cmd_today_log)

    pro = sub.add_parser("today-rollover")
    pro.add_argument("--tz", default="UTC")
    pro.set_defaults(func=cmd_today_rollover)
```

在文件中（`cmd_commit` 之后）加入这些函数：

```python
def cmd_today_show(args) -> int:
    print(json.dumps(daily.load_today(args.tz), ensure_ascii=False, indent=2))
    return 0


def cmd_today_set_plan(args) -> int:
    items = json.loads(args.json)
    today = daily.load_today(args.tz)
    daily.set_plan(today, items)
    daily.save_today(today)
    return 0


def cmd_today_mark_done(args) -> int:
    today = daily.load_today(args.tz)
    try:
        daily.mark_done(today, args.id)
    except KeyError:
        print(f"no such plan item: {args.id}", file=sys.stderr)
        return 1
    daily.save_today(today)
    return 0


def cmd_today_add_unplanned(args) -> int:
    today = daily.load_today(args.tz)
    daily.add_unplanned(today, args.text)
    daily.save_today(today)
    return 0


def cmd_today_log(args) -> int:
    today = daily.load_today(args.tz)
    daily.mark_logged(today)
    daily.save_today(today)
    return 0


def cmd_today_rollover(args) -> int:
    moved = daily.rollover_stale(args.tz)
    print(json.dumps(moved, ensure_ascii=False))
    return 0
```

- [ ] **Step 4: 跑测试确认通过**

Run: `python3 -m pytest tests/test_cli.py -v`
Expected: 原 3 + 新 4 = 7 passed

- [ ] **Step 5: Commit**

```bash
git add src/research_assistant/cli.py tests/test_cli.py
git commit -m "feat: today-* CLI commands"
```

---

## Task 6: CLI loops-* / timeline-append 子命令

**Files:**
- Modify: `src/research_assistant/cli.py`
- Modify: `tests/test_cli.py`

- [ ] **Step 1: 追加失败测试**

```python
def test_loops_add_and_list(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("RESEARCH_HOME", str(tmp_path))
    assert cli.main(["loops-add", "--tz", "UTC", "--desc", "回审稿人邮件", "--source", "碎念"]) == 0
    capsys.readouterr()
    assert cli.main(["loops-list"]) == 0
    loops = _json.loads(capsys.readouterr().out)
    assert loops[0]["desc"] == "回审稿人邮件"
    assert loops[0]["id"] == "o1"
    assert loops[0]["status"] == "open"


def test_timeline_append(tmp_path, monkeypatch):
    monkeypatch.setenv("RESEARCH_HOME", str(tmp_path))
    assert cli.main(["timeline-append", "--date", "2026-05-30", "--text", "09:30 写 intro ✅"]) == 0
    assert "写 intro ✅" in daily.timeline_path("2026-05-30").read_text(encoding="utf-8")
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python3 -m pytest tests/test_cli.py -v`
Expected: FAIL（argparse 不认 `loops-add`）

- [ ] **Step 3: 在 `main()` 注册区追加**

```python
    pll = sub.add_parser("loops-list")
    pll.set_defaults(func=cmd_loops_list)

    pla = sub.add_parser("loops-add")
    pla.add_argument("--tz", default="UTC")
    pla.add_argument("--desc", required=True)
    pla.add_argument("--source", required=True)
    pla.add_argument("--due", default=None)
    pla.set_defaults(func=cmd_loops_add)

    pta = sub.add_parser("timeline-append")
    pta.add_argument("--tz", default="UTC")
    pta.add_argument("--date", default=None)
    pta.add_argument("--text", required=True)
    pta.set_defaults(func=cmd_timeline_append)
```

并加入函数：

```python
def cmd_loops_list(args) -> int:
    print(json.dumps(daily.load_loops(), ensure_ascii=False, indent=2))
    return 0


def cmd_loops_add(args) -> int:
    loops = daily.load_loops()
    daily.add_loop(loops, args.desc, source=args.source,
                   created=state.today_str(args.tz), due=args.due)
    daily.save_loops(loops)
    return 0


def cmd_timeline_append(args) -> int:
    date = args.date or state.today_str(args.tz)
    daily.append_timeline(date, args.text)
    return 0
```

- [ ] **Step 4: 跑测试确认通过**

Run: `python3 -m pytest tests -q`
Expected: 全量全绿（Plan 1 的 22 + 本计划新增）

- [ ] **Step 5: Commit**

```bash
git add src/research_assistant/cli.py tests/test_cli.py
git commit -m "feat: loops and timeline CLI commands"
```

---

## Task 7: 晨间规划技能 `morning-plan`

**Files:**
- Create: `pack/skills/research/morning-plan/SKILL.md`

- [ ] **Step 1: 写技能**

```markdown
---
name: morning-plan
description: 每天早上帮用户定 1-3 件聚焦任务，拆到下一个最小动作，写进 today.json 并推送飞书。cron 触发。
version: 1.0.0
platforms: [linux, macos]
metadata:
  hermes:
    tags: [research, planning, adhd]
    category: research
---

## When to Use
- cron 每天早晨触发（默认 08:30）。
- 用户主动说"帮我规划下今天 / 今天干啥"。

## Procedure

1. **结转昨天没做完的**：运行
   ```
   research-assistant today-rollover --tz <prefs.timezone>
   ```
   输出是被结转进开放循环的未完成项（JSON 列表，可能为空）。

2. **看悬着的事**：运行
   ```
   research-assistant loops-list
   ```
   得到 open_loops（含刚结转的 + 以前攒的）。挑出今天值得推进的。

3. **提建议（判断活）**：读 `~/.hermes/research/prefs.yaml` 的 `style`。
   - 给用户摆 **1-3 件**今天最该做的（别贪多，ADHD 友好）。
   - 每件**拆到"下一个最小动作"**（不是"写论文"，是"打开 overleaf 写 intro 第一句"）。
   - 语气按 `style.accountability` 档位（gentle…savage）。

4. **等用户拍板**：把建议发出去（cron 会经飞书 deliver 给用户）。用户确认 / 改动后，把最终计划写入：
   ```
   research-assistant today-set-plan --tz <prefs.timezone> --json '[{"task":"...","next_action":"..."}, ...]'
   ```

5.（可选增强）若已接 `feishucli`：把每件 task 建成飞书任务 / 在日历占块。见仓库 README「可选增强」。

## Pitfalls
- 1-3 件是上限，别摆一长串。
- `--json` 必须是合法 JSON 数组；task 必填、next_action 尽量给。
- 结转/读 loops 失败不致命：照常让用户口述今天计划，再 set-plan。

## Verification
- 干跑：`research-assistant today-rollover` 与 `loops-list` 能跑。
- 端到端：触发后飞书收到"今天聚焦 X 件"，确认后 `today.json` 的 `plan` 被写入。
```

- [ ] **Step 2: 人工核对**：frontmatter 合法；步骤顺序 rollover→loops-list→建议→set-plan；1-3 件上限与 next_action 拆解在。

- [ ] **Step 3: Commit**

```bash
git add pack/skills/research/morning-plan/SKILL.md
git commit -m "feat: morning-plan skill"
```

---

## Task 8: 晚间复盘技能 `evening-review`

**Files:**
- Create: `pack/skills/research/evening-review/SKILL.md`

- [ ] **Step 1: 写技能**

```markdown
---
name: evening-review
description: 每天晚上带用户复盘今天、记时间轴、把没做完的转入开放循环。cron 触发。
version: 1.0.0
platforms: [linux, macos]
metadata:
  hermes:
    tags: [research, review, adhd]
    category: research
---

## When to Use
- cron 每天晚上触发（默认 22:00）。
- 用户主动说"复盘下今天 / 今天总结"。

## Procedure

1. **读今天的计划**：运行
   ```
   research-assistant today-show --tz <prefs.timezone>
   ```
   得到今天的 `plan` 与 `unplanned_done`。

2. **问进展（判断活）**：逐项问"这件做到哪了？"，并问"还干了啥计划外的？"
   - 用户说完成的：`research-assistant today-mark-done --tz <tz> --id <tN>`
   - 计划外做的：`research-assistant today-add-unplanned --tz <tz> --text "..."`
   - 读 `style`：**先夸完成的**（celebrate_wins 为 true 时给庆祝），没完成的**不指责**（语气按 accountability 档）。

3. **记时间轴**：把今天实际发生的，逐条写进时间轴：
   ```
   research-assistant timeline-append --tz <tz> --text "09:30-11:00 写 intro ✅"
   ```

4. **结转没做完的**：对仍未完成、又值得继续的，问"滚到明天还是先记着"，记着的转入开放循环：
   ```
   research-assistant loops-add --tz <tz> --desc "<没做完的事>" --source "未完成"
   ```

5. **收尾**：`research-assistant today-log --tz <tz>`，再给用户一句明天的引子。把复盘小结作为最终回复（cron deliver 飞书）。

5.（可选增强）若已接 `feishucli`：把时间轴同步到飞书日历。见 README「可选增强」。

## Pitfalls
- 没做完 ≠ 指责。先肯定做到的。
- 只有用户确认"要继续"的才进 open_loops，别把所有未完成都一股脑塞进去变噪音。

## Verification
- 干跑：`today-show` / `timeline-append` / `loops-add` 能跑。
- 端到端：触发后飞书收到复盘；`state/timeline/<date>.md` 有内容；未完成项进了 `open_loops.json`。
```

- [ ] **Step 2: 人工核对**：frontmatter 合法；先夸后不指责；只把确认的未完成转 loops。

- [ ] **Step 3: Commit**

```bash
git add pack/skills/research/evening-review/SKILL.md
git commit -m "feat: evening-review skill"
```

---

## Task 9: cron 模板 + install.sh + README 更新

**Files:**
- Modify: `pack/cron/jobs.snippet.json`
- Modify: `install.sh`
- Modify: `README.md`

- [ ] **Step 1: 把 `pack/cron/jobs.snippet.json` 改成数组（含三个任务）**

```json
[
  {
    "schedule": "0 9 * * *",
    "skill": "arxiv-digest",
    "deliver": "feishu",
    "prompt": "运行 arxiv-digest 技能：抓取今天的 arXiv 新论文，狠筛 3-5 篇，写成日报推送给我。"
  },
  {
    "schedule": "30 8 * * *",
    "skill": "morning-plan",
    "deliver": "feishu",
    "prompt": "运行 morning-plan 技能：帮我定今天 1-3 件聚焦任务，拆到下一步。"
  },
  {
    "schedule": "0 22 * * *",
    "skill": "evening-review",
    "deliver": "feishu",
    "prompt": "运行 evening-review 技能：带我复盘今天、记时间轴、把没做完的记下来。"
  }
]
```

- [ ] **Step 2: 改 `install.sh` 的「安装技能」段——复制整个 research 技能目录**

把原来这行：
```bash
cp -r "$REPO/pack/skills/research/arxiv-digest" "$HERMES/skills/research/"
```
换成：
```bash
cp -r "$REPO/pack/skills/research/." "$HERMES/skills/research/"
```

并把末尾 cron 提示改成三条（自然语言注册）：
```bash
echo "    在飞书对 Hermes 说（逐条）："
echo '      "每天早上9点跑 arxiv-digest 技能，结果发飞书"'
echo '      "每天早上8点半跑 morning-plan 技能，结果发飞书"'
echo '      "每天晚上10点跑 evening-review 技能，结果发飞书"'
```

- [ ] **Step 3: 验证脚本语法 + JSON 合法**

Run:
```bash
bash -n install.sh && echo "install.sh OK"
python3 -c "import json; print('jobs OK:', len(json.load(open('pack/cron/jobs.snippet.json'))), 'jobs')"
```
Expected: `install.sh OK` / `jobs OK: 3 jobs`

- [ ] **Step 4: 在 `README.md` 加一节「日循环」**

在「端到端」之后插入：
```markdown
## 日循环（Plan 2）
装好后，每天会自动：
- **08:30 晨间规划** —— 帮你定 1-3 件、拆到下一步，写进 today.json
- **22:00 晚间复盘** —— 复盘今天、记时间轴、把没做完的转入开放循环

手动触发体验：在飞书说"帮我规划下今天" / "复盘下今天"。
状态文件在 `~/.hermes/research/state/`：`today.json`、`open_loops.json`、`timeline/<date>.md`。
```

- [ ] **Step 5: Commit**

```bash
git add pack/cron/jobs.snippet.json install.sh README.md
git commit -m "feat: register morning/evening cron, install all skills, docs"
```

---

## 自检（写计划时已过一遍）

- **Spec 覆盖**：晨间规划 §10① → Task 5/7；晚间复盘+时间轴 §10⑤ → Task 4/5/6/8；today/open_loops/timeline 状态 §9 → Task 2/3/4；style 驱动语气 §8 → Task 1 + 两个技能读 accountability。
- **承接 Plan 1**：复用 `state.*` / `config.Prefs.raw`；不改 SOUL/arxiv/Plan1 测试。
- **占位符**：无 TODO/TBD；每步给真实代码与命令。
- **类型一致**：`today` dict 形状（date/plan[id,task,next_action,done]/unplanned_done/logged）、`loop` dict 形状（id/desc/created/last_nudged/status/due/source）在 daily.py 与 CLI 间一致；CLI 调的就是 daily.py 里定义的函数。
- **留给 Plan 3**：`current_focus`（专注陪伴）、`due_for_nudge` 选择逻辑 + `loops-update` 的 nudged 用法 + 14:00/18:00 巡检 cron。

## 可选增强：feishucli 原生任务 / 日历（本计划不做）
日循环全程经**飞书聊天消息**即可用。把"计划建成飞书任务、时间轴写进飞书日历"作为增强：在 Mac mini 上先 `feishucli --help` 确认建任务/写日历的确切命令，再在 morning-plan / evening-review 技能的「可选增强」步骤里补上对应命令。**接口未确认前不写死命令**，避免装上就坏（同 Plan 1 §14 原则）。

## 待执行时确认
- 各 cron 的注册方式（优先自然语言；`hermes cron list` 看 job）。
- 时区：技能里的 `<prefs.timezone>` 取自 `~/.hermes/research/prefs.yaml`。
