# Hermes 科研搭子 — 设计文档

- **日期**: 2026-05-29
- **状态**: 头脑风暴已通过，待用户复核 → writing-plans
- **范围**: Phase 1（自用 MVP）。Phase 2（开源分发）只预留接口，不实现。

---

## 1. 一句话

在 Nous Research 的开源框架 **Hermes Agent** 之上，做一套**科研搭子**技能包：每天主动盯你的科研日程、喂你精选 arXiv 论文，全程通过**飞书**交互。面向所有科研工作者，对 ADHD 尤其友好，**强度可调**。

本仓库（`hermes-poss`）是这套"包"的**源码仓库**；安装时把包铺进用户的 `~/.hermes/`。

---

## 2. 目标 & 非目标

### 目标（Phase 1 — 本 spec 范围）

- 自用 MVP：5 个核心功能跑通，日常用顺手。
- 混合架构：机械活脚本化（可测、稳、省 token），判断活交给 agent（灵活）。
- 面向所有科研工作者：强度与功能**可配置**（`prefs.yaml`）。
- 为 Phase 2 分发**预留接口**，但不实现分发本身。

### 非目标（Phase 2 / 以后，明确不做）

- 飞书"扫码即用"的发布应用 / OAuth 用户授权。
- 托管后端 / 多用户 / 计费 / Web 控制台。
- 多论文源（PubMed / bioRxiv）——只留接口，MVP 仅 arXiv。
- 精读陪伴 / 写作陪伴 / 周报月报 / 知识库 / 实验助手——二期（届时复用现有 `paper-reader`、`academic-polish-en` 技能）。

---

## 3. 目标用户

- 主用户：博士生 / 科研工作者，需要外部结构帮助推进研究产出。
- 设计偏好：**低摩擦**（点按钮 > 打字）、**问责强度可调**（温柔 ↔ 骂醒，4 档，见 §8）、**狠筛信息**、**防打扰**（只在该出现时出现）。这些对 ADHD 收益最大，但对所有人都是好搭子原则。
- 通过 `prefs.yaml` 的 `style.proactivity` 从"重度陪伴"到"安静工具"自由调档；功能可单独开关。

---

## 4. 依赖与环境约束（Hermes 事实）

以下事实**决定了**架构形态（来自 Hermes Agent 官方文档）：

- **记忆小且开局冻结**：`~/.hermes/memories/{MEMORY,USER}.md` 各 ~1–2KB，会话开始注入系统提示后整场不变 → **不能**存待办 / 历史。
- **cron 每次全新会话**：定时任务触发的是干净 agent，不记得之前 → **状态必须落盘文件接力**。
- **性格在 `SOUL.md`**；技能（`skills/<cat>/<name>/SKILL.md`，markdown + YAML frontmatter）是"步骤书"，非性格层。
- **`terminal` 工具**可跑任意 CLI / 脚本 → arXiv 抓取、`feishucli` 都靠它。
- **飞书**：自建应用 App ID/Secret（WebSocket 连接，无需公网）；支持向 **home chat 主动推送** + **交互卡片（按钮）**；"扫码"是扫码建应用，**不是**终端用户登录。
- **cron 配置** `~/.hermes/cron/jobs.json`：支持 cron 表达式 / 间隔 / 一次性延迟；触发跑 prompt（可挂技能），结果 `deliver` 到飞书。

**运行环境**：用户提供的 24h 常开机器（cron 可靠，无需妥协方案）。

---

## 5. 架构总览（混合）

```
cron 触发 → 干净 agent → 读 state/* → 判断活(LLM) → 发飞书卡片 → 写回 state/*
                          └──────── 因 cron 是新会话，全靠 state 文件接力记忆 ────────┘
```

- **脚本（机械活，确定性）**：arXiv 抓取 / 去重 / 预筛、状态原子读写。
- **agent（判断活，灵活）**：相关性排序、摘要、对话陪伴、复盘措辞。
- **state 文件**：跨"新会话"接力的记忆。

---

## 6. 目录结构

三层切割（= Phase 2 分发的天然切割线）：🟦 包（可分发） / 🟩 私有数据 / 🟥 密钥。

```
~/.hermes/
├── SOUL.md                       🟦 加入"科研搭子"人设（pack 给模板）
├── .env                          🟥 LLM key、飞书 App ID/Secret（已有）
├── cron/jobs.json                🟦 定时任务（pack 给模板）
├── skills/research/              🟦 五个功能技能（pack）
│   ├── morning-plan/SKILL.md
│   ├── evening-review/SKILL.md
│   ├── focus-buddy/SKILL.md
│   ├── arxiv-digest/SKILL.md
│   └── open-loop-tracker/SKILL.md
└── research/                     科研搭子自己的"家"
    ├── prefs.yaml                🟦→🟩 配置（pack 给模板，用户填）
    ├── bin/                      🟦 脚本（机械活）
    │   └── arxiv_fetch.py        抓取 + 去重 + 预筛
    └── state/                    🟩 私有数据（自动生成）
        ├── today.json
        ├── open_loops.json
        ├── timeline/2026-05-29.md
        └── papers/
            ├── seen.jsonl
            └── digest-2026-05-29.md
```

