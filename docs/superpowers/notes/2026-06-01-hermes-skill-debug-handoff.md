# 交接 note：Hermes 技能不执行 —— 已定位并修复（Phase 1 完成）

> 2026-06-01 更新：原假设（技能没登记进 `DESCRIPTION.md` / 没被加载）**已证伪**。真因已查清并修了，专注链路端到端验证通过。下面是真相 + 已做 + 待办（Phase 2）。

## 真因（证据来自 `state.db` 真实对话 + `.usage.json` + `agent.log`）
技能**确实加载了**——06-01 11:22 agent 真的 `skill_view focus-buddy` 并跑过 `research-assistant focus-start`（msg 1242）；`arxiv-digest`/`evening-review`/`focus-buddy` 在 `.usage.json` 里都有使用记录。CLI 本身也 100% 正常（手动 + 经 agent 全链路都写出了状态）。病根是三条叠加：

1. **写类 CLI 命令静默无输出**：`focus-start`/`today-set-plan`/`loops-add`… 跑完啥都不打印（agent 当时看到的就是空的 `"\n"`）。LLM agent 拿不到"我确实落库了"的确认 → 不信任、不复用 → 退回飞书原生 cron。唯一稳定可用的 `focus-end` 恰好是**唯一会回显 JSON** 的写命令。
2. **agent 自建"影子技能"抢戏**：`focus-session-companion`(04:28) 和 `feishu-personal-productivity-workflows`(06:12) 都是 agent 自己写的，描述直接吃掉"陪我专注/规划今天"，但内部**只用 lark-task + 原生 cron，一个字不提 research-assistant**。导致 `morning-plan`/`open-loop-tracker` 从没被选用过（`.usage.json` 里根本没有它俩）。
3. **没有权威路由 + 强会话习惯**：长会话里 `lark-task` 用了 25 次，agent 形成"日常事一律走飞书原生"的惯性，没有规则把这些意图钉回 research-assistant。

## 产品决策（用户拍板）：**混合方案 —— Todo 归飞书**
- **专注 / 开放循环 / 论文日报 / 时间轴 → research-assistant CLI**（强制，必须真执行）。
- **todo / 规划今天 → 飞书 Todo（lark-task）**，让用户在飞书 App 里看得见，不写 `today.json`。
- **复盘 → 读飞书 Todo 看做了啥 + research-assistant 记时间轴/收开放循环**。

## 已做（Phase 1，已验证）
1. **CLI 全部写命令回显结果 JSON**（`src/research_assistant/cli.py` 9 处：today-set-plan/mark-done/add-unplanned/log、loops-add/nudge/resolve、timeline-append、focus-start）。改 1 个测试加 drain。`PYTHONPATH=src python3 -m pytest -q` → **67 passed**。
2. **SOUL 加"工具路由（硬规则）"段**（`pack/SOUL.snippet.md` → 经 install 的 regex 合并到 `~/.hermes/SOUL.md`）。把上面的混合分流写成硬规则，并明令"别自建影子技能替代 research-assistant 流程"。
3. **`focus-buddy` description 收紧**（强占"陪我专注/盯着我/body double" + 明示"必须用 research-assistant CLI 落库"）。
4. **删掉影子技能 `focus-session-companion`**（备份在 `~/.hermes/skills/.shadow-backup-20260601/`）。
5. **改 `feishu-personal-productivity-workflows`**：把"Focus companionship"段改成委派给 focus-buddy（保留它的飞书 Todo 约定，那部分符合混合方案）。
6. `hermes gateway restart`（技能在 gateway 启动时载入）。

**验证**：干净会话 `hermes -z "陪我专注 2 分钟…任务：调试验证"` → agent 选了 focus-buddy（use_count 2→3）→ **真写出 `focus.json`**（task=调试验证, planned_min=2）→ `focus-end` 收尾也正常。曾经"只动嘴不落库"的 bug 没了。

