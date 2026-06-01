import argparse
import json
import sys
from pathlib import Path

from . import config, state, arxiv, daily, focus


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
    print(json.dumps(today, ensure_ascii=False, indent=2))
    return 0


def cmd_today_mark_done(args) -> int:
    today = daily.load_today(args.tz)
    try:
        daily.mark_done(today, args.id)
    except KeyError:
        print(f"no such plan item: {args.id}", file=sys.stderr)
        return 1
    daily.save_today(today)
    print(json.dumps(today, ensure_ascii=False, indent=2))
    return 0


def cmd_today_add_unplanned(args) -> int:
    today = daily.load_today(args.tz)
    daily.add_unplanned(today, args.text)
    daily.save_today(today)
    print(json.dumps(today, ensure_ascii=False, indent=2))
    return 0


def cmd_today_log(args) -> int:
    today = daily.load_today(args.tz)
    daily.mark_logged(today)
    daily.save_today(today)
    print(json.dumps(today, ensure_ascii=False, indent=2))
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
    loop = daily.add_loop(loops, args.desc, source=args.source,
                          created=state.today_str(args.tz), due=args.due)
    daily.save_loops(loops)
    print(json.dumps(loop, ensure_ascii=False, indent=2))
    return 0


def cmd_timeline_append(args) -> int:
    date = args.date or state.today_str(args.tz)
    daily.append_timeline(date, args.text)
    print(json.dumps({"date": date, "appended": args.text}, ensure_ascii=False))
    return 0


def cmd_loops_due(args) -> int:
    due = daily.due_for_nudge(daily.load_loops(), state.today_str(args.tz),
                              cadence_days=args.cadence)
    print(json.dumps(due, ensure_ascii=False, indent=2))
    return 0


def cmd_loops_nudge(args) -> int:
    loops = daily.load_loops()
    try:
        loop = daily.update_loop(loops, args.id, nudged_date=state.today_str(args.tz))
    except KeyError:
        print(f"no such loop: {args.id}", file=sys.stderr)
        return 1
    daily.save_loops(loops)
    print(json.dumps(loop, ensure_ascii=False, indent=2))
    return 0


def cmd_loops_resolve(args) -> int:
    loops = daily.load_loops()
    try:
        loop = daily.update_loop(loops, args.id, status=args.status)
    except KeyError:
        print(f"no such loop: {args.id}", file=sys.stderr)
        return 1
    daily.save_loops(loops)
    print(json.dumps(loop, ensure_ascii=False, indent=2))
    return 0


def cmd_focus_start(args) -> int:
    sess = focus.start_focus(args.task, started=state.now_iso(args.tz), planned_min=args.minutes)
    print(json.dumps(sess, ensure_ascii=False, indent=2))
    return 0


def cmd_focus_status(args) -> int:
    sess = focus.load_focus()
    if not sess or not sess.get("active"):
        print(json.dumps({"active": False}, ensure_ascii=False))
        return 0
    sess = dict(sess)
    sess["elapsed_min"] = focus.elapsed_minutes(sess["started"], state.now_iso(args.tz))
    print(json.dumps(sess, ensure_ascii=False, indent=2))
    return 0


def cmd_focus_end(args) -> int:
    try:
        sess = focus.end_focus(ended=state.now_iso(args.tz))
    except RuntimeError as e:
        print(str(e), file=sys.stderr)
        return 1
    date, sh = sess["started"].split("T")
    eh = sess["ended"].split("T")[1]
    daily.append_timeline(date, f"{sh}-{eh} 专注 {sess['task']}（{sess['elapsed_min']}min）✅")
    print(json.dumps(sess, ensure_ascii=False, indent=2))
    return 0


def cmd_focus_log(args) -> int:
    log = focus.load_focus_log()
    items = log[-args.limit:] if args.limit else log
    print(json.dumps(items, ensure_ascii=False, indent=2))
    return 0


