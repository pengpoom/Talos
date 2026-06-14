---
name: morning-plan
description: 每天早上的规划仪式：浮出悬着的开放循环，帮用户定 1-3 件今日聚焦，确认后**按 domain 落进共享 open_loop（给各 bot 读自己那片）+ 镜像飞书 Todo（给 App 看）**。cron 触发或用户说"帮我规划今天"。
version: 2.1.1
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
   - 项目背景（可选）：`research-assistant project-list --status active` 看在跑的项目，对卡着的 `project-status --name <项目>` 一眼看哪个项目逾期/没动，规划时优先照顾。

2. **提建议（判断活）**：读 `~/.hermes/research/prefs.yaml` 的 `style`。
   - 给 **1-3 件**今天最该做的（别贪多，ADHD 友好），每件**拆到"下一个最小动作"**（不是"写论文"，是"打开 overleaf 写 intro 第一句"）。
   - 语气按 `style.accountability` 档位（gentle…savage）。

3. **确认后落库：先按 domain 进共享 open_loop，再镜像飞书 Todo**（两处都写，确认后才动）：

   **先对齐（防单边 —— 即使 Todo 已有也要查）**：动笔前比对两边——飞书 Todo 今天分区 vs `research-assistant loops-list`（今天 `created`=今天 且 `source`=今日计划）：
   - **Todo 有、共享后台没有** → 按域 `loops-add … --source 今日计划 --due 今天` **回填**（最常见：你早上在 Todo 建过的项；**别因为"Todo 已经有了"就跳过写后台**）。
   - **共享后台有、Todo 没有** → 补建 Todo。
   - 两边都有 → 不动，别重复。

   下面是写**新确认**的计划项（同样两处都落）：

   **① 共享 open_loop（分域 · 协调层 · 各 bot 读自己那片）** —— 每条计划逐条：
   ```
   research-assistant loops-add --tz <tz> --domain <research|work|personal> \
     --desc "<这件事>" --next-action "<下一个最小动作>" --due <今天 YYYY-MM-DD> \
     --source "今日计划" [--priority high|urgent 给最重点的]
   ```
   - domain 判断同 `open-loop-tracker`：论文/实验/写作=research；回消息/审方案/项目/催人=work；私人=personal。
   - **去重**：建之前 `research-assistant loops-list --domain <d>` 看今天（`created`=今天且 `source`=今日计划）有没有已建的；有就 `loops-update` 改，别重复 `loops-add`。

   **② 飞书 Todo（给你 App 看的视图 · 总管单写）** —— 用 `lark-task` 把同样这 1-3 件建成飞书 Todo（载入 lark-task 看命令）：单一清单 `Todo`、当天 `YYYY-MM-DD` 分区、最重点标 `【今天唯一重点】`、start/due 默认今天、分配给当前登录用户。
   - **只有总管写飞书 Todo**（避免多 bot 往同一张清单打架）；专科 bot 不碰 Todo，读共享 open_loop 即可。
   - **建完回填链接**：建 Todo 拿到 task GUID 后，`research-assistant loops-update --id <对应loop> --todo-id <GUID>` 把两边连上——这样 `todo-sync` 不会把总管自己建的当"手填"重复吸纳。

   **写入纪律**：cron / 主动场景先把"今天聚焦 X 件 + 悬着的事"发出去，问"要我落库 + 加进飞书 Todo 吗？"，**等用户确认再写两处**；当面确认 / 口述后再写。

4. **（可选）排进日历**：计划定下后，问"要不要把这几件排进日历的专注块？" → 走 `time-block` 技能（查忙闲 → 提议 → 确认才建）。

5. **不要再写 `today.json`**（已退役）。**今日计划的真相 = 分域共享 open_loop**；飞书 Todo 是总管维护的 App 视图。

## 各 bot 读自己那片（为什么要落共享后台）
计划落进**分域共享 open_loop** 后，专科 bot 问"今天我这域要干啥"直接读，**不碰飞书 Todo、不要 Feishu 权限**：
- 科研 bot：`research-assistant loops-due --domain research`（或 `loops-list --domain research` 看 `created`=今天的）。
- 总管：读全部（不带 `--domain`）。

**真相在共享 open_loop；飞书 Todo 是总管维护的视图。**

## 视图对账（总管复盘时）
飞书 Todo 单写会滞后（专科 bot 在共享后台把事标 done，Todo 还显示开着）。总管在 `evening-review` 顺手对账：读共享 open_loop 最新状态 → 飞书 Todo 里已 done 的勾掉、没了的清掉，让 App 视图追上真相。

## Pitfalls
- 1-3 件是上限，别摆一长串。
- **两处都要写、且去重**：先分域落共享 open_loop，再镜像飞书 Todo；重跑别建重复 loop（按 `created`=今天 + `source`=今日计划 查）。
- **只有总管写飞书 Todo**：专科 bot 不碰 Todo，避免一张清单多头写。
- **别因"Todo 已有"就不写共享后台**：每次规划都对齐两边，Todo 单边领先时回填后台（否则专科 bot 读后台读不到）。
- cron 场景别擅自往飞书 Todo 写——先提议、用户确认再落（外发/写入要可预览）。
- 浮出 loops 只是当背景，别把所有 open loop 一股脑塞成今日任务。
- `loops-due` 失败不致命：照常让用户口述今天计划，再建飞书 Todo。

## Verification
- 干跑：`research-assistant loops-due` 能跑。
- 端到端：确认后 ① 共享后台多出分域 loop（`loops-list --domain research` 看得到带 `source=今日计划` 的今天条目）；② 飞书 Todo 也出现同样的任务（App 可见）。
- 分身：科研 bot `loops-due --domain research` 能读到总管刚落的科研那条。
