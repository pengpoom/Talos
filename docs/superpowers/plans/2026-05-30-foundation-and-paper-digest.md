# 基础设施 + 论文日报 实施计划 (Plan 1)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 Hermes 之上跑通"每天定时抓取 → 去重 → 交给 agent 狠筛 → 推送飞书"的论文日报闭环，并打好后续功能共用的基础设施（配置 / 状态 / SOUL 人设）。

**Architecture:** 混合方案。机械活（arXiv 抓取、去重、状态读写）= 可单测的 Python 包 `research_assistant`；判断活（相关性排序、摘要、措辞）= `arxiv-digest` 技能里的 agent 推理。两者通过 `research-assistant fetch` / `commit` 两个 CLI 子命令衔接，状态落盘到 `~/.hermes/research/state/`。

**Tech Stack:** Python ≥3.10、`requests`、`feedparser`、`PyYAML`、`pytest`；Hermes 技能(SKILL.md) + cron + 飞书 gateway；`feishucli`(已装)。

> **关于 git：** 你说先不用 git。计划里每个任务末尾保留了 `git commit` 作为**检查点**——执行时如果还没起仓库，把它当作"跑全量测试 + 停下来 review"的节点即可；**强烈建议执行阶段开个本地 git**（这项目要开源，迟早要），那样 commit 步骤直接可用。

---

## 文件结构（本计划新建/修改）

```
hermes-poss/
├── pyproject.toml                         # Create — 包定义、依赖、pytest、console_script
├── src/research_assistant/
│   ├── __init__.py                        # Create
│   ├── config.py                          # Create — 读 prefs.yaml
│   ├── state.py                           # Create — 路径/原子读写/日期/seen 去重
│   ├── arxiv.py                           # Create — 查询/抓取/解析/去重
│   └── cli.py                             # Create — fetch / commit 两个子命令
├── tests/
│   ├── __init__.py                        # Create
│   ├── fixtures/arxiv_sample.xml          # Create — 解析用样例
│   ├── test_config.py                     # Create
│   ├── test_state.py                      # Create
│   ├── test_arxiv.py                      # Create
│   └── test_cli.py                        # Create
├── pack/                                  # 可分发的"包"
│   ├── SOUL.snippet.md                    # Create — 科研搭子人设
│   ├── prefs.example.yaml                 # Create — 配置模板
│   ├── skills/research/arxiv-digest/SKILL.md   # Create — 论文日报技能
│   └── cron/jobs.snippet.json             # Create — 定时任务模板
├── install.sh                             # Create — 把 pack 装进 ~/.hermes/
└── README.md                              # Create — 安装 + 端到端验证
```

**职责边界**：`config.py` 只管读配置；`state.py` 只管落盘与日期；`arxiv.py` 只管和 arXiv 打交道；`cli.py` 只做编排 + 进出参数。互不越界，便于单测。

---

## Task 1: 项目骨架与工具链

**Files:**
- Create: `pyproject.toml`
- Create: `src/research_assistant/__init__.py`
- Create: `tests/__init__.py`

- [ ] **Step 1: 写 `pyproject.toml`**

```toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[project]
name = "research-assistant"
version = "0.1.0"
description = "Hermes 科研搭子 — 基础设施与论文日报"
requires-python = ">=3.10"
dependencies = [
    "requests>=2.28",
    "feedparser>=6.0",
    "PyYAML>=6.0",
    "tzdata>=2024.1",
]

[project.optional-dependencies]
dev = ["pytest>=7.0"]

[project.scripts]
research-assistant = "research_assistant.cli:main"

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

- [ ] **Step 2: 建空包与测试目录**

`src/research_assistant/__init__.py`：

```python
__version__ = "0.1.0"
```

`tests/__init__.py`：留空文件即可。

- [ ] **Step 3: 安装并确认 pytest 能跑**

Run: `pip install -e ".[dev]" && pytest -q`
Expected: 安装成功；pytest 输出 `no tests ran`（0 个测试，退出码 5 或 0 均可，关键是无导入错误）。

- [ ] **Step 4: Commit**

```bash
git add pyproject.toml src/research_assistant/__init__.py tests/__init__.py
git commit -m "chore: project skeleton and tooling"
```

---

## Task 2: 配置加载 `config.py`

**Files:**
- Create: `src/research_assistant/config.py`
- Test: `tests/test_config.py`

- [ ] **Step 1: 写失败测试**

```python
from pathlib import Path
import pytest
from research_assistant.config import load_prefs

def _write(tmp_path: Path, text: str) -> Path:
    p = tmp_path / "prefs.yaml"
    p.write_text(text, encoding="utf-8")
    return p

