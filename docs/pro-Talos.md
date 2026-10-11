我会把 **Talos** 设计成一个：



> **以 Open Loop 为核心、以飞书为操作界面、基于 Hermes 的多 Agent 个人科研/工作操作系统。**



它不是“一个更会聊天的机器人”，而是一个长期帮你维护 **任务、项目、论文、专注、日程、文档、复盘** 的助手。



你现在截图里的科研功能其实已经形成了一个雏形闭环：



| 当前科研功能            | 本质能力       | 可以抽象成 Talos 的核心能力 |

| ----------------- | ---------- | ----------------- |

| focus-buddy       | 陪你进入专注状态   | 专注/执行陪伴           |

| open-loop-tracker | 记住未闭环事项并巡检 | 开放循环管理            |

| arxiv-digest      | 定时抓论文、筛论文  | 信息雷达/研究情报         |

| morning-plan      | 规划今天       | 每日计划/优先级排序        |

| evening-review    | 复盘今天       | 反思/沉淀/明日准备        |



所以 Talos 的核心不应该先分“科研助手”和“工作助手”，而应该先抽象成：



> **Talos 管的是一个人的所有 Loop：学习 Loop、论文 Loop、项目 Loop、工作 Loop、沟通 Loop、专注 Loop。**



科研和工作只是 Loop 的不同类型。



---



# 1. Talos 的顶层定位



我建议定义为：



> **Talos 是一个飞书原生的多 Agent 个人执行系统。它会记住你的开放事项，帮助你规划、专注、产出、复盘，并在需要时操作飞书 Todo、日历、云文档、群聊和知识库。**



核心关键词：



```text

Open Loop

Daily Plan

Focus Session

Paper Digest

Work Draft

Project Review

Follow-up

Memory

Feishu Actions

Human Confirmation

```



也就是说，Talos 的日常形态应该是这样的：



早上：



> 你今天有 3 个工作待办、2 个科研待办、1 篇论文值得看。建议上午先处理 A 项目审核意见，下午安排 90 分钟读论文。



工作中：



> 你说“记一下，别让我忘了跟张三确认接口字段”，Talos 自动记录成 open loop，并在合适时间提醒。



专注时：



> 你说“陪我专注 50 分钟写论文 related work”，Talos 记录 session，结束后问你产出，并更新研究日志。



晚上：



> Talos 汇总今天完成了什么、哪些 Loop 没闭合、明天应该先做什么。



这就是一个完整的私人科研/工作搭子。



---



# 2. Talos 的核心抽象：Open Loop



我强烈建议你把 **Open Loop** 做成 Talos 的第一核心对象。



因为科研和工作里最共性的东西不是“文档”或“聊天”，而是：



> 有一件事情还没有闭环。



比如科研里：



* 有一篇论文要读

* 有一个实验要跑

* 有一个公式没理解

* 有一个数据要提取

* 有一个 section 要写

* 有一个审稿意见要回复



工作里：



* 有一封邮件要回

* 有一个方案要审核

* 有一个人要催

* 有一个会议纪要要发

* 有一个用户指南要写

* 有一个项目风险要跟进



这些本质上都是 Open Loop。



建议 Talos 内部有统一结构：



```ts

type OpenLoop = {

  id: string

  domain: "research" | "work" | "personal"

  title: string

  project?: string

  source: "chat" | "todo" | "calendar" | "doc" | "manual"

  status: "open" | "planned" | "doing" | "blocked" | "waiting" | "done"

  priority: "low" | "medium" | "high" | "urgent"

  due_at?: datetime

  next_action: string

  owner?: string

  related_docs?: string[]

  related_people?: string[]

  evidence_refs?: string[]

  last_touched_at: datetime

  reminder_policy?: string

}

```



这个对象非常重要。



以后无论是：



```text

“记一下”

“帮我规划今天”

“复盘今天”

“有哪些悬着的事”

“这个项目卡在哪”

“最近科研有哪些没推进”

```



本质都是在操作 OpenLoop。



---



# 3. Talos 的多 Agent 架构



不要把多 Agent 理解成“一堆人格聊天”。更好的设计是：



> **Orchestrator 负责理解用户意图，Specialist Agents 负责不同类型任务，Tool Agent 负责飞书执行，Critic Agent 负责检查风险。**



