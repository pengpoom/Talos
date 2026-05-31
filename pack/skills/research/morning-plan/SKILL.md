---
name: morning-plan
description: 每天早上帮用户定 1-3 件聚焦任务，拆到下一个最小动作，写进 today.json 并推送飞书。cron 触发。
version: 1.0.0
platforms: [linux, macos]
metadata:
  hermes:
    tags: [research, planning, adhd]
    category: research
---

## When to Use
- cron 每天早晨触发（默认 08:30）。
- 用户主动说"帮我规划下今天 / 今天干啥"。

## Procedure

1. **结转昨天没做完的**：运行
   ```
   research-assistant today-rollover --tz <prefs.timezone>
   ```
   输出是被结转进开放循环的未完成项（JSON 列表，可能为空）。

2. **看悬着的事**：运行
   ```
   research-assistant loops-list
   ```
   得到 open_loops（含刚结转的 + 以前攒的）。挑出今天值得推进的。

3. **提建议（判断活）**：读 `~/.hermes/research/prefs.yaml` 的 `style`。
   - 给用户摆 **1-3 件**今天最该做的（别贪多，ADHD 友好）。
   - 每件**拆到"下一个最小动作"**（不是"写论文"，是"打开 overleaf 写 intro 第一句"）。
   - 语气按 `style.accountability` 档位（gentle…savage）。

4. **等用户拍板**：把建议发出去（cron 会经飞书 deliver 给用户）。用户确认 / 改动后，把最终计划写入：
   ```
   research-assistant today-set-plan --tz <prefs.timezone> --json '[{"task":"...","next_action":"..."}, ...]'
   ```

5. （可选增强）若已接 `feishucli`：把每件 task 建成飞书任务 / 在日历占块。见仓库 README「可选增强」。

## Pitfalls
- 1-3 件是上限，别摆一长串。
- `--json` 必须是合法 JSON 数组；task 必填、next_action 尽量给。
- 结转/读 loops 失败不致命：照常让用户口述今天计划，再 set-plan。

## Verification
- 干跑：`research-assistant today-rollover` 与 `loops-list` 能跑。
- 端到端：触发后飞书收到"今天聚焦 X 件"，确认后 `today.json` 的 `plan` 被写入。
