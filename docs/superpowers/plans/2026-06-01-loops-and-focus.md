# Plan 3：开放循环巡检 + 专注陪伴

补齐 5 个 MVP 功能里剩下的两个：
- **开放循环巡检 open-loop-tracker**：cron 14:00 / 18:00，挑该跟进的开放循环来提醒；空就闭嘴。
- **专注陪伴 focus-buddy**：按需 body-doubling，记一次专注会话，陪开始、陪结束。

配置已就位（`prefs.example.yaml` 已有 `schedule.open_loop_check` 与 `features.focus_buddy/open_loop_tracker`），本计划不动 prefs schema。

## 数据
- 开放循环复用现有 `open_loops.json`（`{id,desc,created,last_nudged,status,due,source}`）。
- 新增 `focus.json`：`{active,task,started,planned_min,ended}`（单会话，覆盖式）。

## 批次

### Batch 1 — 机械层（纯函数 + 单测，无 Hermes）
**P3-T1 `daily.py` 巡检逻辑**
- `_days_between(a,b)`：两个 `%Y-%m-%d` 的天数差。
- `is_overdue(loop, today)`：有 `due` 且 `due <= today`。
- `due_for_nudge(loops, today, *, cadence_days=1)`：status==open 且（从没 nudge 过 或 距上次 nudge ≥ cadence 天）；overdue 排前、再按 created 早的在前。

**P3-T2 `state.now_iso` + `focus.py`**
- `state.now_iso(tz)` → `%Y-%m-%dT%H:%M`（新增函数，不动 `today_str`）。
- `focus.py`：`focus_path / load_focus / start_focus(task,*,started,planned_min=None) / end_focus(*,ended) / elapsed_minutes(started,now)`；`end_focus` 无活跃会话抛 `RuntimeError`。

验收：`pytest -q` 全绿（新增 ~11 测）。

### Batch 2 — CLI（薄封装 + 单测）
**P3-T3 `cli.py`**
- `loops-due --tz [--cadence N]`、`loops-nudge --tz --id`、`loops-resolve --id --status done|dropped`
- `focus-start --tz --task [--minutes N]`、`focus-status --tz`、`focus-end --tz`
- 坏 id / 无会话 → 返回 1。

验收：`pytest -q` 全绿（新增 ~5 测）。

### Batch 3 — Agent 层（产物，无单测）
**P3-T4 `pack/skills/research/open-loop-tracker/SKILL.md`**：`loops-due` → 空则闭嘴 / 非空挑要紧的按 accountability 提醒 → `loops-nudge`（当天不重复）/ `loops-resolve`。
**P3-T5 `pack/skills/research/focus-buddy/SKILL.md`**：`focus-start` → body-doubling 开场 → `focus-status` 看进度 → `focus-end` 按 celebrate_wins 收尾、可写时间轴。
**P3-T6 cron + install + README**：`jobs.snippet.json` 加 14:00/18:00 两条 open-loop-check（focus-buddy 按需、不进 cron）；`install.sh` cron 提示补一行；`README.md` 加「巡检 + 专注」段。install.sh 拷技能已是 `cp -r .../research/.`，无需改。

验收：`bash -n install.sh`、cron JSON 合法、`pytest -q` 全绿。