> `feishucli`（用户已装）是"飞书落点"的执行器（建任务 / 写日历），技能与脚本通过 `terminal` 调用它。

---

## 7. 组件

| 功能 | 性格层 `SOUL.md` | 技能（怎么做） | 脚本（机械活） | 定时 `cron` | 飞书落点 |
|---|---|---|---|---|---|
| 晨间规划 | 主动·拆到下一步 | `morning-plan` | 读 prefs / 开放循环 / 昨日未完 | 08:30 | home chat 卡片 + 任务 |
| 专注陪伴 | 陪伴·问责可调 | `focus-buddy` | （计时，纯 agent 即可） | 你喊才启（一次性闹钟） | 卡片 check-in |
| 晚间复盘+时间轴 | 夸·问责可调 | `evening-review` | 写 today/timeline，同步日历 | 22:00 | 卡片 + 日历 |
| 开放循环追踪 | 接住掉的事 | `open-loop-tracker` | 扫开放循环 + 时间戳 | 14:00 & 18:00（有事才发） | home chat 提醒 |
| 论文日报 | 狠筛 | `arxiv-digest` | `arxiv_fetch.py` 抓+去重 | 09:00 | home chat 卡片 |

- **SOUL.md 人设**：主动但不噪音、把大任务拆到"下一个最小动作"、接住你掉的事、夸进步、**问责强度可调（温柔↔骂醒）**、狠筛信息；读 `prefs.yaml` 调频率、问责强度与语气。
- **交互优先级**：**卡片按钮优先**（点一下 < 打一段字），直接回消息兜底。

---

## 8. 配置 `prefs.yaml`

"面向所有科研工作者"全靠这一个文件（pack 给模板，用户填）：

```yaml
timezone: Asia/Shanghai
name: 你的名字

arxiv:
  categories: [cs.RO, cs.LG, cs.CL, eess.SY]
  keywords: ["robotic manipulation", "LLM agent", "model predictive control"]
  max_per_day: 5
  # source: arxiv        # 🔌 预留：以后可加 pubmed / biorxiv（接口留好）

schedule:                # 留空 = 关掉该功能的定时
  morning_plan:    "08:30"
  paper_digest:    "09:00"
  open_loop_check: ["14:00", "18:00"]
  evening_review:  "22:00"

style:                   # 🎚️ 搭子强度（"面向所有人"的旋钮）
  proactivity: high      # 提醒频率: high(频繁) | medium | low(基本静默，只在你主动时出现)
  accountability: gentle # 问责强度: gentle(温柔) | firm(坚定) | tough(严格) | savage(骂醒/狠话)
  celebrate_wins: true

features:                # 🔌 功能开关
  morning_plan:      true
  paper_digest:      true
  focus_buddy:       true
  open_loop_tracker: true
  evening_review:    true
```

**`style.proactivity` 如何落地**：(1) 启用 / 禁用哪些 cron（`schedule` 留空即关）；(2) 各技能读取 `proactivity`，调整提醒频率。`low` ≈ 只留论文日报 + 你主动时才出现。

**`style.accountability` 四档**（技能 / SOUL.md 据此调措辞，每档都**只针对行为、不否定你这个人**）：

- `gentle` 温柔：鼓励为主，不施压，不制造负罪感。
- `firm` 坚定：直说"你这事拖 3 天了"，对事不对人，适度施压。
- `tough` 严格：严师式强力催，戳你拖延的痛点，盯得紧。
- `savage` 骂醒：允许更冲、更扎心的狠话逼你动（仍守不人身羞辱的底线）。

---

## 9. 状态文件 schema

| 文件 | 存什么 | 关键字段 |
|---|---|---|
| `state/today.json` | 今日计划 + 完成 | `date`；`plan[]`（`id` / `task` / `next_action` / `feishu_task_id` / `done`）；`current_focus`（`goal` / `started_at` / `until`）；`unplanned_done[]`；`logged` |
| `state/open_loops.json` | 开放循环 | 数组，每条：`id` / `desc` / `created` / `last_nudged` / `status`(open·done·dropped) / `due` / `source` |
| `state/timeline/<date>.md` | 当天时间轴 | 人类可读；顺便喂以后的周报 |
| `state/papers/seen.jsonl` | 已推论文 | 每行一个 arXiv id（去重）；**仅成功推送后写入** |
| `state/papers/digest-<date>.md` | 日报存档 | 当天推送原文 |

**谁会进 `open_loops`**：晨间没排进今日但提过的、碎念里的"要做 X"、复盘没完成又重要的、deadline 类。agent 在各流程里顺手写入。

---

## 10. 数据流（5 流程）

**通用模式**：`cron 触发 → 干净 agent → 读 state/* → 判断活(LLM) → 发飞书卡片 → 写回 state/*`

**① 晨间规划 · 08:30**
1. 读 `today.json`（昨日未完）+ `open_loops.json` + `prefs.yaml`。
2. 生成"今天聚焦 1–3 件"，每件拆到"下一个最小动作"。
3. 发 home chat 卡片：建议 + 按钮【就这么定】【我改改】。
4. 确认/修改 → 写 `today.json` + feishucli 建飞书任务（可选给日历占块）。

