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