我建议 Talos 分成这些 Agent。



## 3.1 Talos Commander：总调度 Agent



这是主入口，用户在飞书里聊天时面对的就是它。



职责：



* 理解用户意图

* 判断是科研、工作、计划、专注、复盘、工具操作还是闲聊

* 选择合适的子 Agent

* 维护任务状态

* 决定是否需要用户确认

* 汇总最终结果



例如用户说：



> 帮我规划今天。



Commander 会调用：



```text

Memory Agent

Todo Agent

Calendar Agent

Research Agent

Work Agent

Planner Agent

```



然后输出今日计划。



---



## 3.2 Memory Agent：记忆 Agent



这是 Talos 的长期记忆中心。



它不负责写文章、不负责执行工具，只负责回答：



> 我知道你是谁、你在做什么、你过去怎么做。



它应该维护几类记忆：



```text

UserProfile：你的称呼、作息、偏好、语气、确认习惯

ProjectMemory：科研项目、工作项目、当前阶段、相关文档

PeopleMemory：同事、合作者、导师、用户、沟通偏好

WorkflowMemory：你的 SOP、审核标准、写作流程

TemplateMemory：邮件模板、审核意见模板、周报模板

DecisionMemory：过去做过的重要决定和原因

```



例如它应该记住：



```text

- 用户不喜欢 AI 自动发送正式消息

- 外发内容必须先预览确认

- 科研相关输出需要带来源

- 工作审核意见偏好“问题-风险-建议-下一步”结构

- 用户希望 Talos 像监督搭子，而不是只做问答

```



---



## 3.3 Research Lead：科研主 Agent



科研主 Agent 负责管理所有科研 Loop。



下面可以拆成几个子 Agent：



| Agent              | 职责                        |

| ------------------ | ------------------------- |

| Paper Scout        | 找论文、下载论文、arXiv 日报、关键词监控   |

| Paper Reader       | 读 PDF、总结论文、提取贡献、方法、实验     |

| Data Extractor     | 从论文里提数据、表格、实验条件、指标        |

| Study Buddy        | 陪你一起学论文、提问、解释公式、生成复习卡片    |

| Writing Agent      | 帮你写论文段落、related work、审稿回复 |

| Research Log Agent | 记录今天读了什么、学了什么、实验进展        |

| Focus Buddy        | 陪你专注、记录专注时长、追踪产出          |



你现在已有的功能可以归入这里：



```text

focus-buddy      -> Focus Buddy

arxiv-digest     -> Paper Scout

morning-plan     -> Planner Agent + Research Lead

evening-review   -> Review Agent + Research Log Agent

open-loop-tracker -> Open Loop Agent

```



---



## 3.4 Work Lead：工作主 Agent



工作 Agent 和科研 Agent 的区别是：



科研强调：



```text

证据、文献、实验、知识沉淀

```



工作强调：



```text

沟通、任务、项目、交付物、跟进

```



Work Lead 下面可以拆成：



| Agent           | 职责                 |

| --------------- | ------------------ |

| Inbox Agent     | 整理飞书消息、待回复事项、群聊结论  |

| Draft Agent     | 写邮件、飞书回复、审核意见、用户说明 |

| Meeting Agent   | 会议准备、会议纪要、提取待办     |

| Project Agent   | 管理项目状态、风险、里程碑、负责人  |

| Review Agent    | 审方案、审文档、按 SOP 找问题  |

| Follow-up Agent | 催办、提醒、跟进未闭环事项      |

| Report Agent    | 生成日报、周报、月报、项目进展    |

| Docs Agent      | 创建、修改、整理飞书云文档      |



工作 Agent 的核心能力不是“自动干活”，而是：



> 把散乱信息变成可交付文本和可执行任务。



比如：



```text

输入：这几个点帮我写成审核意见。

输出：问题、风险、建议、可发送版本。



输入：这段会议纪要帮我拆 Todo。

输出：任务、负责人、截止时间、是否写入飞书 Todo。



输入：这个项目现在卡在哪？

输出：当前状态、风险、下一步、待跟进人。

```



---



## 3.5 Planner Agent：计划 Agent



Planner 是连接科研和工作的关键。



它负责：



* 每日计划

* 时间块安排

* 优先级排序

* 专注 session 安排

* 根据日历和 Todo 调整计划

