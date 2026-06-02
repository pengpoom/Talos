---
name: morning-plan
description: 每天早上的规划仪式：浮出悬着的开放循环，帮用户定 1-3 件今日聚焦，确认后写进飞书 Todo（不写 today.json）。cron 触发或用户说"帮我规划今天"。
version: 2.0.0
platforms: [linux, macos]
metadata:
  hermes:
    tags: [research, planning, adhd]
    category: research
---

## When to Use
- cron 每个工作日早晨触发。
- 用户主动说"帮我规划下今天 / 今天干啥"。

## Procedure

1. **浮出悬着的事**（给今天当背景，不是直接塞成任务）：
   ```
   research-assistant loops-due --tz <prefs.timezone>
   ```
   （也可 `loops-due --domain work` / `--domain research` 把工作和科研的**分开看**）。挑出今天值得推进的，规划时科研/工作分别列。

2. **提建议（判断活）**：读 `~/.hermes/research/prefs.yaml` 的 `style`。
   - 给 **1-3 件**今天最该做的（别贪多，ADHD 友好），每件**拆到"下一个最小动作"**（不是"写论文"，是"打开 overleaf 写 intro 第一句"）。
   - 语气按 `style.accountability` 档位（gentle…savage）。

3. **写进飞书 Todo（状态以飞书为准，用户 App 里看得见）**：用 `lark-task` 技能把确认后的 1-3 件建成飞书 Todo（载入 lark-task 看具体命令）。约定见 `feishu-personal-productivity-workflows`：单一清单 `Todo`、当天 `YYYY-MM-DD` 分区、最重要的标 `【今天唯一重点】`、start/due 默认今天、分配给当前登录用户。
   - **cron / 主动场景**：先把"今天聚焦 X 件 + 悬着的事"发出去，并问"要我加进飞书 Todo 吗？"，**等用户确认再建**——不要不打招呼就往飞书 Todo 写。
   - 用户当面确认 / 口述后再建任务。

4. **（可选）排进日历**：计划定下后，问"要不要把这几件排进日历的专注块？" → 走 `time-block` 技能（查忙闲 → 提议 → 确认才建）。

5. **不要再写 `today.json`**（已退役，今日计划状态以飞书 Todo 为准）。

## Pitfalls
- 1-3 件是上限，别摆一长串。
- cron 场景别擅自往飞书 Todo 写——先提议、用户确认再落（外发/写入要可预览）。
- 浮出 loops 只是当背景，别把所有 open loop 一股脑塞成今日任务。
- `loops-due` 失败不致命：照常让用户口述今天计划，再建飞书 Todo。

## Verification
- 干跑：`research-assistant loops-due` 能跑。
- 端到端：触发后飞书收到"今天聚焦 X 件 + 悬着的事"，确认后任务出现在飞书 Todo（App 可见）。
