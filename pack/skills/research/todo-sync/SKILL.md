---
name: todo-sync
description: 总管把飞书 Todo 吸纳进共享后台——尤其用户【手填】的 Todo（绕过 Hermes 直接在飞书 App 建的），按 domain 吸成 open_loop、靠 todo_id 去重，让小研等子 agent 也读得到。cron 定时触发，或用户说"同步一下飞书 Todo / 我刚手填了个 Todo"。
version: 1.0.0
platforms: [linux, macos]
metadata:
  hermes:
    tags: [research, work, sync, todo]
    category: research
---

## When to Use
- **cron 定时**（每天几次）自动跑，捕获你手填的 Todo。
- 用户说"把飞书 Todo 同步进后台 / 我刚在飞书手填了个 Todo / 同步一下"。
- **只有总管跑**（它是飞书 Todo 的唯一管理者）；专科 bot 不跑、不碰 Todo。

## 干什么
飞书 Todo 既是"视图"又是"可选快速入口"——你有时图省事 / 嫌 Hermes 慢，直接在 App 手填一个 Todo。本技能把这些 Todo **吸纳**进共享后台（分域 `open_loop`），靠 `todo_id`（飞书 task GUID）去重，让小研等子 agent 也读得到。真相仍在共享后台，Todo 是入口。

## Procedure

1. **读飞书 Todo**：用 `lark-task` 读清单（今天分区 + 未完成项）。每条拿到：**task GUID**、标题、截止、完成状态。

2. **读共享后台**：`research-assistant loops-list`（拿全部 loop，含各自 `todo_id` 和 `desc`）。

3. **逐条对账（三种情况）**——对每个飞书 task：
   - **A. 已链接**（某 loop 的 `todo_id` == 这个 GUID；可 `loops-list --todo-id <GUID>` 直接判）→ **跳过**。可选：飞书已完成而 loop 还 open → `loops-resolve --id <id> --status done`（状态对齐）。
   - **B. 存在但没链接**（没 todo_id 匹配，但有个 loop 的 `desc` 跟标题明显同一件、且其 `todo_id` 为空）→ 这是总管之前建的、只是没连上 → `loops-update --id <loopid> --todo-id <GUID>` **补链接**（**别新建**）。
   - **C. 全新手填**（既无 todo_id 匹配、也无同名 loop）→ **吸纳**：
     ```
     research-assistant loops-add --tz <tz> --domain <判定> \
       --desc "<标题>" --source "飞书Todo手填" --todo-id <GUID> \
       [--due <task截止 YYYY-MM-DD>] [--next-action "<能拆就拆>"] [--priority <按 Todo 旗标>]
     ```
     - **domain 判定**：标题含论文/实验/写作 → research；回消息/审方案/项目/催人 → work；私人 → personal。**拿不准默认 work 或留空**（留空仍归总管，专科 bot 切不到那条，可接受）。

4. **静默原则**：没有新吸纳 / 无变化 → **别吭声**（cron 场景尤其）。有吸纳就给一句简报："从飞书 Todo 吸纳 N 条进后台：…（各归了什么域）"。

## Pitfalls
- **去重靠 `todo_id`，不是文本**：先 `loops-list --todo-id <GUID>` 判已吸纳没；文本匹配只用来**补链接（B）**，不用来新建。
- **别重复吸纳总管自己建的**：morning-plan 建的 loop 若没带 todo_id，会落到 B 分支 → 补链接，不是新建。
- **只有总管跑**：专科 bot 不跑本技能。
- domain 拿不准默认 work / 留空，别瞎归。
- 状态对齐是可选轻活，与 evening-review 对账都以**共享后台为真相**，不冲突。

## Verification
- 在飞书 App 手填一个 Todo → 跑 todo-sync → `loops-list` 多出一条带 `source=飞书Todo手填` + `todo_id`；**再跑一次不重复**（todo_id 去重生效）。
- 子 agent `loops-due --domain <域>` 能读到这条。
