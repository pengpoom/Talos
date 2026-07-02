---
name: memory-recall
description: 从 Talos 本地共享后台检索历史上下文。用户问"之前/上次/我记得/查一下历史/这个项目背景/我们当时为什么这么定"时用。只读本地 state，不写入、不外发。
version: 1.0.0
platforms: [linux, macos]
metadata:
  hermes:
    tags: [memory, recall, rag, research, work]
    category: research
---

## When to Use
- 用户问过去发生过的事："之前说过什么 / 上次做到哪 / 我当时为什么这么定 / 查一下历史"。
- 用户问项目、开放循环、专注、论文日报、科研日志的背景。
- 回答前需要用真实记录校准，而不是靠当前会话记忆猜。

## Core Rule
先跑本地检索，再总结成人话：
```
research-assistant recall --query "<用户原话或关键词>" --limit 8
```

`recall` 会只读共享后台里的本地状态：时间轴、开放循环、项目、专注记录、论文日报存档。它不会访问网络、不会写文件、不会改状态。

## Procedure
1. **整理查询词**：优先用用户原话；太长时提取项目名、人名、论文名、关键词。
2. **跑 recall**：
   ```
   research-assistant recall --query "<关键词>" --limit 8
   ```
3. **读返回 JSON**：每条有 `kind/source/date/title/text/score`。
4. **总结成人话**：
   - 先给结论："我查到的历史里，主要是..."
   - 按时间或主题列 2-5 条证据。
   - 说明来源类型：时间轴 / open loop / 项目 / 专注 / 论文日报。
5. **读不到就诚实说**：没有命中时说"本地记录里没查到"，然后问用户是否要帮他现在补记成 open loop / 项目 / 时间轴。

## Pitfalls
- recall 是事实检索，不是写入工具；别用它代替 `loops-add` / `timeline-append`。
- 不要把 JSON 原样甩给用户；要组织成人话。
- 命中结果只是本地记录，不等于完整真相；重要结论要说"本地记录显示"。
- 如果用户明确问论文库 Base 里的论文，优先走 `paper-library`；recall 只查本地日报/日志，不查飞书 Base。

## Verification
- "我们之前 Talos RAG 怎么定的？" → 跑 recall → 从时间轴 / 项目 / open loop 里拢出历史。
- 空状态下查询 → 返回无命中，并明确说没查到，不编。
