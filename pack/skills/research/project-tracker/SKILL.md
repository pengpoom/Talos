---
name: project-tracker
description: 管理"项目"这个对象（科研/工作/个人的长期事项容器），并回答"X 项目现在卡在哪"。建/改项目、把开放循环和专注挂到项目下、聚合出某项目的开放事项+逾期+专注时长。用户说"X 项目什么状态/卡在哪 / 新建个项目 / 这事归到 X 项目 / 我手头有哪些项目"时用。
version: 1.0.0
platforms: [linux, macos]
metadata:
  hermes:
    tags: [research, work, project, open-loop]
    category: research
---

## When to Use
- **建项目**："新开个项目 X / 把 X 立成一个项目"。
- **查状态**："X 项目现在啥状态 / 卡在哪 / 推进到哪了"、"我手头有哪些项目"。
- **改项目**："X 项目改投 ICLR 了 / 暂停 / 完成了 / 把这文档挂到 X 项目下"。
- **归属**：用户把某件事/某次专注归到某项目时（落库带 `--project`）。

## 核心心智
**项目 = 一堆 open loop + 专注 + 论文 + 文档的容器。** 项目本身不存"待办清单"，它聚合的是已经分散落在各处、`--project` 标了它名字的东西。所以"卡在哪"= 把挂在它名下的开放循环 + 专注时长拢一起看。

## A. 建项目
```
research-assistant project-add --tz <tz> --name "<项目名>" \
  --domain <research|work|personal> --goal "<目标>" [--next-milestone "<下一个里程碑>"]
```
回执项目 id 和名字。**项目名要简短稳定**（后面 loop/focus 靠它来挂，如 `lunwen2`）。

## B. 把事/专注挂到项目（关键——不挂就聚合不出来）
- **开放循环**：捕获时带 `--project "<项目名>"`（见 `open-loop-tracker`）：
  ```
  research-assistant loops-add ... --project "lunwen2"
  ```
  已存在的 loop 补挂：`research-assistant loops-update --id <id> --project "lunwen2"`。
- **专注**：开专注时带 `--project`：
  ```
  research-assistant focus-start --tz <tz> --task "<事>" --minutes <N> --project "lunwen2"
  ```
- **论文**：在 `paper-library` 入库时把"方向/标签"写成项目名，或单独留一列，查库时按项目筛（论文存飞书 Base，不在本地 state，所以不进下面的聚合）。
- 名或 id 都能匹配，大小写不敏感。

## C. 查"卡在哪"（核心视图）
```
research-assistant project-status --tz <tz> --name "<项目名或 id>"
```
返回：`project`（项目本身）、`open_count`/`overdue_count`/`done_count`、`focus`(次数+累计分钟)、`next_actions`（开放循环的下一步，逾期的排前面）、`open_loops`、`done_loops`。

**组织成人话回**（别贴 JSON）：
- 一句状态：「**lunwen2**（目标：投 NeurIPS）：开着 3 件、其中 1 件逾期，已专注 95min。」
- 逐条开放事项**带 next_action + owner**，逾期的标出来：「⚠️ 回审稿意见（逾期）→ 下一步：…」。
- 给下一步建议：要不要现在推最要紧那条 / 排个专注。
- 没有项目记录但有挂了这个名字的事 → 照样聚合，并提一句"要不要把它立成正式项目"。

## D. 列 / 改项目
- 列：`research-assistant project-list [--domain work] [--status active]`。
- 改：`research-assistant project-update --tz <tz> --id "<名或id>" [--status active|paused|done] [--goal ...] [--next-milestone ...] [--add-doc <url>] [--add-person <名>]`。

## Pitfalls
- **挂了才聚合**：loop/focus 不带 `--project` 就不会进某项目的"卡在哪"。捕获/开专注时顺手挂。
- **项目名稳定**：改名会让旧的 `--project` 标记对不上（必要时用 `project-update --name` 改，并提醒用户旧挂法）。
- **论文不进本地聚合**：论文在飞书 Base，按项目看论文走 `paper-library` 的筛，不在 `project-status` 里。
- 拿不准 domain / 是否该立项 就问一句，别乱建。

## Verification
- 建项目 → `project-list` 能看到。
- loops-add/focus-start 带 `--project` → `project-status --name <项目>` 的 open_count / focus 分钟数随之变。
- 逾期的开放循环在 `next_actions` 里 `overdue=true` 且排在最前。
