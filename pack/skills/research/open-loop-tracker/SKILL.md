---
name: open-loop-tracker
description: 巡检开放循环，挑该跟进的提醒用户；没有就不打扰。cron 触发（默认 14:00 / 18:00）。
version: 1.0.0
platforms: [linux, macos]
metadata:
  hermes:
    tags: [research, follow-up, adhd]
    category: research
---

## When to Use
- cron 每天下午触发（默认 14:00、18:00）。
- 用户主动说"有啥悬着的事没 / 我还欠着啥"。

## Procedure

1. **取该跟进的**：运行
   ```
   research-assistant loops-due --tz <prefs.timezone>
   ```
   返回已排序的开放循环（overdue 的排前面），可能为空。

2. **空 → 闭嘴**。直接结束,别为了发而发。巡检的价值是"该提醒才提醒",不是定点骚扰。

3. **非空（判断活）**：读 `~/.hermes/research/prefs.yaml` 的 `style`。
   - 挑**最多 1-3 件**最要紧的（overdue 优先），别把整张单子倒出来。
   - 按 `style.accountability` 档位语气提醒。
   - 每件给个出路："现在推一下？ / 要不要专注一会？ / 还是先搁着？"

4. **按用户回应落账**（关键，否则同一天 18:00 会重复提醒同一件）：
   - 做完了 → `research-assistant loops-resolve --id <id> --status done`
   - 不做了 / 没必要了 → `research-assistant loops-resolve --id <id> --status dropped`
   - 先搁着 → `research-assistant loops-nudge --tz <tz> --id <id>`（标记今天已提醒）

5. （可衔接 focus-buddy）用户想立刻做某件 → 引导进专注会话（见 focus-buddy 技能）。

## Pitfalls
- **空就别推送**。宁可不发,也别凑数骚扰。
- 一次最多挑 1-3 件,挑 overdue / 最久没动的。
- 无论"做完/放弃/搁着",都要落一次 `loops-resolve` 或 `loops-nudge`,否则 14:00 提过 18:00 又提。

## Verification
- 干跑：`research-assistant loops-due` 能跑。
- 端到端：有开放循环时触发 → 飞书收到挑选后的提醒；对某件 `loops-nudge` 后再 `loops-due`,当天不再出现。
