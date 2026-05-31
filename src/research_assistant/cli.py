import argparse
import json
import sys
from pathlib import Path

from . import config, state, arxiv, daily


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


def cmd_today_show(args) -> int:
    print(json.dumps(daily.load_today(args.tz), ensure_ascii=False, indent=2))
    return 0


def cmd_today_set_plan(args) -> int:
    items = json.loads(args.json)
    today = daily.load_today(args.tz)
    daily.set_plan(today, items)
    daily.save_today(today)
    return 0


def cmd_today_mark_done(args) -> int:
    today = daily.load_today(args.tz)
    try:
        daily.mark_done(today, args.id)
    except KeyError:
        print(f"no such plan item: {args.id}", file=sys.stderr)
        return 1
    daily.save_today(today)
    return 0


def cmd_today_add_unplanned(args) -> int:
    today = daily.load_today(args.tz)
    daily.add_unplanned(today, args.text)
    daily.save_today(today)
    return 0


def cmd_today_log(args) -> int:
    today = daily.load_today(args.tz)
    daily.mark_logged(today)
    daily.save_today(today)
    return 0


def cmd_today_rollover(args) -> int:
    moved = daily.rollover_stale(args.tz)
    print(json.dumps(moved, ensure_ascii=False))
    return 0


def cmd_loops_list(args) -> int:
    print(json.dumps(daily.load_loops(), ensure_ascii=False, indent=2))
    return 0


def cmd_loops_add(args) -> int:
    loops = daily.load_loops()
    daily.add_loop(loops, args.desc, source=args.source,
                   created=state.today_str(args.tz), due=args.due)
    daily.save_loops(loops)
    return 0


def cmd_timeline_append(args) -> int:
    date = args.date or state.today_str(args.tz)
    daily.append_timeline(date, args.text)
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

    pts = sub.add_parser("today-show")
    pts.add_argument("--tz", default="UTC")
    pts.set_defaults(func=cmd_today_show)

    psp = sub.add_parser("today-set-plan")
    psp.add_argument("--tz", default="UTC")
    psp.add_argument("--json", required=True, help="[{task, next_action}] 的 JSON")
    psp.set_defaults(func=cmd_today_set_plan)

    pmd = sub.add_parser("today-mark-done")
    pmd.add_argument("--tz", default="UTC")
    pmd.add_argument("--id", required=True)
    pmd.set_defaults(func=cmd_today_mark_done)

    pau = sub.add_parser("today-add-unplanned")
    pau.add_argument("--tz", default="UTC")
    pau.add_argument("--text", required=True)
    pau.set_defaults(func=cmd_today_add_unplanned)

    plog = sub.add_parser("today-log")
    plog.add_argument("--tz", default="UTC")
    plog.set_defaults(func=cmd_today_log)

    pro = sub.add_parser("today-rollover")
    pro.add_argument("--tz", default="UTC")
    pro.set_defaults(func=cmd_today_rollover)

    pll = sub.add_parser("loops-list")
    pll.set_defaults(func=cmd_loops_list)

    pla = sub.add_parser("loops-add")
    pla.add_argument("--tz", default="UTC")
    pla.add_argument("--desc", required=True)
    pla.add_argument("--source", required=True)
    pla.add_argument("--due", default=None)
    pla.set_defaults(func=cmd_loops_add)

    pta = sub.add_parser("timeline-append")
    pta.add_argument("--tz", default="UTC")
    pta.add_argument("--date", default=None)
    pta.add_argument("--text", required=True)
    pta.set_defaults(func=cmd_timeline_append)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