* 判断哪些事今天必须做，哪些可以推迟



它应该读取：



```text

Feishu Calendar

Feishu Todo

OpenLoop Store

ProjectMemory

Focus History

Deadline

User Energy Pattern

```



输出：



```text

今日必须完成

今日建议推进

适合专注的任务

可以顺手处理的小任务

需要跟进的人

建议的时间块

```



---



## 3.6 Review Agent：复盘 Agent



Evening Review 不应该只是“今天怎么样”，而要变成记忆写入入口。



它负责：



* 汇总今天完成事项

* 汇总专注时长

* 找出未闭环事项

* 识别拖延的 Loop

* 生成明日建议

* 写入 Research Log / Work Log

* 更新周报素材



晚上 Talos 可以问：



```text

今天 A 项目审核意见完成了吗？

论文 X 读完了吗？

你下午 50 分钟专注 session 的产出是什么？

今天有 2 个 open loop 没处理，要不要安排到明天？

```



这会让 Talos 真的像监督搭子。



---



## 3.7 Tool Executor：工具执行 Agent



这个 Agent 专门负责调用飞书 CLI/API。



它不应该自己做决策，只负责执行已经确认的动作。



可以支持：



```text

飞书 Todo：创建、更新、完成任务

飞书 Calendar：创建时间块、会议、提醒

飞书 Docs：创建文档、追加内容、生成纪要

飞书 Sheets/Base：维护论文库、项目表、专注记录

飞书 Messenger：发送私聊提醒、生成群消息草稿

飞书 Drive：保存论文、文档、资料

```



重点是：**执行和决策分离。**



Planner 可以建议：



> 明天下午安排 90 分钟读论文。



Tool Executor 只负责：



> 用户确认后，在日历里创建时间块。



---



## 3.8 Safety / Critic Agent：安全和质检 Agent



这个很关键。



Talos 能操作 Todo、日历、云文档后，必须有一个专门的安全层。



它负责判断：



* 这个动作是否会影响别人？

* 是否会修改共享文档？

* 是否会发送消息？

* 是否代表用户承诺 deadline？

* 是否涉及敏感信息？

* 是否需要二次确认？

* 输出内容是否过于武断？

* 科研结论有没有来源？

* 工作审核意见是否语气不合适？



建议 Talos 所有动作走这个流程：



```text

Plan -> Preview -> Confirm -> Execute -> Log

```



也就是：



```text

先计划

再预览

用户确认

再执行

最后记录

```



---



# 4. Talos 的核心技能体系



你现在已有的科研技能可以保留，但建议统一成 Skill Manifest。



每个技能都应该有固定结构：



```yaml

skill_id: focus-buddy

domain: research

trigger:

  - "陪我专注 X"

  - "开始专注"

tools:

  - calendar

  - todo

  - focus_log

memory_read:

  - user_profile

  - open_loops

memory_write:

  - focus_session

  - daily_log

approval_level: low

output:

  - focus_plan

  - end_review

```



这样以后扩展工作技能会更清晰。



---



# 5. 当前科研功能怎么整理



你现在截图里的功能，我会这样重新组织。



| 功能   | 技能名                 | Talos 中的位置      | 下一步建议             |

| ---- | ------------------- | --------------- | ----------------- |

| 专注陪伴 | `focus-buddy`       | Focus Buddy     | 已经可以作为稳定技能        |

| 开放循环 | `open-loop-tracker` | Open Loop Agent | 应该升级为全系统核心对象      |

| 论文日报 | `arxiv-digest`      | Paper Scout     | 需要异步队列、缓存、失败重试    |

| 规划今天 | `morning-plan`      | Planner Agent   | 接入飞书 Todo 后价值会大很多 |

| 复盘今天 | `evening-review`    | Review Agent    | 接入专注记录、Todo、论文记录  |



尤其是 `open-loop-tracker`，我建议你不要只把它当一个功能，而是把它升级成 Talos 的核心数据库。



因为之后所有功能都会依赖它：



```text

morning-plan 读取 open loops

evening-review 更新 open loops

focus-buddy 绑定 open loop

work-followup 追踪 open loop

paper-reading 生成 open loop

meeting-minutes 生成 open loop

```



---



# 6. 工作助手应该补哪些技能



工作助手可以沿用科研助手的结构，只是技能不同。



