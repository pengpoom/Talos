import json
from datetime import datetime
from pathlib import Path
from . import state


def focus_path() -> Path:
    return state.state_dir() / "focus.json"


def load_focus():
    return state.read_json(focus_path(), default=None)


def start_focus(task: str, *, started: str, planned_min=None) -> dict:
    sess = {"active": True, "task": task, "started": started,
            "planned_min": planned_min, "ended": None}
    state.atomic_write_json(focus_path(), sess)
    return sess


def focus_log_path() -> Path:
    return state.state_dir() / "focus_log.jsonl"


def append_focus_log(record: dict) -> None:
    path = focus_log_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def load_focus_log() -> list:
    path = focus_log_path()
    if not path.exists():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except (json.JSONDecodeError, ValueError):
            continue
    return out


def focus_stats(log: list, *, since: str = None) -> dict:
    items = [r for r in log if since is None or r.get("ended", "") >= since]
    total = sum(int(r.get("elapsed_min", 0)) for r in items)
    return {"count": len(items), "total_min": total}


def end_focus(*, ended: str) -> dict:
    sess = load_focus()
    if not sess or not sess.get("active"):
        raise RuntimeError("no active focus session")
    sess["active"] = False
    sess["ended"] = ended
    sess["elapsed_min"] = elapsed_minutes(sess["started"], ended)
    state.atomic_write_json(focus_path(), sess)
    append_focus_log({"task": sess["task"], "started": sess["started"],
                      "ended": ended, "elapsed_min": sess["elapsed_min"]})
    return sess


def elapsed_minutes(started: str, now: str) -> int:
    fmt = "%Y-%m-%dT%H:%M"
    delta = datetime.strptime(now, fmt) - datetime.strptime(started, fmt)
    return max(0, int(delta.total_seconds() // 60))
