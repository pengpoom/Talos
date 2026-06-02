---
name: evening-review
description: 每天晚上的复盘仪式：读飞书 Todo 看今天做了啥，写 research-assistant 时间轴，把没做完的转成开放循环（不读 today.json）。cron 触发或用户说"复盘今天"。
version: 2.0.0
platforms: [linux, macos]
metadata:
  hermes:
    tags: [research, review, adhd]
    category: research
---

## When to Use
- cron 每个工作日晚上触发。
- 用户主动说"复盘下今天 / 今天总结"。

## Procedure

1. **看今天做了啥**：用 `lark-task` 技能读飞书 Todo（今天 `YYYY-MM-DD` 分区的完成 / 未完成情况；载入 lark-task 看命令）。可结合 `session_search` 翻今天聊过的进展。

2. **问进展 + 夸完成（判断活）**：逐项确认"这件做到哪了？还干了啥计划外的？"
   - 读 `style`：**先夸完成的**（`celebrate_wins` 为 true 时给庆祝），没完成的**不指责**（语气按 accountability 档）。

3. **记时间轴**（research-assistant 永久日志，飞书给不了）：把今天 **focus 之外**实际发生的逐条写进时间轴（**专注会话 `focus-end` 已自动记过，别重复**）：
   ```
   research-assistant timeline-append --tz <tz> --text "09:30-11:00 写 intro ✅"
   ```
   复盘里要回顾专注时长就用 `research-assistant focus-log` / `focus-stats` 读，别再 `timeline-append` 同一段。

4. **没做完的转开放循环**：对仍未完成、又值得继续的，问"滚到明天还是先记着"，记着的转入开放循环：
   ```
   research-assistant loops-add --tz <tz> --desc "<没做完的事>" --source "未完成" --domain <research|work> --next-action "<下一个最小动作>" --due <YYYY-MM-DD>
   ```

5. **收尾**：给用户一句明天的引子。把复盘小结作为最终回复（cron deliver 飞书）。

## Pitfalls
- **专注会话已由 `focus-end` 自动入时间轴**，复盘时**别再 `timeline-append` 重复记**那几段；要回顾用 `focus-log`/`focus-stats` 读。
- 没做完 ≠ 指责。先肯定做到的。
- 只有用户确认"要继续"的才进 open_loops，别把所有未完成都一股脑塞进去变噪音。
- `--due` 必须 `YYYY-MM-DD`，别塞"明天 / today"这种词（否则 `loops-due` 排序认不出）。
- 不读 `today.json`（已退役）；今天做了啥以飞书 Todo 为准。

## Verification
- 干跑：`research-assistant timeline-append` / `loops-add` 能跑。
- 端到端：触发后飞书收到复盘；`state/timeline/<date>.md` 有内容；未完成项进了 `open_loops.json`。
