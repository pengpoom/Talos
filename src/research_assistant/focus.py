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


def end_focus(*, ended: str) -> dict:
    sess = load_focus()
    if not sess or not sess.get("active"):
        raise RuntimeError("no active focus session")
    sess["active"] = False
    sess["ended"] = ended
    state.atomic_write_json(focus_path(), sess)
    return sess


def elapsed_minutes(started: str, now: str) -> int:
    fmt = "%Y-%m-%dT%H:%M"
    delta = datetime.strptime(now, fmt) - datetime.strptime(started, fmt)
    return int(delta.total_seconds() // 60)