## 6.1 `work-inbox-digest`



触发：



```text

"看看我今天有哪些消息要处理"

"帮我整理飞书未读"

"今天有什么需要回复"

```



功能：



* 读取飞书消息/群聊摘要

* 找出需要回复的消息

* 找出被 @ 的事情

* 找出潜在任务

* 生成待处理清单



输出：



```text

今天你需要处理 4 件事：



1. A 项目群里张三问接口字段，需要回复

2. B 用户反馈希望今天给说明

3. C 文档有人评论了 2 条，需要确认

4. 下午 3 点会议前要补充方案风险说明

```



---



## 6.2 `draft-reply`



触发：



```text

"帮我回一下"

"把这段写正式点"

"帮我写封邮件"

"帮我写个委婉的催办"

```



功能：



* 按对象调整语气

* 生成飞书回复/邮件/公告

* 支持正式、委婉、强硬、简洁、用户友好等风格

* 默认只生成草稿，不自动发送



输出：



```text

我给你写了两个版本：



版本 A：委婉

……



版本 B：更直接

……



需要我放到飞书输入框/文档里吗？

```



---



## 6.3 `project-review`



触发：



```text

"帮我审这个方案"

"按我的 SOP 看看有什么问题"

"帮我写审核意见"

```



功能：



* 读取方案文档

* 按 SOP 检查

* 输出问题、风险、建议

* 生成可发送审核意见



输出结构固定：



```text

一、主要问题

二、风险判断

三、修改建议

四、可发送审核意见

五、需要追问的问题

```



这个技能非常适合你截图里那个人的需求。



---



## 6.4 `meeting-to-actions`



触发：



```text

"把这段会议纪要拆成 Todo"

"总结这个会议"

"帮我生成会议纪要"

```



功能：



* 整理会议结论

* 提取决定

* 提取待办

* 识别负责人和截止时间

* 用户确认后写入飞书 Todo

* 可生成群消息草稿



输出：



```text

识别到 3 个待办：



1. 补充测试方案

   负责人：你

   截止：周三

   项目：A 项目



2. 确认接口字段

   负责人：张三

   截止：周二

   项目：A 项目



是否创建到飞书 Todo？

```



---



## 6.5 `follow-up-nudger`



触发：



```text

"有哪些事该催了"

"帮我催一下张三"

"这周有哪些悬着的事"

```



功能：



* 扫描 open loops

* 找出超过时间没更新的事项

* 生成催办话术

* 按关系和场景调整语气



输出：



```text

有 2 件事建议今天跟进：



1. 张三 - A 项目测试方案

   已超过原计划 1 天。

   建议话术：

   “张三，这边想确认一下 A 项目测试方案目前进展如何？如果有需要我补充的信息可以随时说。”



2. 李四 - 接口字段确认

   今天下午会议前需要结果。

```



---



## 6.6 `deliverable-builder`



触发：



```text

"帮我写用户指南"

"把这个整理成 FAQ"

"帮我生成项目周报"

"把这段内部说明改成给用户看的版本"

```



功能：



* 生成用户指南

* 生成 FAQ

* 生成项目汇报

* 生成操作说明

* 生成上线通知

* 生成风险说明

* 根据对象切换版本



同一件事可以输出不同版本：



```text

给领导版：结论先行、风险和资源

给用户版：少技术词、解释影响和替代方案

给研发版：明确问题、接口、测试、时间点

```



这就是工作助手的强需求。



---



# 7. 科研和工作的统一技能矩阵



Talos 可以把科研和工作统一成一张能力矩阵。



| 通用能力      | 科研场景          | 工作场景           |

| --------- | ------------- | -------------- |

| 信息雷达      | arXiv 日报、论文推荐 | 消息摘要、项目动态、待回复  |

| Open Loop | 待读论文、待跑实验     | 待回复、待审核、待催办    |

| 计划        | 今日读论文/写作/实验   | 今日会议/文档/评审/沟通  |

| 专注        | 陪读论文、写论文      | 陪写文档、处理方案、集中审核 |

| 产出        | 论文笔记、实验记录     | 邮件、审核意见、用户指南   |

| 质检        | 数据来源、引用、实验条件  | SOP、风险、语气、完整性  |

| 跟进        | 论文未读、实验未跑     | 人未回复、任务未完成     |