def test_load_prefs_reads_arxiv_and_timezone(tmp_path):
    p = _write(tmp_path, """
timezone: Asia/Shanghai
arxiv:
  categories: [cs.RO, cs.LG]
  keywords: ["robotic manipulation", "LLM agent"]
  max_per_day: 5
""")
    prefs = load_prefs(p)
    assert prefs.timezone == "Asia/Shanghai"
    assert prefs.arxiv.categories == ["cs.RO", "cs.LG"]
    assert prefs.arxiv.keywords == ["robotic manipulation", "LLM agent"]
    assert prefs.arxiv.max_per_day == 5

def test_load_prefs_defaults_when_fields_missing(tmp_path):
    p = _write(tmp_path, "arxiv: {}\n")
    prefs = load_prefs(p)
    assert prefs.timezone == "UTC"
    assert prefs.arxiv.categories == []
    assert prefs.arxiv.max_per_day == 5

def test_load_prefs_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_prefs(tmp_path / "nope.yaml")
```

- [ ] **Step 2: 跑测试确认失败**

Run: `pytest tests/test_config.py -v`
Expected: FAIL（`ModuleNotFoundError: research_assistant.config`）

- [ ] **Step 3: 实现 `config.py`**

```python
from dataclasses import dataclass
from pathlib import Path
import yaml


@dataclass
class ArxivPrefs:
    categories: list[str]
    keywords: list[str]
    max_per_day: int = 5


@dataclass
class Prefs:
    timezone: str
    arxiv: ArxivPrefs
    raw: dict


def load_prefs(path) -> Prefs:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"prefs not found: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    az = data.get("arxiv") or {}
    arxiv = ArxivPrefs(
        categories=list(az.get("categories", [])),
        keywords=list(az.get("keywords", [])),
        max_per_day=int(az.get("max_per_day", 5)),
    )
    return Prefs(timezone=data.get("timezone", "UTC"), arxiv=arxiv, raw=data)
```

- [ ] **Step 4: 跑测试确认通过**

Run: `pytest tests/test_config.py -v`
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add src/research_assistant/config.py tests/test_config.py
git commit -m "feat: prefs.yaml loader"
```

---

## Task 3: 状态存储核心 `state.py`（路径 / 原子读写 / 日期 / 坏文件恢复）

**Files:**
- Create: `src/research_assistant/state.py`
- Test: `tests/test_state.py`

- [ ] **Step 1: 写失败测试**

```python
import json
from pathlib import Path
import research_assistant.state as state

def test_research_home_from_env(tmp_path, monkeypatch):
    monkeypatch.setenv("RESEARCH_HOME", str(tmp_path))
    assert state.research_home() == tmp_path
    assert state.seen_path() == tmp_path / "state" / "papers" / "seen.jsonl"
    assert state.digest_path("2026-05-30") == tmp_path / "state" / "papers" / "digest-2026-05-30.md"

def test_atomic_write_and_read_json(tmp_path, monkeypatch):
    monkeypatch.setenv("RESEARCH_HOME", str(tmp_path))
    target = tmp_path / "state" / "today.json"
    state.atomic_write_json(target, {"a": 1})
    assert state.read_json(target, default=None) == {"a": 1}

def test_read_json_missing_returns_default(tmp_path):
    assert state.read_json(tmp_path / "missing.json", default=[]) == []

def test_read_json_corrupt_backs_up_and_returns_default(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("{not json", encoding="utf-8")
    assert state.read_json(bad, default={}) == {}
    assert (tmp_path / "bad.json.corrupt").exists()

def test_today_str_uses_timezone():
    s = state.today_str("Asia/Shanghai")
    assert len(s) == 10 and s[4] == "-" and s[7] == "-"
```

- [ ] **Step 2: 跑测试确认失败**

Run: `pytest tests/test_state.py -v`
Expected: FAIL（`ModuleNotFoundError` 或 `AttributeError`）

- [ ] **Step 3: 实现 `state.py`（核心部分）**

```python
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
```

- [ ] **Step 4: 跑测试确认通过**

Run: `pytest tests/test_state.py -v`
Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add src/research_assistant/state.py tests/test_state.py
git commit -m "feat: state store core (paths, atomic io, dates)"
```

---

## Task 4: 状态存储 `seen.jsonl` 去重

**Files:**
- Modify: `src/research_assistant/state.py`
- Modify: `tests/test_state.py`

- [ ] **Step 1: 追加失败测试到 `tests/test_state.py`**

```python
def test_load_seen_missing_returns_empty(tmp_path):
    assert state.load_seen(tmp_path / "seen.jsonl") == set()