## 二次修复（同日，线上复测暴露两个新点）
1. **坑（我自己造的）**：删影子技能后我把它备份到 `~/.hermes/skills/.shadow-backup-20260601/`——**这在 skills 根里面**，加载器递归扫描就把它当技能又载回来了。gpt‑5.5 选技能带随机性，于是有的"陪我专注"又选回 focus-session-companion 走原生 cron。**教训：技能备份必须放到 skills 根之外**（已移到 `~/.hermes/.shadow-backup-skills-20260601/`）。
2. **长会话习惯**：这个线上会话（history 140+）"陪我专注 → 直接建 cron、跳过 focus-start"重复了十来次，agent 有时**根本不 skill_view、直接照旧建 cron**。光删影子技能不够。修法：把 SOUL 的专注规则升级成**硬流程顺序门**——"收到专注请求，第一个工具调用必须是 `focus-start`；落库成功前禁止建 cron、禁止发'我在盯着'"。升级后在同一个线上会话 `hermes -z` 连测 **4/4 都落库**。
   - 备选核弹：`hermes sessions delete <id>` 删掉被污染的会话，下条飞书消息即开新会话（干净会话本来就稳）。代价：丢当天和 bot 的聊天记忆（Todo/状态在外部存储，不丢）。

## 三次修复（线上真实使用暴露的时区 bug）
确认核心修复在飞书全新会话里**生效**了（投简历、读论文都正常 focus-start + focus-end 入账）。但暴露一个时区 bug：到点的**自动收尾 reminder 跑 `focus-end` 时没带 `--tz`**，而 CLI 的 `--tz` 默认是 `UTC` → `ended` 记成 UTC（08:31），`started` 是 CST（16:27），naive 字符串相减得 `elapsed_min: -476`。
- 修法①（根因）：`cli.py` 加 `_default_tz()`，所有 `--tz` 默认从 `default="UTC"` 改成读 `prefs.timezone`（用户是 Asia/Shanghai）——省略 `--tz` 也和 focus-start 一致。
- 修法②（兜底）：`focus.elapsed_minutes` 夹 `max(0, …)`，永不为负。
- `tests/test_focus.py` 加回归断言（16:27→08:31 应得 0）。`pytest -q` → **67 passed**。CLI 是 editable 装，改完即生效，无需重启/重部署。
- 注：agent 当时**自己发现并改正了 `focus_log.jsonl`** 那条负数（改成 4min），只漏了 `focus.json`——我已补正。

## 待办（Phase 2，按混合方案收尾）
- **`morning-plan` / `evening-review` 仍跑 `today.json`**，与"Todo 归飞书"冲突（SOUL 规则已把规划/复盘指向飞书，但这俩技能的 procedure 还在写/读 today.json）。要把它们 **repoint 到 lark-task（飞书 Todo）**：morning-plan 把计划写进飞书 Todo + 保留 `loops-list` 浮出悬着的事；evening-review 读飞书 Todo 看完成度 + 保留 `timeline-append`/`loops-add`。这会让 `today-*` 子系统基本退役（代码留着无害，测试照绿）。
- **cron**：morning-plan(08:30)/evening-review(22:00) 的定时还在跑 today.json 流，Phase 2 一起调。
- **会话习惯**：线上那个长会话（history 140+）有 lark-task×25 的惯性；干净会话测试已过，但老会话里可能仍偶发漂移。SOUL 规则每条消息都加载，应能压住；要最干净就开个新飞书会话测。

## 怎么验（线上）
飞书发"陪我专注 2 分钟测试，任务写 X" → `cat ~/.hermes/research/state/focus.json` 应有 active:true + 你的 task。状态文件位置：`~/.hermes/research/state/`：`today.json`、`open_loops.json`、`focus.json`、`focus_log.jsonl`、`timeline/<date>.md`。

## 约束（沿用）
- 中文回复；不加多余注释；不改已有函数签名；边写边跑 pytest。
- **git 操作只给命令、不替用户执行。**
- 本机环境：用 `python3`（无 `python`）；pytest 需 `python3 -m pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org pytest`（环境有 SSL 证书问题）。Hermes agent 跑在 gpt-5.5（自定义 provider）。部署：改技能后 `cp -r pack/skills/research/. ~/.hermes/skills/research/` + regex 合 SOUL（见 install.sh），再 `hermes gateway restart`；`pip install -e` 那步本机会被 SSL 卡，按需跳过（包已 editable 装好）。