def cmd_focus_stats(args) -> int:
    stats = focus.focus_stats(focus.load_focus_log(), since=args.since)
    print(json.dumps(stats, ensure_ascii=False))
    return 0


def _default_tz() -> str:
    try:
        return config.load_prefs(state.research_home() / "prefs.yaml").timezone
    except Exception:
        return "UTC"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="research-assistant")
    sub = parser.add_subparsers(dest="cmd", required=True)
    tzd = _default_tz()

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
    pts.add_argument("--tz", default=tzd)
    pts.set_defaults(func=cmd_today_show)

    psp = sub.add_parser("today-set-plan")
    psp.add_argument("--tz", default=tzd)
    psp.add_argument("--json", required=True, help="[{task, next_action}] 的 JSON")
    psp.set_defaults(func=cmd_today_set_plan)

    pmd = sub.add_parser("today-mark-done")
    pmd.add_argument("--tz", default=tzd)
    pmd.add_argument("--id", required=True)
    pmd.set_defaults(func=cmd_today_mark_done)

    pau = sub.add_parser("today-add-unplanned")
    pau.add_argument("--tz", default=tzd)
    pau.add_argument("--text", required=True)
    pau.set_defaults(func=cmd_today_add_unplanned)

    plog = sub.add_parser("today-log")
    plog.add_argument("--tz", default=tzd)
    plog.set_defaults(func=cmd_today_log)

    pro = sub.add_parser("today-rollover")
    pro.add_argument("--tz", default=tzd)
    pro.set_defaults(func=cmd_today_rollover)

    pll = sub.add_parser("loops-list")
    pll.set_defaults(func=cmd_loops_list)

    pla = sub.add_parser("loops-add")
    pla.add_argument("--tz", default=tzd)
    pla.add_argument("--desc", required=True)
    pla.add_argument("--source", required=True)
    pla.add_argument("--due", default=None)
    pla.set_defaults(func=cmd_loops_add)

    pta = sub.add_parser("timeline-append")
    pta.add_argument("--tz", default=tzd)
    pta.add_argument("--date", default=None)
    pta.add_argument("--text", required=True)
    pta.set_defaults(func=cmd_timeline_append)

    pld = sub.add_parser("loops-due", help="列出该跟进（巡检）的开放循环")
    pld.add_argument("--tz", default=tzd)
    pld.add_argument("--cadence", type=int, default=1)
    pld.set_defaults(func=cmd_loops_due)

    pln = sub.add_parser("loops-nudge", help="标记某开放循环今天已提醒")
    pln.add_argument("--tz", default=tzd)
    pln.add_argument("--id", required=True)
    pln.set_defaults(func=cmd_loops_nudge)

    plr = sub.add_parser("loops-resolve", help="关闭开放循环")
    plr.add_argument("--id", required=True)
    plr.add_argument("--status", required=True, choices=["done", "dropped"])
    plr.set_defaults(func=cmd_loops_resolve)

    pfs = sub.add_parser("focus-start", help="开始一次专注会话")
    pfs.add_argument("--tz", default=tzd)
    pfs.add_argument("--task", required=True)
    pfs.add_argument("--minutes", type=int, default=None)
    pfs.set_defaults(func=cmd_focus_start)

    pfst = sub.add_parser("focus-status", help="查看当前专注会话与已用时长")
    pfst.add_argument("--tz", default=tzd)
    pfst.set_defaults(func=cmd_focus_status)

    pfe = sub.add_parser("focus-end", help="结束当前专注会话")
    pfe.add_argument("--tz", default=tzd)
    pfe.set_defaults(func=cmd_focus_end)

    pflog = sub.add_parser("focus-log", help="列出最近的专注记录")
    pflog.add_argument("--limit", type=int, default=10)
    pflog.set_defaults(func=cmd_focus_log)

    pfstat = sub.add_parser("focus-stats", help="专注累计统计（可 --since YYYY-MM-DD）")
    pfstat.add_argument("--since", default=None)
    pfstat.set_defaults(func=cmd_focus_stats)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