| 复盘        | 今日科研日志        | 工作日报/周报/项目复盘   |

| 记忆        | 研究方向、论文库      | 项目背景、人员、流程、模板  |



这张表其实就是 Talos 的产品边界。



---



# 8. Talos 的飞书集成设计



飞书在 Talos 里不只是聊天入口，而是状态容器。



我建议这样映射：



| 飞书模块        | Talos 用法                   |

| ----------- | -------------------------- |

| 飞书聊天        | Talos 主入口，DM 优先，群聊谨慎       |

| 飞书 Todo     | Open Loop 的外部任务落点          |

| 飞书日历        | 专注时间块、会议、提醒                |

| 飞书云文档       | 论文笔记、项目文档、会议纪要、草稿          |

| 飞书多维表格/Base | 论文库、项目库、Open Loop 数据库、专注统计 |

| 飞书云盘        | 存论文 PDF、资料、交付物             |

| 飞书消息        | 提醒、日报、复盘、草稿预览              |



关键原则：



> Talos 内部有自己的状态，但重要状态要同步到飞书，让用户能看见、能编辑、能信任。



不要让所有东西只藏在 agent memory 里，否则用户会没有掌控感。



---



# 9. 操作权限分级



因为 Talos 可以操作飞书，所以必须设计权限等级。



## Level 0：只读/总结，无需确认



例如：



```text

总结文档

读取 Todo

查看日历

生成草稿

分析论文

```



## Level 1：私人空间写入，可轻确认



例如：



```text

创建私人 Todo

记录专注时长

写入私人日志

创建私人草稿文档

```



## Level 2：影响协作者，需要明确确认



例如：



```text

修改共享文档

创建会议邀请

给别人分配 Todo

在项目文档里追加内容

```



## Level 3：外发/承诺/删除，必须二次确认



例如：



```text

发送飞书消息

发送邮件

代表用户承诺 deadline

删除文档

批量修改任务

向领导/用户发送正式结论

```



Talos 每次执行 Level 2/3 动作前，都应该输出：



```text

我准备执行以下操作：



1. 在 A 项目文档追加风险说明

2. 创建一个周三 18:00 截止的 Todo

3. 生成一段发到项目群的消息草稿



是否执行？

```



---



# 10. Talos 的每日工作流



Talos 最有生命力的地方，是每天固定出现。



## 早上：Morning Plan



触发：



```text

cron 09:00

"帮我规划今天"

```



流程：



```text

读取日历

读取 Todo

读取 Open Loops

读取论文队列

读取项目状态

根据 deadline 和优先级排序

生成今日计划

```



输出：



```text

今天建议这样安排：



一、必须完成

1. A 项目审核意见，18:00 前

2. 回复 B 用户反馈



二、建议推进

1. 读论文 X，至少完成方法部分

2. 更新 C 文档 FAQ



三、专注建议

10:30-11:20 写审核意见

15:30-16:20 读论文 X



四、需要跟进

张三：接口字段确认

```



---



## 白天：Execution Buddy



触发：



```text

"陪我专注 50 分钟"

"记一下别让我忘了"

"帮我写一下"

"帮我审一下"

```



Talos 扮演执行搭子。



它不是一直打扰，而是在关键点出现：



```text

开始前：确认目标

过程中：减少干扰

结束后：记录产出

未完成：转成 Open Loop

```



---



## 晚上：Evening Review



触发：



```text

cron 21:30

"复盘下今天"

```



流程：



```text

读取今日 Todo 完成情况

读取专注记录

读取文档更新

读取论文阅读记录

读取未闭合 Loop

生成复盘

写入日志

生成明日建议

```



输出：



```text

今天完成：



1. A 项目审核意见已完成

2. 读完论文 X 的 Introduction 和 Method

3. 专注 2 次，共 95 分钟



未闭环：



1. B 用户反馈还没回复

2. 论文 X 的实验部分还没看

3. 张三接口字段未确认



建议明天优先处理：

先回复 B 用户，再读论文 X 的实验部分。

```



---



# 11. Talos 的内部状态设计



建议至少有这些表/集合。



