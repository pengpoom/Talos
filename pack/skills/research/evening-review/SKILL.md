---
name: evening-review
description: 每天晚上的复盘仪式：**从共享后台读今天做了啥（含各 bot 的进展）**，写时间轴，把没做完的转成开放循环，并**对账飞书 Todo 视图**（不读 today.json）。cron 触发或用户说"复盘今天"。
version: 2.1.0
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

1. **看今天做了啥（以共享后台为准 —— 这样才看得到各 bot 的进展）**：
   - **今日计划及其状态**：`research-assistant loops-list`（今天 `created`=今天、`source`=今日计划 的各域条目，含已 done / 仍 open——**专科 bot（如小研）改过的状态都在这**）。
   - **专注**：`research-assistant focus-stats` / `focus-log`（含小研陪你做的那几段）。
   - **项目**：对在跑项目 `research-assistant project-status --name <项目>` 看推进。
   - **科研软进展**：今天时间轴里带 `[研究]` 的行（读懂/想通/否了啥）——复盘时念一句，别只盯任务勾没勾。
   - **飞书 Todo（视图）**：用 `lark-task` 读一眼今天分区，主要为下一步**对账**用，别当唯一真相。
   - 可结合 `session_search` 翻今天聊过的进展。

2. **问进展 + 夸完成（判断活）**：逐项确认"这件做到哪了？还干了啥计划外的？"
   - 读 `style`：**先夸完成的**（`celebrate_wins` 为 true 时给庆祝），没完成的**不指责**（语气按 accountability 档）。

3. **记时间轴**（research-assistant 永久日志，飞书给不了）：把今天 **focus 之外**实际发生的逐条写进时间轴（**专注会话 `focus-end` 已自动记过，别重复**）：
   ```
   research-assistant timeline-append --tz <tz> --text "09:30-11:00 写 intro ✅"
   ```
   复盘里要回顾专注时长就用 `research-assistant focus-log` / `focus-stats` 读，别再 `timeline-append` 同一段。

4. **结清今日计划 + 没做完的处理**：
   - **今日计划那几条 loop**（`source=今日计划`）：做完的 `research-assistant loops-resolve --id <id> --status done`；没做完但值得继续的**留着**（它本就是 loop，会自然滚到明天），需要就 `loops-update` 改 next_action/due。
   - **计划外、新冒出来又没收尾的事**：`research-assistant loops-add --tz <tz> --desc "<没做完的事>" --source "未完成" --domain <research|work|personal> --next-action "<下一个最小动作>" --due <YYYY-MM-DD>`。

5. **对账飞书 Todo 视图（总管做）**：飞书 Todo 是单向镜像、会滞后（专科 bot 在共享后台标的 done，Todo 还开着）。用 `lark-task` 把今天分区**对齐共享 open_loop 的最新状态**：共享里已 done 的 → 勾掉对应 Todo；已 drop / 不存在的 → 清掉。让 App 视图追上真相。（只有总管干这步。）

6. **收尾**：给用户一句明天的引子。把复盘小结作为最终回复（cron deliver 飞书）。

## Pitfalls
- **专注会话已由 `focus-end` 自动入时间轴**，复盘时**别再 `timeline-append` 重复记**那几段；要回顾用 `focus-log`/`focus-stats` 读。
- 没做完 ≠ 指责。先肯定做到的。
- 只有用户确认"要继续"的才进 open_loops，别把所有未完成都一股脑塞进去变噪音。
- `--due` 必须 `YYYY-MM-DD`，别塞"明天 / today"这种词（否则 `loops-due` 排序认不出）。
- 不读 `today.json`（已退役）；**今天做了啥以共享后台为准**（loops/focus/项目/时间轴），飞书 Todo 只是要对账的视图。
- **对账只总管做**：专科 bot 不去改飞书 Todo。

## Verification
- 干跑：`research-assistant timeline-append` / `loops-list` / `focus-stats` 能跑。
- 端到端：触发后飞书收到复盘；复盘内容**含小研写的科研进展**（因为读的是共享后台）；`state/timeline/<date>.md` 有内容；今日计划 loop 该 done 的已 `loops-resolve`；飞书 Todo 视图对齐了共享状态。
