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