```text

UserProfile

- name

- preferred_name

- work_style

- writing_style

- confirmation_policy

- active_hours



Project

- id

- name

- domain

- status

- goal

- related_docs

- related_people

- open_loops



OpenLoop

- id

- title

- domain

- project

- next_action

- due_at

- status

- priority

- source



FocusSession

- id

- start_time

- end_time

- target

- project

- output

- quality

- interruptions



Paper

- id

- title

- authors

- source

- status

- tags

- relevance_score

- pdf_path

- notes_doc



WorkArtifact

- id

- type

- project

- doc_url

- status

- last_modified

- review_status



InteractionLog

- timestamp

- user_message

- agent_action

- tools_called

- result

- memory_written

```



其中最关键的是：



```text

OpenLoop

Project

FocusSession

Paper

WorkArtifact

```



这五个能支撑大部分功能。



---



# 12. Talos 的命令设计



可以保留自然语言，但最好也有稳定命令。



## 通用命令



```text

/today

规划今天



/review-day

复盘今天



/open

查看当前悬着的事



/focus 50 写论文 related work

开始专注



/capture 记一下，别让我忘了明天问张三接口字段

捕获 open loop



/done

标记当前任务完成

```



## 科研命令



```text

/papers

查看今天论文日报



/read <paper>

一起读某篇论文



/extract <paper>

提取论文数据、指标、实验条件



/study

进入学习模式



/write-paper

辅助写论文段落



/research-log

查看科研日志

```



## 工作命令



```text

/inbox

整理待回复消息



/draft

生成邮件、回复、审核意见



/review-doc

审文档/审方案



/meeting

生成会议纪要或拆 Todo



/followup

查看需要跟进的人和事



/report

生成日报/周报

```



自然语言仍然支持，例如：



```text

“帮我规划今天”

“陪我专注 40 分钟看论文”

“记一下，别让我忘了催接口”

“帮我把这几个点写成审核意见”

“把这个会议纪要拆成 Todo”

```



命令只是给高频功能一个稳定入口。



---



# 13. Talos 的多 Agent 工作流示例



## 示例一：用户说“帮我规划今天”



流程：



```text

User

 -> Commander

 -> Memory Agent：读取用户偏好

 -> Calendar Agent：读取今天日历

 -> Todo Agent：读取飞书 Todo

 -> Open Loop Agent：读取悬着的事

 -> Research Lead：读取论文/科研任务

 -> Work Lead：读取工作项目

 -> Planner Agent：生成计划

 -> Critic Agent：检查是否过载

 -> Commander：输出最终计划

```



输出：



```text

我建议今天不要安排太满。上午优先处理 A 项目审核意见，下午安排一段论文阅读。B 用户反馈可以放在午饭后快速处理。

```



---



## 示例二：用户说“帮我审这个方案”



流程：



```text

User

 -> Commander

 -> Docs Agent：读取方案文档

 -> Memory Agent：读取项目背景和审核 SOP

 -> Review Agent：检查问题

 -> Work Draft Agent：生成审核意见

 -> Critic Agent：检查语气、完整性、风险

 -> Commander：给用户预览

```



输出：



```text

我按“问题-风险-建议-可发送意见”整理了一版。

需要我创建到飞书文档，还是直接发你草稿？

```



---



## 示例三：论文日报



流程：



```text

Scheduler 09:00

 -> Paper Scout：抓取候选论文

 -> Relevance Agent：按你的研究方向排序

 -> Paper Reader：快速摘要 Top N

 -> Research Lead：生成日报

 -> Docs Agent：写入论文日报文档

 -> Messenger：私聊推送摘要

```



你截图里 `arxiv-digest` 现在遇到限流，所以这里建议做成：



```text

异步队列

缓存

失败重试

指数退避

每日上限

已有论文去重

```



不要每次用户问就实时猛拉。



---



# 14. 第一阶段 MVP 建议



我建议 Talos 第一阶段不要贪多，先做一个能每天用起来的闭环。



## Phase 1：个人闭环



目标：让 Talos 每天真的陪你运转。



必须完成：



```text

focus-buddy

open-loop-tracker

morning-plan

evening-review

Feishu Todo 接入

Feishu Calendar 只读/创建时间块

```



这阶段的核心是：



> 让 Talos 记得住、提醒得准、规划得像个人。



---



## Phase 2：工作交付物



目标：让 Talos 能帮你把工作半成品变成正式输出。



加入：



```text

draft-reply

project-review

meeting-to-actions

follow-up-nudger

weekly-report

Feishu Docs 接入

```



