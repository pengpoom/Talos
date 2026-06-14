from . import daily


def projects_path():
    from . import state
    return state.state_dir() / "projects.json"


_PROJECT_DEFAULTS = {"domain": "research", "status": "active", "goal": "",
                     "next_milestone": None, "docs": [], "people": [], "updated": None}


def load_projects() -> list:
    from . import state
    projects = state.read_json(projects_path(), default=[])
    for p in projects:
        for k, v in _PROJECT_DEFAULTS.items():
            p.setdefault(k, list(v) if isinstance(v, list) else v)
    return projects


def save_projects(projects: list) -> None:
    from . import state
    state.atomic_write_json(projects_path(), projects)


def _next_id(items: list, prefix: str) -> str:
    nums = [int(i["id"][len(prefix):]) for i in items
            if i.get("id", "").startswith(prefix) and i["id"][len(prefix):].isdigit()]
    return f"{prefix}{(max(nums) if nums else 0) + 1}"


def add_project(projects: list, name: str, *, created: str, domain: str = "research",
                goal: str = "", status: str = "active", next_milestone=None) -> dict:
    p = {"id": _next_id(projects, "p"), "name": name, "domain": domain,
         "status": status, "goal": goal, "next_milestone": next_milestone,
         "docs": [], "people": [], "created": created, "updated": created}
    projects.append(p)
    return p


def find_project(projects: list, key: str):
    if not key:
        return None
    k = key.strip().lower()
    for p in projects:
        if p["id"].lower() == k or p["name"].strip().lower() == k:
            return p
    return None


def update_project(projects: list, key: str, *, updated: str, name=None, status=None,
                   goal=None, next_milestone=None, domain=None,
                   add_doc=None, add_person=None) -> dict:
    p = find_project(projects, key)
    if p is None:
        raise KeyError(key)
    if name is not None:
        p["name"] = name
    if status is not None:
        p["status"] = status
    if goal is not None:
        p["goal"] = goal
    if next_milestone is not None:
        p["next_milestone"] = next_milestone
    if domain is not None:
        p["domain"] = domain
    if add_doc:
        p.setdefault("docs", [])
        if add_doc not in p["docs"]:
            p["docs"].append(add_doc)
    if add_person:
        p.setdefault("people", [])
        if add_person not in p["people"]:
            p["people"].append(add_person)
    p["updated"] = updated
    return p


def _names_for(key: str, rec) -> set:
    names = {key.strip().lower()} if key else set()
    if rec:
        names |= {rec["id"].lower(), rec["name"].strip().lower()}
    return names


def _matches(value, names: set) -> bool:
    return (value or "").strip().lower() in names if value else False


def project_status(key: str, projects: list, loops: list, focus_log: list, today: str) -> dict:
    rec = find_project(projects, key)
    names = _names_for(key, rec)
    matched = [l for l in loops if _matches(l.get("project"), names)]
    open_loops = [l for l in matched if l.get("status") == "open"]
    open_loops.sort(key=lambda l: (not daily.is_overdue(l, today),
                                   daily._PRIORITY_RANK.get(l.get("priority", "medium"), 2),
                                   l.get("created", "")))
    overdue = [l for l in open_loops if daily.is_overdue(l, today)]
    done = [l for l in matched if l.get("status") == "done"]
    fmatched = [r for r in focus_log if _matches(r.get("project"), names)]
    focus_min = sum(int(r.get("elapsed_min", 0)) for r in fmatched)
    next_actions = [{"desc": l["desc"], "next_action": l.get("next_action"),
                     "owner": l.get("owner"), "priority": l.get("priority"),
                     "overdue": daily.is_overdue(l, today)} for l in open_loops]
    return {"project": rec, "key": key,
            "open_count": len(open_loops), "overdue_count": len(overdue),
            "done_count": len(done),
            "focus": {"sessions": len(fmatched), "total_min": focus_min},
            "next_actions": next_actions,
            "open_loops": open_loops, "done_loops": done}