def test_append_then_load_seen(tmp_path):
    p = tmp_path / "seen.jsonl"
    state.append_seen(p, ["id-a", "id-b"], "2026-05-30")
    state.append_seen(p, ["id-c"], "2026-05-31")
    assert state.load_seen(p) == {"id-a", "id-b", "id-c"}

def test_load_seen_skips_corrupt_lines(tmp_path):
    p = tmp_path / "seen.jsonl"
    p.write_text('{"id": "ok"}\nGARBAGE\n{"nope": 1}\n', encoding="utf-8")
    assert state.load_seen(p) == {"ok"}
```

- [ ] **Step 2: 跑测试确认失败**

Run: `pytest tests/test_state.py -v`
Expected: FAIL（`AttributeError: module 'research_assistant.state' has no attribute 'load_seen'`）

- [ ] **Step 3: 在 `state.py` 末尾追加实现**

```python
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
```

- [ ] **Step 4: 跑测试确认通过**

Run: `pytest tests/test_state.py -v`
Expected: 8 passed

- [ ] **Step 5: Commit**

```bash
git add src/research_assistant/state.py tests/test_state.py
git commit -m "feat: seen.jsonl dedup store"
```

---

## Task 5: arXiv 查询构造 + 抓取（带重试）

**Files:**
- Create: `src/research_assistant/arxiv.py`
- Test: `tests/test_arxiv.py`

- [ ] **Step 1: 写失败测试**

```python
import pytest
from research_assistant.arxiv import build_query, fetch_raw

def test_build_query_combines_categories_and_keywords():
    q = build_query(["cs.RO", "cs.LG"], ["robotic manipulation"])
    assert q == '(cat:cs.RO OR cat:cs.LG) AND (all:"robotic manipulation")'

def test_build_query_categories_only():
    assert build_query(["eess.SY"], []) == "(cat:eess.SY)"

class _Resp:
    def __init__(self, text, ok=True):
        self.text = text
        self._ok = ok
    def raise_for_status(self):
        if not self._ok:
            raise RuntimeError("http 500")

def test_fetch_raw_returns_body():
    calls = []
    def fake_get(url, params=None, timeout=None):
        calls.append((url, params))
        return _Resp("<feed/>")
    body = fetch_raw("cat:cs.RO", 10, http_get=fake_get)
    assert body == "<feed/>"
    assert calls[0][1]["search_query"] == "cat:cs.RO"
    assert calls[0][1]["max_results"] == 10

def test_fetch_raw_retries_then_raises():
    attempts = {"n": 0}
    def flaky_get(url, params=None, timeout=None):
        attempts["n"] += 1
        raise ConnectionError("boom")
    with pytest.raises(RuntimeError):
        fetch_raw("cat:cs.RO", 10, http_get=flaky_get, retries=3, backoff=0)
    assert attempts["n"] == 3
```

- [ ] **Step 2: 跑测试确认失败**

Run: `pytest tests/test_arxiv.py -v`
Expected: FAIL（`ModuleNotFoundError: research_assistant.arxiv`）

- [ ] **Step 3: 实现 `arxiv.py`（查询 + 抓取部分）**

```python
import time
from dataclasses import dataclass
import requests

ARXIV_API = "http://export.arxiv.org/api/query"


@dataclass
class Paper:
    id: str
    title: str
    summary: str
    authors: list[str]
    link: str
    published: str


def build_query(categories: list[str], keywords: list[str]) -> str:
    parts = []
    if categories:
        parts.append("(" + " OR ".join(f"cat:{c}" for c in categories) + ")")
    if keywords:
        parts.append("(" + " OR ".join(f'all:"{k}"' for k in keywords) + ")")
    return " AND ".join(parts)


def fetch_raw(query: str, max_results: int, *, http_get=requests.get,
              retries: int = 3, backoff: float = 2.0) -> str:
    params = {
        "search_query": query,
        "start": 0,
        "max_results": max_results,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
    }
    last_exc = None
    for attempt in range(retries):
        try:
            resp = http_get(ARXIV_API, params=params, timeout=30)
            resp.raise_for_status()
            return resp.text
        except Exception as e:  # noqa: BLE001
            last_exc = e
            if attempt < retries - 1 and backoff:
                time.sleep(backoff * (attempt + 1))
    raise RuntimeError(f"arXiv fetch failed after {retries} attempts: {last_exc}")
```

- [ ] **Step 4: 跑测试确认通过**

Run: `pytest tests/test_arxiv.py -v`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add src/research_assistant/arxiv.py tests/test_arxiv.py
git commit -m "feat: arxiv query builder and fetch with retry"
```

---

## Task 6: arXiv 解析 + 去重 + 候选编排

**Files:**
- Create: `tests/fixtures/arxiv_sample.xml`
- Modify: `src/research_assistant/arxiv.py`
- Modify: `tests/test_arxiv.py`

