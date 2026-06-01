---
name: focus-buddy
description: 用户说"陪我专注 / 盯着我做 X / body double / 开一会专注"时用。必须用 research-assistant focus-start/focus-status/focus-end 开真实专注会话并落库（focus.json + 历史 + 时间轴），别用飞书原生提醒代替会话本身。按需触发，不进固定 cron。
version: 1.1.0
platforms: [linux, macos]
metadata:
  hermes:
    tags: [research, focus, adhd]
    category: research
---

## When to Use
- 用户说"陪我专注 / 盯着我做 X / body double / 开一会专注"。
- 纯按需,**不进固定 cron**。

## Procedure

1. **确认做什么 + 多久**：没说时长就问，或默认 25–50 分钟。

2. **开新前先看有没有在专注**（避免覆盖丢失）：
   ```
   research-assistant focus-status --tz <prefs.timezone>
   ```
   - `active: true` → 先告诉用户"你还有个『X』在专注（已 N 分钟），先结束它再开新的吗？"。同意结束 → 先 `research-assistant focus-end --tz <tz>`（自动入账），再开新的；要继续旧的 → 别动。
   - `active: false` → 直接开。

3. **开会话**：
   ```
   research-assistant focus-start --tz <tz> --task "<要专注的事>" --minutes <N>
   ```

4. **建一个"到点检查"的一次性提醒**（关键）：让 Hermes 在「开始时间 + N 分钟」**只触发一次**，其提示词写明三件事：
   - 先 `research-assistant focus-status --tz <tz>`；**若仍活跃**则 `research-assistant focus-end --tz <tz>` 收尾，并按 `style` 庆祝 +「X 分钟到了，收工还是再续一会？」；**若已结束**则无需操作、不打扰。
   - 跑完**删除本提醒任务**。
   - ⚠️ **必须是一次性**：只在那个时间点响一次、响完清掉，**不要建成每天循环**的提醒（否则明天又冒出来 + 堆一堆 job）。

5. **body-doubling 开场**：利落不啰嗦——"我在这儿盯着，你开始。先做最小那步：<下一个最小动作>。到点（X:XX）我来叫你。"（这句现在是真的，提醒会触发。）

6. **期间**：用户回来报告进展或说分心 → 温和拉回；想看进度用 `focus-status`（显示 `elapsed_min`）；**别主动频繁打断**——是"在场"，不是查岗。

7. **结束**（用户说"做完了"，或到点提醒触发）：
   ```
   research-assistant focus-end --tz <tz>
   ```
   `focus-end` 会**自动**：关会话、算时长、追加进 `focus_log.jsonl` 历史、写一条当天时间轴。你只需读它返回的 `elapsed_min`，按 `celebrate_wins` 给个利落的庆祝。
   - 若刚推进的是某个开放循环，问要不要 `research-assistant loops-resolve --id <id> --status done`。

8. **回顾**：用户问"我最近/这周专注了多少" →
   - `research-assistant focus-log --limit 10`（最近几次）
   - `research-assistant focus-stats --since <本周一日期>`（累计次数 + 分钟）

## Pitfalls
- 到点提醒**必须一次性 + 自删**；别建循环的。
- 开新会话前一定先 `focus-status`，有活跃的先确认，别默默覆盖丢了旧会话。
- `focus-end` 已自动写历史 + 时间轴，**别再手动 `timeline-append` 同一段**（会重复）。
- 别变监工：body-doubling 的关键是"陪伴感"。

## Verification
- 干跑：`focus-start` → `focus-status` → `focus-end`（产出 `focus_log.jsonl` 一行 + 时间轴一行）→ `focus-log` / `focus-stats` 能跑。
- 端到端：飞书"陪我专注 25 分钟写 X" → 收到开场 + 一次性到点提醒；到点收到收尾庆祝；`focus-log` 能看到这次。
