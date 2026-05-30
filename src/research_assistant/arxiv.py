import time
from dataclasses import dataclass
import requests
import feedparser

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