- [ ] **Step 1: 建解析样例 `tests/fixtures/arxiv_sample.xml`**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <id>http://arxiv.org/abs/2401.00001v1</id>
    <title>A Sample Paper on Robotic Manipulation</title>
    <summary>We present a method for robotic manipulation using LLMs.</summary>
    <published>2024-01-01T00:00:00Z</published>
    <author><name>Alice Smith</name></author>
    <author><name>Bob Jones</name></author>
    <link href="http://arxiv.org/abs/2401.00001v1" rel="alternate" type="text/html"/>
  </entry>
  <entry>
    <id>http://arxiv.org/abs/2401.00002v1</id>
    <title>Model Predictive Control for Quadrotors</title>
    <summary>An MPC approach for agile quadrotor flight.</summary>
    <published>2024-01-02T00:00:00Z</published>
    <author><name>Carol White</name></author>
    <link href="http://arxiv.org/abs/2401.00002v1" rel="alternate" type="text/html"/>
  </entry>
</feed>
```

- [ ] **Step 2: 追加失败测试到 `tests/test_arxiv.py`**

```python
from pathlib import Path
from research_assistant.arxiv import parse_entries, dedup, fetch_candidates
from research_assistant.config import ArxivPrefs

FIXTURE = Path(__file__).parent / "fixtures" / "arxiv_sample.xml"

def test_parse_entries():
    papers = parse_entries(FIXTURE.read_text(encoding="utf-8"))
    assert len(papers) == 2
    assert papers[0].id == "http://arxiv.org/abs/2401.00001v1"
    assert papers[0].title == "A Sample Paper on Robotic Manipulation"
    assert papers[0].authors == ["Alice Smith", "Bob Jones"]
    assert "robotic manipulation" in papers[0].summary.lower()

def test_parse_entries_empty_feed():
    assert parse_entries("<feed xmlns='http://www.w3.org/2005/Atom'/>") == []

def test_dedup_filters_seen():
    papers = parse_entries(FIXTURE.read_text(encoding="utf-8"))
    out = dedup(papers, {"http://arxiv.org/abs/2401.00001v1"})
    assert [p.id for p in out] == ["http://arxiv.org/abs/2401.00002v1"]

def test_fetch_candidates_dedups(monkeypatch):
    def fake_get(url, params=None, timeout=None):
        class R:
            text = FIXTURE.read_text(encoding="utf-8")
            def raise_for_status(self): pass
        return R()
    prefs = ArxivPrefs(categories=["cs.RO"], keywords=[], max_per_day=5)
    out = fetch_candidates(prefs, {"http://arxiv.org/abs/2401.00002v1"}, http_get=fake_get)
    assert [p.id for p in out] == ["http://arxiv.org/abs/2401.00001v1"]
```

- [ ] **Step 3: 跑测试确认失败**

Run: `pytest tests/test_arxiv.py -v`
Expected: FAIL（`ImportError: cannot import name 'parse_entries'`）

- [ ] **Step 4: 在 `arxiv.py` 末尾追加实现**

```python
import feedparser


def parse_entries(atom_xml: str) -> list[Paper]:
    feed = feedparser.parse(atom_xml)
    papers = []
    for e in feed.entries:
        papers.append(Paper(
            id=e.get("id", ""),
            title=e.get("title", "").strip().replace("\n", " "),
            summary=e.get("summary", "").strip().replace("\n", " "),
            authors=[a.get("name", "") for a in e.get("authors", [])],
            link=e.get("link", e.get("id", "")),
            published=e.get("published", ""),
        ))
    return papers


def dedup(papers: list[Paper], seen: set) -> list[Paper]:
    return [p for p in papers if p.id not in seen]


def fetch_candidates(arxiv_prefs, seen: set, *, http_get=requests.get,
                     candidate_pool: int = 50) -> list[Paper]:
    query = build_query(arxiv_prefs.categories, arxiv_prefs.keywords)
    xml = fetch_raw(query, candidate_pool, http_get=http_get)
    return dedup(parse_entries(xml), seen)
```

> 注意：`import feedparser` 放文件顶部更规范；这里为分步清晰追加在末尾，执行时把它挪到顶部 import 区。

- [ ] **Step 5: 跑测试确认通过**

Run: `pytest tests/test_arxiv.py -v`
Expected: 8 passed

- [ ] **Step 6: Commit**

```bash
git add src/research_assistant/arxiv.py tests/test_arxiv.py tests/fixtures/arxiv_sample.xml
git commit -m "feat: arxiv parse, dedup, fetch_candidates"
```

---

## Task 7: CLI `fetch` / `commit`

**Files:**
- Create: `src/research_assistant/cli.py`
- Test: `tests/test_cli.py`

- [ ] **Step 1: 写失败测试**

```python
import json
from pathlib import Path
import pytest
from research_assistant import cli, arxiv

