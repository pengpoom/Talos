# Plan 3.1：focus-buddy 闭环 + 历史

实测发现 Hermes 的 agent **能自建一次性定时提醒**(11:46 那个 cron 实锤),所以不用自己写轮询。改成把专注做成闭环 + 永久历史。

## 五条
1. 开始时建**一次性**提醒(用完即清,不循环、不堆积)—— 技能层
2. 提醒触发时**顺带 `focus-end`** 收尾(关会话 + 庆祝)—— 技能层
3. 开新会话前先 `focus-status` 确认(避免覆盖丢失)—— 技能层
4. **`focus-end` 追加 `focus_log.jsonl` + 时间轴** → 永久历史 + 时长 —— 代码
5. **`focus-log` / `focus-stats`** 命令查看历史与累计 —— 代码

## 批次

### Batch 1 — 代码(4、5) + 单测
- `focus.py`：`focus_log_path / append_focus_log / load_focus_log / focus_stats(log,*,since=None)`；`end_focus` 收尾时算 `elapsed_min` 并追加一条 log（不改签名）。
- `cli.py`：`focus-end` 顺带写当天时间轴；新增 `focus-log [--limit]`、`focus-stats [--since]`。
- 验收：`pytest -q` 全绿。

### Batch 2 — 技能(1、2、3)
- 重写 `pack/skills/research/focus-buddy/SKILL.md`：开始前 `focus-status` 确认 → `focus-start` → 建**一次性**到点提醒(其 prompt 跑 `focus-end` 收尾 + 自删) → 结束自动入账(log+时间轴) → 提 `focus-log/focus-stats`。
- 验收：frontmatter 合法、`bash -n` 无关、人读通顺。

## 数据
- `focus_log.jsonl`：每行 `{task, started, ended, elapsed_min}`，只追加。
