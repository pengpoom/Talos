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

## Phase 2 已完成（同日晚）+ 工作侧起步
- ✅ **`morning-plan` / `evening-review` repoint 到飞书 Todo**（v2.0.0）：morning 浮出 `loops-due` → 提 1-3 件 → 确认后写飞书 Todo（不写 today.json）；evening 读飞书 Todo + `timeline-append` + `loops-add`（`--due` 强制 ISO；专注会话已由 focus-end 自动入时间轴，复盘不重复记）。`today-*` CLI 退役（代码/测试保留，67 测绿）。
- ✅ **cron 收编**：删 4 个通用"科研监督" + 多余 10:00 巡检，换成 **9:00 morning-plan(工作日) / 17:30 开放循环巡检(每天) / 22:00 evening-review(工作日)**，全挂 `--skill` + deliver 飞书。备份 `~/.hermes/cron/jobs.json.bak-20260601`。
- ✅ **5 个 MVP 功能全验证**：focus / open-loop(含 17:30 巡检实测) / morning-plan / evening-review / arxiv-digest(fetch 实测抓 50 篇；之前失败是限流/超时，非 bug)。
- ✅ **工作侧起步**（新 `work/` 分类，install.sh 已拷 + SOUL 加路由 + 自测过）：`draft-reply`（写回复/邮件/润色，默认只出草稿，明确说"直接发 X"才 `lark-im --as user` 代发）；`project-review`（按 `~/.hermes/research/review-sop.md` 或默认镜审方案，输出"问题/风险/建议/可发送意见/待追问"5 段）。

## 残留待办
- **provider fallback（最要紧）**：ppqq(`https://ppqq.997525.xyz/v1`) 反复抽风（502 / 单次 234s 龟速），`fallback_providers: []` 空 → 一抽风 bot 整个哑。`hermes fallback add` 配个备胎。
- **draft-reply 飞书授权**：首次读会话/查联系人触发 `missing_scope`，agent 已发设备码授权链接，用户点一下补 contact+im 权限即长期可用。
- **下一个工作技能**：`meeting-to-actions`（会议纪要拆 Todo）；`follow-up-nudger` 别单独做（≈ open-loop-tracker，并进去）。
- **会话习惯**：长会话曾被"陪我专注→建cron"养坏过，删会话 + 硬路由已解；新会话不受影响。
- **arxiv 韧性（可选）**：加 Retry-After/退避/缓存（once-daily cron 其实够用）。

## 怎么验（线上）
飞书发"陪我专注 2 分钟测试，任务写 X" → `cat ~/.hermes/research/state/focus.json` 应有 active:true + 你的 task。状态文件位置：`~/.hermes/research/state/`：`open_loops.json`、`focus.json`、`focus_log.jsonl`、`timeline/<date>.md`（`today.json` 已退役）。

## 约束（沿用）
- 中文回复；不加多余注释；不改已有函数签名；边写边跑 pytest。
- **git 操作只给命令、不替用户执行。**
- 本机环境：用 `python3`（无 `python`）；pytest 需 `python3 -m pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org pytest`（环境有 SSL 证书问题）。Hermes agent 跑在 gpt-5.5（自定义 provider）。部署：改技能后 `cp -r pack/skills/research/. ~/.hermes/skills/research/`（工作侧 `cp -r pack/skills/work/. ~/.hermes/skills/work/`）+ regex 合 SOUL（见 install.sh），再 `hermes gateway restart`；`pip install -e` 那步本机会被 SSL 卡，按需跳过（包已 editable 装好）。
