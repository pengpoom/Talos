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