这阶段的核心是：



> 工作里可以直接用，尤其是审核意见、会议纪要、Todo、周报。



---



## Phase 3：科研增强



目标：让 Talos 成为真正科研助手。



加入：



```text

paper-download

paper-reader

paper-data-extractor

research-note-builder

citation/evidence trace

paper database

```



这阶段的核心是：



> 论文不是只总结，而是能筛、读、提数、沉淀、回查来源。



---



## Phase 4：多 Agent 协作



目标：让 Talos 可以并行处理复杂任务。



例如：



```text

一个 Agent 找论文

一个 Agent 读论文

一个 Agent 提取实验数据

一个 Agent 写综述草稿

一个 Agent 检查来源和一致性

```



工作场景也是：



```text

一个 Agent 读会议纪要

一个 Agent 拆 Todo

一个 Agent 写群通知

一个 Agent 更新项目文档

一个 Agent 做安全检查

```



---



# 15. 我建议 Talos 的第一版技能表



可以这样排优先级：



| 优先级 | 技能                              | 价值         |

| --- | ------------------------------- | ---------- |

| P0  | `open-loop-tracker`             | 全系统核心      |

| P0  | `morning-plan`                  | 每天启动 Talos |

| P0  | `evening-review`                | 每天沉淀记忆     |

| P0  | `focus-buddy`                   | 科研/工作都高频   |

| P1  | `todo-sync`                     | 打通飞书状态     |

| P1  | `draft-reply`                   | 工作场景立刻有用   |

| P1  | `project-review`                | 审核意见刚需     |

| P1  | `arxiv-digest`                  | 科研信息雷达     |

| P2  | `meeting-to-actions`            | 工作助手核心     |

| P2  | `paper-reader`                  | 科研助手核心     |

| P2  | `follow-up-nudger`              | 推进项目       |

| P2  | `weekly-report`                 | 形成长期依赖     |

| P3  | `paper-data-extractor`          | 高价值但实现难    |

| P3  | `multi-agent-literature-review` | 真科研助手高级形态  |



---



# 16. Talos 最重要的产品原则



## 原则一：所有功能都要落到状态



不要只回答用户，要更新状态。



例如：



```text

“帮我读这篇论文”

```



不应该只输出总结，还应该更新：



```text

Paper.status = reading

OpenLoop = “看论文 X 的实验部分”

ResearchLog += 今日阅读记录

```



---



## 原则二：所有外部动作都要可预览



尤其是工作场景。



```text

发消息

改共享文档

创建会议

分配任务

承诺 deadline

```



都必须先预览。



---



## 原则三：所有科研结论都要可回查



科研助手不能只说“论文认为……”。



最好输出：



```text

结论

来源位置

置信度

是否需要人工确认

```



---



## 原则四：Talos 要主动，但不能烦



建议有三个主动程度：



```text

silent：只在用户叫它时工作

normal：早晚计划/复盘 + 重要提醒

strict：像监督搭子一样追问、催促、复盘

```



用户可以说：



```text

“这周对我严格一点”

“今天别主动提醒”

“论文写作这块盯紧我”

```



---



# 17. 最终形态



Talos 最终应该像这样：



```text

Talos

├── Commander Agent

├── Memory Agent

├── Planner Agent

├── Open Loop Agent

├── Research Lead

│   ├── Paper Scout

│   ├── Paper Reader

│   ├── Data Extractor

│   ├── Study Buddy

│   └── Research Writer

├── Work Lead

│   ├── Inbox Agent

│   ├── Draft Agent

│   ├── Meeting Agent

│   ├── Project Agent

│   ├── Review Agent

│   └── Follow-up Agent

├── Tool Executor

│   ├── Feishu Todo

│   ├── Feishu Calendar

│   ├── Feishu Docs

│   ├── Feishu Base/Sheets

│   └── Feishu Messenger

└── Safety / Critic Agent

```



一句话总结：



> **Talos 不应该只是 Hermes 接飞书，而应该是一个以 Open Loop 为中心的科研/工作多 Agent 系统。科研侧负责论文、学习、专注、知识沉淀；工作侧负责沟通、审核、会议、项目推进和交付物；底层统一由计划、记忆、飞书工具、权限确认和复盘系统支撑。**


