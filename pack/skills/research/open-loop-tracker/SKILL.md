---
name: open-loop-tracker
description: 捕获和巡检开放循环（悬着的事/承诺）。捕获：用户"记一下 / 别让我忘了 X / 得催某人"→ 落库并判断 domain/下一步/负责人/优先级。巡检：cron 或"有啥悬着的"→ 挑该跟进的提醒，没有就闭嘴。
version: 2.0.0
platforms: [linux, macos]
metadata:
  hermes:
    tags: [research, work, follow-up, adhd]
    category: research
---

## When to Use
- **捕获**：用户"记一下 / 别让我忘了 / 我答应了 / 得催某人 …"——随口的承诺、悬着的事。
- **巡检**：cron 触发（默认下午/傍晚）；或用户"有啥悬着的事没 / 我还欠着啥"。

## A. 捕获（记一下 → loops-add，带上字段）
用户让你记一件悬着的事，**判断并带上这些字段再落库**：
```
research-assistant loops-add --tz <tz> --desc "<事>" --source "<哪来的>" \
  --domain <research|work|personal> --next-action "<下一个最小动作>" \
  --priority <low|medium|high|urgent> [--owner <谁>] [--due <YYYY-MM-DD>]
```
- **domain**：论文/实验/学习/写作 = research；回消息/审方案/项目/催人 = work；私人 = personal。拿不准默认 research。
- **next_action**：拆到"下一个最小动作"（不是"催张三"，是"发消息问接口字段定了没"）。**这条最重要，别只记个模糊的事**。
- **owner**：如果是"催/等某人"，owner = 那个人。
- **priority**：今天就要/卡着别的 = high/urgent；一般 = medium。
- **due**：有明确期限才带，用 `YYYY-MM-DD`。
落库后回一句确认（"记下了：<事>，下一步 <...>"）。

## B. 巡检（cron / "有啥悬着的"）
1. **取该跟进的**：`research-assistant loops-due --tz <tz>`（已按 overdue → 优先级 → 创建早 排序；可加 `--domain work` 只看某类）。可能为空。
2. **空 → 闭嘴**。别为了发而发。
3. **非空（判断活）**：读 `prefs.yaml` 的 `style`。
   - 挑**最多 1-3 件**最要紧的，别倒整张单。
   - 提醒时**直接带上 `next_action` 和 `owner`**——不是"有件事悬着"，是"催**张三**——下一步：**发消息问接口字段定了没**"。
   - 按 `style.accountability` 档语气；每件给出路："现在推一下？/ 专注一会？/ 先搁着？"
4. **按回应落账**（否则同一天会重复提醒）：
   - 做完 → `loops-resolve --id <id> --status done`
   - 不做了 → `loops-resolve --id <id> --status dropped`
   - 先搁着 → `loops-nudge --tz <tz> --id <id>`
   - 下一步变了 → `loops-update --id <id> --next-action "..."`（顺手更新）
5. （衔接 focus-buddy）想立刻做 → 引导进专注会话。

## Pitfalls
- 捕获时**尽量带 next_action**——一个没有下一步的开放循环，巡检时也推不动。
- domain 判断错不致命（可 `loops-update --domain` 改），但尽量分对，好让"工作上有啥悬着"筛得准。
- 巡检：空就别推；一次最多 1-3 件；无论结果都落一次 `loops-resolve`/`loops-nudge`。

## Verification
- 捕获："记一下我得催张三确认接口" → `loops-add` 带 `domain=work, owner=张三, next_action=...`。
- 巡检：`loops-due` 能跑；提醒里带下一步；`loops-nudge` 后当天不再出现。