FIXTURE = Path(__file__).parent / "fixtures" / "arxiv_sample.xml"

def _patch_fetch(monkeypatch, papers):
    monkeypatch.setattr(arxiv, "fetch_candidates", lambda *a, **k: papers)

def test_fetch_prints_json(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("RESEARCH_HOME", str(tmp_path))
    prefs = tmp_path / "prefs.yaml"
    prefs.write_text("timezone: UTC\narxiv:\n  categories: [cs.RO]\n", encoding="utf-8")
    _patch_fetch(monkeypatch, [arxiv.Paper("id1", "T", "S", ["A"], "L", "P")])
    rc = cli.main(["fetch", "--prefs", str(prefs)])
    out = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert out[0]["id"] == "id1"

def test_fetch_returns_nonzero_on_failure(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("RESEARCH_HOME", str(tmp_path))
    prefs = tmp_path / "prefs.yaml"
    prefs.write_text("timezone: UTC\narxiv:\n  categories: [cs.RO]\n", encoding="utf-8")
    def boom(*a, **k):
        raise RuntimeError("arXiv down")
    monkeypatch.setattr(arxiv, "fetch_candidates", boom)
    rc = cli.main(["fetch", "--prefs", str(prefs)])
    assert rc == 1
    assert "arXiv down" in capsys.readouterr().err

def test_commit_archives_and_marks_seen(tmp_path, monkeypatch):
    monkeypatch.setenv("RESEARCH_HOME", str(tmp_path))
    digest = tmp_path / "d.md"
    digest.write_text("# digest body", encoding="utf-8")
    rc = cli.main([
        "commit", "--ids", "idA,idB",
        "--digest-file", str(digest),
        "--date", "2026-05-30",
    ])
    assert rc == 0
    from research_assistant import state
    assert state.load_seen(state.seen_path()) == {"idA", "idB"}
    assert state.digest_path("2026-05-30").read_text(encoding="utf-8") == "# digest body"
```

- [ ] **Step 2: 跑测试确认失败**

Run: `pytest tests/test_cli.py -v`
Expected: FAIL（`ModuleNotFoundError: research_assistant.cli`）

- [ ] **Step 3: 实现 `cli.py`**

```python
import argparse
import json
import sys
from pathlib import Path

from . import config, state, arxiv


def cmd_fetch(args) -> int:
    prefs = config.load_prefs(Path(args.prefs))
    seen = state.load_seen(state.seen_path())
    try:
        papers = arxiv.fetch_candidates(prefs.arxiv, seen)
    except RuntimeError as e:
        print(str(e), file=sys.stderr)
        return 1
    print(json.dumps([vars(p) for p in papers], ensure_ascii=False, indent=2))
    return 0


def cmd_commit(args) -> int:
    ids = [i for i in args.ids.split(",") if i]
    date = args.date or state.today_str(args.timezone)
    if args.digest_file:
        text = Path(args.digest_file).read_text(encoding="utf-8")
        state.atomic_write_text(state.digest_path(date), text)
    state.append_seen(state.seen_path(), ids, date)
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="research-assistant")
    sub = parser.add_subparsers(dest="cmd", required=True)

    pf = sub.add_parser("fetch", help="抓取并打印去重后的候选论文 JSON")
    pf.add_argument("--prefs", default=str(Path.home() / ".hermes" / "research" / "prefs.yaml"))
    pf.set_defaults(func=cmd_fetch)

    pc = sub.add_parser("commit", help="归档日报并把推过的 id 写入 seen.jsonl")
    pc.add_argument("--ids", required=True)
    pc.add_argument("--digest-file", default=None)
    pc.add_argument("--date", default=None)
    pc.add_argument("--timezone", default="UTC")
    pc.set_defaults(func=cmd_commit)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: 跑测试确认通过**

Run: `pytest tests/test_cli.py -v && pytest -q`
Expected: `test_cli.py` 3 passed；全量 `pytest -q` 全绿。

- [ ] **Step 5: Commit**

```bash
git add src/research_assistant/cli.py tests/test_cli.py
git commit -m "feat: fetch and commit CLI commands"
```

---

## Task 8: SOUL 人设片段 `pack/SOUL.snippet.md`

**Files:**
- Create: `pack/SOUL.snippet.md`

- [ ] **Step 1: 写人设片段**

```markdown
<!-- BEGIN research-assistant persona (managed by install.sh) -->
## 角色：科研搭子

你是用户的科研搭子——一个主动、靠谱、会盯进度也会陪写作的研究伙伴。面向所有科研工作者，对注意力容易分散的人尤其友好。

### 操作原则
- **主动但不噪音**：该出现时出现，没事别打扰。提醒只在"真有该提醒的事"时发。
- **拆到下一个最小动作**：把"写论文"这种大任务，拆成"打开 overleaf 写 intro 第一句"这种立刻能做的小动作。
- **接住掉的事**：用户随口的承诺/待办，记下来，别让它掉地上。
- **夸进步**：完成了就具体地夸，给即时正反馈。
- **狠筛信息**：论文、资料宁缺毋滥。每天精选 3–5 篇，给"为什么和你相关"，不堆量。

### 问责强度（读 `~/.hermes/research/prefs.yaml` 的 `style.accountability`，默认 gentle）
每一档都**只针对行为、不否定用户这个人**：
- `gentle` 温柔：鼓励为主，不施压，不制造负罪感。
- `firm` 坚定：直说"你这事拖 3 天了"，对事不对人，适度施压。
- `tough` 严格：严师式强力催，戳拖延的痛点，盯得紧。
- `savage` 骂醒：允许更冲、更扎心的狠话逼用户动（仍守不人身羞辱的底线）。

读 `style.proactivity` 调提醒频率；`style.celebrate_wins` 为 true 时完成给庆祝反馈。
<!-- END research-assistant persona -->
```

- [ ] **Step 2: 人工核对**

确认：四档问责齐全、每档都写了"针对行为不针对人"、狠筛原则在、读 prefs 的指引在。用 `BEGIN/END` 注释包起来，方便 install.sh 幂等替换。

- [ ] **Step 3: Commit**

```bash
git add pack/SOUL.snippet.md
git commit -m "feat: research buddy persona snippet for SOUL.md"
```

---

## Task 9: 论文日报技能 `pack/skills/research/arxiv-digest/SKILL.md`

**Files:**
- Create: `pack/skills/research/arxiv-digest/SKILL.md`

- [ ] **Step 1: 写技能**

````markdown
---
name: arxiv-digest
description: 每天从 arXiv 抓取用户方向的新论文，狠筛 3-5 篇并推送到飞书。由 cron 定时触发。
version: 1.0.0
platforms: [linux, macos]
metadata:
  hermes:
    tags: [research, arxiv, digest]
    category: research
---

## When to Use
- 由 cron 每天定时触发（默认 09:00）。
- 用户主动说"看看今天的论文 / 来份论文日报"。

## Procedure

1. **抓候选**：运行
   ```
   research-assistant fetch --prefs ~/.hermes/research/prefs.yaml
   ```
   - 退出码 0：stdout 是去重后的候选论文 JSON 数组（含 id/title/summary/authors/link/published）。
   - 退出码非 0：抓取失败。**不要**继续，直接执行下面的「失败处理」。

2. **狠筛 + 排序（判断活）**：读 `~/.hermes/research/prefs.yaml` 的 `arxiv.keywords` 与 `arxiv.max_per_day`。
   - 按"与用户方向的相关度"给候选打分排序。
   - 只保留前 `max_per_day` 篇（默认 5）。宁缺毋滥，弱相关的砍掉。

3. **写日报正文（markdown）**：每篇一块，包含：
   - 标题（加粗）+ arXiv 链接
   - 一句话"它讲了啥"
   - 一句话"**为什么和你相关**"
   - 建议动作：`精读` / `扫一眼` / `跳过`
   把正文存成临时文件，例如：
   ```
   /tmp/arxiv-digest.md
   ```

4. **归档 + 标记已读**：运行
   ```
   research-assistant commit --ids <逗号分隔的入选 id> --digest-file /tmp/arxiv-digest.md --date <YYYY-MM-DD> --timezone <prefs.timezone>
   ```
   - 这一步把入选论文写进 `seen.jsonl`（明天不再重复推）并归档日报。
   - **务必在确认要推送之后、作为最后一步**执行（失败就别推、也别 commit）。

5. **推送**：把第 3 步的日报正文作为本次回复的最终内容输出。cron 的 `deliver: feishu` 会把它发到 home chat。

## 失败处理（第 1 步非 0 时）
- 给用户发一句软提示，例如："今天 arXiv 没抓到（可能它在抽风）。回我『重试』我就再来一次。"
- 不要 commit、不要污染 seen.jsonl。
- 可选：用 cronjob 工具挂一个 1 小时后的一次性重试。

## Pitfalls
- 不要在抓取失败时还硬编一份"空日报"——会把 seen 弄脏。
- `commit` 的 `--ids` 必须是**入选**那几篇的 id，不是全部候选。
- max_per_day 是硬上限，别超。

## Verification
- 干跑：`research-assistant fetch` 能打印候选 JSON。
- 端到端：`hermes cron run <job_id>` 触发后，飞书 home chat 收到日报，且 `~/.hermes/research/state/papers/` 下出现当天 `digest-*.md`、`seen.jsonl` 增长。
````

- [ ] **Step 2: 人工核对**

确认：frontmatter 合法；fetch→筛→写→commit→推 的顺序对；失败分支不污染 seen；commit 在推送前作为最后一步。

- [ ] **Step 3: Commit**

```bash
git add pack/skills/research/arxiv-digest/SKILL.md
git commit -m "feat: arxiv-digest skill"
```

---

## Task 10: 配置模板 `pack/prefs.example.yaml`

**Files:**
- Create: `pack/prefs.example.yaml`

- [ ] **Step 1: 写配置模板**

```yaml
timezone: Asia/Shanghai
name: 你的名字

arxiv:
  categories: [cs.RO, cs.LG, cs.CL, eess.SY]
  keywords: ["robotic manipulation", "LLM agent", "model predictive control"]
  max_per_day: 5
  # source: arxiv   # 预留：以后可加 pubmed / biorxiv

schedule:            # Plan 1 只用到 paper_digest；其余给 Plan 2 用
  morning_plan:    "08:30"
  paper_digest:    "09:00"
  open_loop_check: ["14:00", "18:00"]
  evening_review:  "22:00"

style:
  proactivity: high          # high | medium | low
  accountability: gentle     # gentle | firm | tough | savage
  tone: warm
  celebrate_wins: true

features:
  morning_plan:      true
  paper_digest:      true
  focus_buddy:       true
  open_loop_tracker: true
  evening_review:    true
```

> 注：Plan 1 的代码只消费 `timezone` 与 `arxiv.*`；其余字段先放着，给 Plan 2 用，不影响本期。

- [ ] **Step 2: 人工核对**

确认 yaml 合法（`python -c "import yaml,sys; yaml.safe_load(open('pack/prefs.example.yaml'))"` 不报错），arxiv 字段名与 `config.py` 一致。

- [ ] **Step 3: Commit**

```bash
git add pack/prefs.example.yaml
git commit -m "feat: prefs.example.yaml template"
```

---

## Task 11: cron 模板 + 安装脚本

**Files:**
- Create: `pack/cron/jobs.snippet.json`
- Create: `install.sh`

- [ ] **Step 1: 写 cron 模板 `pack/cron/jobs.snippet.json`**

```json
{
  "schedule": "0 9 * * *",
  "skill": "arxiv-digest",
  "deliver": "feishu",
  "prompt": "运行 arxiv-digest 技能：抓取今天的 arXiv 新论文，狠筛 3-5 篇，写成日报推送给我。"
}
```

> 这是给人看的模板；真正注册用 install.sh 里的 `hermes cron create` 或自然语言（见下）。`0 9 * * *` 对应 prefs 的 `paper_digest: "09:00"`，改时间就改这里。

- [ ] **Step 2: 写 `install.sh`（幂等）**

```bash
#!/usr/bin/env bash
set -euo pipefail

REPO="$(cd "$(dirname "$0")" && pwd)"
HERMES="${HERMES_HOME:-$HOME/.hermes}"
RESEARCH="$HERMES/research"

echo "==> 安装 Python 包"
pip install -e "$REPO"

echo "==> 建目录"
mkdir -p "$RESEARCH/state/papers" "$RESEARCH/state/timeline" \
         "$HERMES/skills/research"

echo "==> 配置文件"
if [ ! -f "$RESEARCH/prefs.yaml" ]; then
  cp "$REPO/pack/prefs.example.yaml" "$RESEARCH/prefs.yaml"
  echo "    已生成 $RESEARCH/prefs.yaml —— 记得填你的方向关键词"
else
  echo "    已存在 $RESEARCH/prefs.yaml，跳过"
fi

echo "==> 安装技能"
cp -r "$REPO/pack/skills/research/arxiv-digest" "$HERMES/skills/research/"

echo "==> 合并 SOUL 人设（幂等）"
SOUL="$HERMES/SOUL.md"
touch "$SOUL"
if grep -q "BEGIN research-assistant persona" "$SOUL"; then
  python3 - "$SOUL" "$REPO/pack/SOUL.snippet.md" <<'PY'
import re, sys
soul_path, snip_path = sys.argv[1], sys.argv[2]
soul = open(soul_path, encoding="utf-8").read()
snip = open(snip_path, encoding="utf-8").read()
soul = re.sub(
    r"<!-- BEGIN research-assistant persona.*?END research-assistant persona -->",
    snip.strip(), soul, flags=re.S)
open(soul_path, "w", encoding="utf-8").write(soul)
PY
  echo "    已更新 SOUL 人设片段"
else
  printf "\n\n%s\n" "$(cat "$REPO/pack/SOUL.snippet.md")" >> "$SOUL"
  echo "    已追加 SOUL 人设片段"
fi

echo
echo "==> 还差最后一步：注册定时任务（cron 的确切 CLI 参数因 Hermes 版本而异）"
echo "    方式 A（推荐，自然语言）：在飞书直接对 Hermes 说："
echo '      "每天早上 9 点跑 arxiv-digest 技能，结果发飞书"'
echo "    方式 B（命令行）：参考 \`hermes cron --help\`，按 pack/cron/jobs.snippet.json 注册"
echo
echo "完成。先 \`research-assistant fetch\` 自测，再用 cron 跑一次端到端。"
```

- [ ] **Step 3: 验证脚本语法**

Run: `bash -n install.sh && chmod +x install.sh`
Expected: 无语法错误。

> cron 注册故意不写死 CLI 参数：Hermes 各版本 `cron create` 的 `--skill/--deliver` 旗标不一定一致（见 spec §14），用自然语言注册最稳，避免装上去就坏。

- [ ] **Step 4: Commit**

```bash
git add pack/cron/jobs.snippet.json install.sh
git commit -m "feat: cron template and idempotent installer"
```

---

## Task 12: README + 端到端验证

**Files:**
- Create: `README.md`

- [ ] **Step 1: 写 README**

````markdown
# Hermes 科研搭子

在 [Hermes Agent](https://github.com/NousResearch/hermes-agent) 之上的科研助手。Plan 1：基础设施 + arXiv 论文日报。

## 前置
- 已跑起来的 Hermes（飞书 gateway 能对话）。
- 已设好飞书 home chat：在飞书对 Hermes 发 `/set-home`。
- 已装 `feishucli`（后续功能用）。

## 安装
```bash
git clone <this-repo> && cd hermes-poss
bash install.sh
```
然后编辑 `~/.hermes/research/prefs.yaml`，填上你真实的 `arxiv.categories` 与 `keywords`。

## 自测
```bash
# 1) 机械活：能抓到候选
research-assistant fetch --prefs ~/.hermes/research/prefs.yaml | head

# 2) 全量单测
pip install -e ".[dev]" && pytest -q
```

## 端到端（论文日报）
1. 按 install.sh 末尾提示注册 cron（自然语言最省事）。
2. 立刻触发一次：`hermes cron run <job_id>`（或在飞书说"来份论文日报"）。
3. 预期：飞书 home chat 收到 3–5 篇精选日报；`~/.hermes/research/state/papers/` 出现当天 `digest-*.md`，`seen.jsonl` 增长。
4. 再触发一次：之前推过的不再出现（去重生效）。

## 目录
- `src/research_assistant/` — 机械活 Python 包（含单测）
- `pack/` — 可分发的包（SOUL 人设 / 技能 / 配置模板 / cron 模板）
- `install.sh` — 装进 `~/.hermes/`
- `docs/superpowers/` — 设计 spec 与实施计划
````

- [ ] **Step 2: 端到端人工验证（在常开机器上）**

按 README「端到端」走一遍，确认四点全绿：收到日报、有 digest 存档、seen 增长、二次触发去重。

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "docs: README and end-to-end verification"
```

---

## 自检（写计划时已过一遍）

- **Spec 覆盖**：基础设施(配置 §8 / 状态 §9 / SOUL §7) → Task 2/3/4/8；论文日报数据流 §10② → Task 5/6/7/9/11；错误处理 §11(arXiv 重试 / seen 仅成功后写 / 坏文件恢复) → Task 5/7/3 + 技能失败分支；测试策略 §12(脚本单测 + 干跑) → 各 TDD 任务 + Task 12；分发预留 §13(三层分离 / 零硬编码 / 安装雏形 / 源接口) → pack 结构 + install.sh + `fetch_candidates` 接口。
- **范围**：仅 Plan 1（基础设施 + 论文日报）；晨间/复盘/巡检/专注 留给 Plan 2。
- **占位符**：无 TODO/TBD；每个代码步骤都给了真实可跑代码与命令。
- **类型一致**：`Prefs/ArxivPrefs` 字段、`Paper` 字段、`state.*` 与 `arxiv.*` 函数签名在 Task 间一致；CLI 调用的就是前面定义的函数。

## 待执行时确认（来自 spec §14）
- `prefs.yaml` 里填真实 `arxiv.keywords`。
- 飞书已 `/set-home`。
- `hermes cron` 注册的确切方式（优先自然语言）。
- 接的 LLM provider 已在 Hermes 配好（不影响本计划代码）。
