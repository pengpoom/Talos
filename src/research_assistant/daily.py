from datetime import datetime
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


_LOOP_DEFAULTS = {"domain": "research", "next_action": None,
                  "priority": "medium", "project": None, "owner": None}
_PRIORITY_RANK = {"urgent": 0, "high": 1, "medium": 2, "low": 3}


def load_loops() -> list:
    loops = state.read_json(open_loops_path(), default=[])
    for loop in loops:
        for k, v in _LOOP_DEFAULTS.items():
            loop.setdefault(k, v)
    return loops


def save_loops(loops: list) -> None:
    state.atomic_write_json(open_loops_path(), loops)


def _next_id(items: list, prefix: str) -> str:
    nums = [int(i["id"][len(prefix):]) for i in items
            if i.get("id", "").startswith(prefix) and i["id"][len(prefix):].isdigit()]
    return f"{prefix}{(max(nums) if nums else 0) + 1}"


def add_loop(loops: list, desc: str, *, source: str, created: str, due=None,
             domain: str = "research", next_action=None, priority: str = "medium",
             project=None, owner=None) -> dict:
    loop = {"id": _next_id(loops, "o"), "desc": desc, "created": created,
            "last_nudged": None, "status": "open", "due": due, "source": source,
            "domain": domain, "next_action": next_action, "priority": priority,
            "project": project, "owner": owner}
    loops.append(loop)
    return loop


def update_loop(loops: list, loop_id: str, *, status=None, nudged_date=None,
                next_action=None, priority=None, domain=None, project=None, owner=None) -> dict:
    for loop in loops:
        if loop["id"] == loop_id:
            if status:
                loop["status"] = status
            if nudged_date:
                loop["last_nudged"] = nudged_date
            if next_action is not None:
                loop["next_action"] = next_action
            if priority is not None:
                loop["priority"] = priority
            if domain is not None:
                loop["domain"] = domain
            if project is not None:
                loop["project"] = project
            if owner is not None:
                loop["owner"] = owner
            return loop
    raise KeyError(loop_id)


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


def _days_between(a: str, b: str) -> int:
    fmt = "%Y-%m-%d"
    return (datetime.strptime(b, fmt).date() - datetime.strptime(a, fmt).date()).days


def is_overdue(loop: dict, today: str) -> bool:
    due = loop.get("due")
    return bool(due) and due <= today


def due_for_nudge(loops: list, today: str, *, cadence_days: int = 1) -> list:
    out = [l for l in loops
           if l.get("status") == "open"
           and (l.get("last_nudged") is None
                or _days_between(l["last_nudged"], today) >= cadence_days)]
    out.sort(key=lambda l: (not is_overdue(l, today),
                            _PRIORITY_RANK.get(l.get("priority", "medium"), 2),
                            l.get("created", "")))
    return out
