import json
import os
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


def research_home() -> Path:
    return Path(os.environ.get("RESEARCH_HOME", Path.home() / ".hermes" / "research"))


def state_dir() -> Path:
    return research_home() / "state"


def papers_dir() -> Path:
    return state_dir() / "papers"


def seen_path() -> Path:
    return papers_dir() / "seen.jsonl"


def digest_path(date: str) -> Path:
    return papers_dir() / f"digest-{date}.md"


def today_str(tz: str) -> str:
    return datetime.now(ZoneInfo(tz)).strftime("%Y-%m-%d")


def now_iso(tz: str) -> str:
    return datetime.now(ZoneInfo(tz)).strftime("%Y-%m-%dT%H:%M")


def atomic_write_text(path, text: str) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


def atomic_write_json(path, obj) -> None:
    atomic_write_text(path, json.dumps(obj, ensure_ascii=False, indent=2))


def read_json(path, default):
    path = Path(path)
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, ValueError):
        shutil.copy(path, path.with_suffix(path.suffix + ".corrupt"))
        return default


def load_seen(path) -> set:
    path = Path(path)
    if not path.exists():
        return set()
    ids = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
            ids.add(obj["id"])
        except (json.JSONDecodeError, KeyError, ValueError):
            continue
    return ids


def append_seen(path, ids, date: str) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        for _id in ids:
            f.write(json.dumps({"id": _id, "date": date}, ensure_ascii=False) + "\n")