**② 论文日报 · 09:00**
1. 跑 `arxiv_fetch.py`：按 `categories` + `keywords` 拉昨日新论文 → 对 `seen.jsonl` 去重。
2. agent 判断活：相关度排序、狠筛 3–5 篇，每篇写"为什么相关 + 精读/扫一眼/跳过"。
3. 发卡片：一篇一块 + 按钮【精读这篇】（→ 二期）。
4. 存档 `digest-<date>.md`，推过 id 进 `seen.jsonl`。

**③ 专注陪伴 · 你喊才启**
1. 你说"专注 25 分钟写 intro" → 把目标写进 `today.json.current_focus`。
2. 起一次性闹钟（cron relative delay `25m`）。
3. 时间到 → 干净 agent 读 `current_focus` → check-in："搞定了吗？再来一轮 / 歇 5 分钟？"
4. 完成 → 计入 `today.json` + 即时正反馈 🎉。

**④ 开放循环追踪 · 14:00 & 18:00**
1. 读 `open_loops.json`。
2. agent 判断"谁该戳了"（悬太久 / 和今日计划相关 / deadline 临近）——**只有真有该戳的才发**（防噪音，对 ADHD 极重要）。
3. 发提醒 + 按钮【现在做】【晚点】【已做了】【删掉】→ 更新 `open_loops.json`。

**⑤ 晚间复盘 + 时间轴 · 22:00**
1. 读 `today.json`（计划 + 已记录完成）。
2. 卡片问："这几件做到哪了？还干了啥计划外的？"（可勾选）。
3. agent 先夸完成的 → 没完成的不指责，问滚明天还是进 `open_loops`。
4. 写时间轴 `timeline/<date>.md` + 同步飞书日历；更新 `open_loops`，给明天留引子。

---

## 11. 错误处理（原则：宁可降级，绝不静默卡住）

| 出啥事 | 怎么扛 |
|---|---|
| arXiv 抓不到 | 退避重试 3 次；仍失败 → 飞书软提示，1h 后自动再试 / 回"重试"。`seen.jsonl` 仅成功后更新，失败不害明天漏论文 |
| feishucli 失败 | 计划先存本地 `today.json`，绝不丢；提示"建任务失败，方便时说一声我重建" |
| cron 漏跑（重启/更新） | 看 `today.json` 日期戳：发现今天没跑 → 你一上线就补；同日防重复 |
| LLM 报错/超额 | 降级：论文日报给原始候选列表（标注 AI 排序挂了）；专注退化成纯计时。不让你干等 |
| 状态文件损坏/并发写 | "临时文件 + 改名"原子写；读到坏 json 备份+重建+告警。五流程时间错开，碰撞极少 |
| 时区/日期边界 | 统一用 `prefs.timezone`，日期字符串走单一 helper |

---

## 12. 测试策略

- **脚本 = 单元测试（pytest）**：`arxiv_fetch.py` 用录好的 arXiv 返回做 fixture，测去重 / 筛选 / 空结果 / 超 `max_per_day`；状态读写测原子写 + 坏文件恢复。
- **流程 = 干跑（dry-run）**：开关使流程发到**测试聊天**、用固定"今天"日期，配合 `hermes cron run <job>` 手动立刻触发，肉眼看输出；配样例 `today.json` / `open_loops.json` 喂复盘与巡检。
- **不过度测**：不测 LLM 具体措辞（本就会变），只测管道（抓没抓到、去没去重、推没推、状态写没写、出错降没降级）。

---

## 13. 分发预留（Phase 2 hooks，现在只"不挡路"）

- ✅ 包 / 数据 / 密钥三层已分离 → "包" = `skills/research` + `bin` + `SOUL.md 模板` + `prefs.yaml 模板` + `cron 模板`，一个目录拷走。
- ✅ 零硬编码：技能 / 脚本不写死个人路径 / id，全读 `prefs.yaml` / `.env`。
- ✅ 一键安装雏形：`setup` 脚本——拷包 → 从模板生成 `prefs.yaml` → 注册 cron → 交互式填空（方向 / 时间 / 强度）。MVP 可简陋。
- ✅ 论文源接口留好：`arxiv_fetch` 藏在干净接口后，以后 pubmed / biorxiv 直接插。
- 🚫 现在不做：飞书发布应用 / 托管后端 / 多用户 / 计费 / Web 控制台。

---

## 14. 待填 / 实施时确认

- arXiv `categories` / `keywords` 的真实方向（当前占位：`cs.RO` / `cs.LG` / `cs.CL` / `eess.SY`）。
- 接哪家 LLM provider / model（用户已有，接 Hermes，不影响架构）。
- 提醒时间已定：08:30 / 09:00 / 14:00 & 18:00 / 22:00。
- 飞书 home chat 是否已 `/set-home`；`feishucli` 建任务 / 写日历的确切命令格式（对照其 help / 文档）。
- 飞书交互卡片按钮回调在当前 Hermes 版本的可用性（文档称支持 command-approval 卡片，实施时验证）。
