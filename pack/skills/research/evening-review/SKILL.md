---
name: evening-review
description: 每天晚上带用户复盘今天、记时间轴、把没做完的转入开放循环。cron 触发。
version: 1.0.0
platforms: [linux, macos]
metadata:
  hermes:
    tags: [research, review, adhd]
    category: research
---

## When to Use
- cron 每天晚上触发（默认 22:00）。
- 用户主动说"复盘下今天 / 今天总结"。

## Procedure

1. **读今天的计划**：运行
   ```
   research-assistant today-show --tz <prefs.timezone>
   ```
   得到今天的 `plan` 与 `unplanned_done`。

2. **问进展（判断活）**：逐项问"这件做到哪了？"，并问"还干了啥计划外的？"
   - 用户说完成的：`research-assistant today-mark-done --tz <tz> --id <tN>`
   - 计划外做的：`research-assistant today-add-unplanned --tz <tz> --text "..."`
   - 读 `style`：**先夸完成的**（celebrate_wins 为 true 时给庆祝），没完成的**不指责**（语气按 accountability 档）。

3. **记时间轴**：把今天实际发生的，逐条写进时间轴：
   ```
   research-assistant timeline-append --tz <tz> --text "09:30-11:00 写 intro ✅"
   ```

4. **结转没做完的**：对仍未完成、又值得继续的，问"滚到明天还是先记着"，记着的转入开放循环：
   ```
   research-assistant loops-add --tz <tz> --desc "<没做完的事>" --source "未完成"
   ```

5. **收尾**：`research-assistant today-log --tz <tz>`，再给用户一句明天的引子。把复盘小结作为最终回复（cron deliver 飞书）。

6. （可选增强）若已接 `feishucli`：把时间轴同步到飞书日历。见 README「可选增强」。

## Pitfalls
- 没做完 ≠ 指责。先肯定做到的。
- 只有用户确认"要继续"的才进 open_loops，别把所有未完成都一股脑塞进去变噪音。

## Verification
- 干跑：`today-show` / `timeline-append` / `loops-add` 能跑。
- 端到端：触发后飞书收到复盘；`state/timeline/<date>.md` 有内容；未完成项进了 `open_loops.json`。
