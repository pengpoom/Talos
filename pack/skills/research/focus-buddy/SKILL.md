---
name: focus-buddy
description: 按需 body-doubling，陪用户开一次专注会话、陪开始陪结束。用户主动触发，不进 cron。
version: 1.0.0
platforms: [linux, macos]
metadata:
  hermes:
    tags: [research, focus, adhd]
    category: research
---

## When to Use
- 用户说"陪我专注 / 盯着我做 X / body double / 开一会专注"。
- 纯按需,**不用 cron**。

## Procedure

1. **确认做什么 + 多久**：没说时长就问，或默认 25–50 分钟。开会话：
   ```
   research-assistant focus-start --tz <prefs.timezone> --task "<要专注的事>" --minutes <N>
   ```

2. **body-doubling 开场（判断活）**：利落、不啰嗦。营造"有人在场"而非"被监工"——
   例如："我在这儿盯着，你开始。先做最小那步：<下一个最小动作>。"

3. **期间**：用户回来报告进展或说分心了 →
   - 温和把注意力拉回那件事，别说教。
   - 想看进度：`research-assistant focus-status --tz <tz>`（显示已专注 `elapsed_min` 分钟）。
   - **别主动频繁打断**——body-doubling 是"在场"，不是盯梢。

4. **结束**：
   ```
   research-assistant focus-end --tz <tz>
   ```
   拿到 `elapsed_min` 后：
   - 读 `style`：`celebrate_wins` 为 true 就按 `tone` 给个利落的庆祝。
   - 问要不要记进时间轴：`research-assistant timeline-append --tz <tz> --text "HH:MM-HH:MM <事> ✅"`
   - 若刚推进的是某个开放循环，问要不要 `research-assistant loops-resolve --id <id> --status done` 关掉它。

## Pitfalls
- 别变监工：关键是"陪伴感"，不是每几分钟查岗。
- 时长到了温柔提醒，不强制结束；想续就再 `focus-start`。
- 一次只跟一个专注会话（`focus.json` 覆盖式）；开新的会覆盖旧的。

## Verification
- 干跑：`focus-start` → `focus-status`（显示 elapsed_min）→ `focus-end` 能跑。
- 端到端：飞书说"陪我专注 30 分钟写 intro" → 收到开场；结束时收到庆祝 + 可选记时间轴。
