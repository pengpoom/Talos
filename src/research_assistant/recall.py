import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path

from . import daily, focus, projects, state


@dataclass
class MemoryHit:
    source: str
    kind: str
    title: str
    text: str
    date: str | None = None
    score: float = 0.0


_TOKEN_RE = re.compile(r"[A-Za-z0-9_\-]+|[\u4e00-\u9fff]+")


def _tokens(text: str) -> list[str]:
    tokens: list[str] = []
    for match in _TOKEN_RE.finditer(text or ""):
        token = match.group(0).lower()
        tokens.append(token)
        if re.fullmatch(r"[\u4e00-\u9fff]+", token) and len(token) > 2:
            tokens.extend(token[i:i + 2] for i in range(len(token) - 1))
    return list(dict.fromkeys(tokens))


def _date_from_name(path: Path) -> str | None:
    match = re.search(r"\d{4}-\d{2}-\d{2}", path.name)
    return match.group(0) if match else None


def _snippet(text: str, *, max_chars: int = 500) -> str:
    text = " ".join((text or "").split())
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 1].rstrip() + "..."


def _read_jsonl(path: Path) -> list[dict]:
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


def _timeline_items() -> list[MemoryHit]:
    root = state.state_dir() / "timeline"
    if not root.exists():
        return []
    items: list[MemoryHit] = []
    for path in sorted(root.glob("*.md")):
        date = _date_from_name(path)
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            items.append(MemoryHit(
                source=str(path.relative_to(state.state_dir())),
                kind="timeline",
                title=f"{date or path.stem} 时间轴",
                text=line,
                date=date,
            ))
    return items


def _loop_items() -> list[MemoryHit]:
    items: list[MemoryHit] = []
    for loop in daily.load_loops():
        parts = [
            loop.get("desc", ""),
            f"next_action: {loop.get('next_action')}" if loop.get("next_action") else "",
            f"project: {loop.get('project')}" if loop.get("project") else "",
            f"owner: {loop.get('owner')}" if loop.get("owner") else "",
            f"source: {loop.get('source')}" if loop.get("source") else "",
        ]
        title = f"{loop.get('id', 'loop')} {loop.get('desc', '')}".strip()
        items.append(MemoryHit(
            source=str(daily.open_loops_path().relative_to(state.state_dir())),
            kind="open_loop",
            title=title,
            text="; ".join(p for p in parts if p),
            date=loop.get("created"),
        ))
    return items


def _project_items() -> list[MemoryHit]:
    items: list[MemoryHit] = []
    for project in projects.load_projects():
        parts = [
            f"name: {project.get('name')}",
            f"goal: {project.get('goal')}" if project.get("goal") else "",
            f"next_milestone: {project.get('next_milestone')}" if project.get("next_milestone") else "",
            f"domain: {project.get('domain')}" if project.get("domain") else "",
            f"status: {project.get('status')}" if project.get("status") else "",
            f"docs: {', '.join(project.get('docs') or [])}" if project.get("docs") else "",
            f"people: {', '.join(project.get('people') or [])}" if project.get("people") else "",
        ]
        title = f"{project.get('id', 'project')} {project.get('name', '')}".strip()
        items.append(MemoryHit(
            source=str(projects.projects_path().relative_to(state.state_dir())),
            kind="project",
            title=title,
            text="; ".join(p for p in parts if p),
            date=project.get("updated") or project.get("created"),
        ))
    return items


def _focus_items() -> list[MemoryHit]:
    items: list[MemoryHit] = []
    for rec in _read_jsonl(focus.focus_log_path()):
        title = f"专注 {rec.get('task', '')}".strip()
        text = (
            f"task: {rec.get('task', '')}; "
            f"elapsed_min: {rec.get('elapsed_min', 0)}; "
            f"started: {rec.get('started', '')}; "
            f"ended: {rec.get('ended', '')}"
        )
        if rec.get("project"):
            text += f"; project: {rec['project']}"
        items.append(MemoryHit(
            source=str(focus.focus_log_path().relative_to(state.state_dir())),
            kind="focus",
            title=title,
            text=text,
            date=(rec.get("ended") or rec.get("started") or "")[:10] or None,
        ))
    return items


def _paper_digest_items() -> list[MemoryHit]:
    root = state.papers_dir()
    if not root.exists():
        return []
    items: list[MemoryHit] = []
    for path in sorted(root.glob("digest-*.md")):
        text = path.read_text(encoding="utf-8")
        date = _date_from_name(path)
        title = ""
        for line in text.splitlines():
            line = line.strip("# ").strip()
            if line:
                title = line
                break
        items.append(MemoryHit(
            source=str(path.relative_to(state.state_dir())),
            kind="paper_digest",
            title=title or path.stem,
            text=_snippet(text, max_chars=900),
            date=date,
        ))
    return items


def collect_memory() -> list[MemoryHit]:
    return [
        *_timeline_items(),
        *_loop_items(),
        *_project_items(),
        *_focus_items(),
        *_paper_digest_items(),
    ]


def _score(item: MemoryHit, query_tokens: list[str]) -> float:
    if not query_tokens:
        return 0.0
    title = (item.title or "").lower()
    text = (item.text or "").lower()
    kind = (item.kind or "").lower()
    score = 0.0
    for token in query_tokens:
        if token in title:
            score += 5.0
        if token in kind:
            score += 2.0
        count = text.count(token)
        if count:
            score += min(count, 5) * 1.0
    if item.kind in {"open_loop", "project"}:
        score *= 1.15
    return score


def search(query: str, *, limit: int = 8) -> list[MemoryHit]:
    query_tokens = _tokens(query)
    hits = []
    for item in collect_memory():
        score = _score(item, query_tokens)
        if score <= 0:
            continue
        hit = MemoryHit(**asdict(item))
        hit.score = round(score, 3)
        hit.text = _snippet(hit.text)
        hits.append(hit)
    hits.sort(key=lambda h: (-h.score, h.date or "", h.source, h.title))
    return hits[:limit]


def to_jsonable(items: list[MemoryHit]) -> list[dict]:
    return [asdict(item) for item in items]
