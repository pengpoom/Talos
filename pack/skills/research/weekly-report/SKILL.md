---
name: weekly-report
description: 读已有状态（专注记录/时间轴/飞书 Todo/开放循环）生成本周进展周报。用户说"帮我写周报 / 这周做了啥 / 生成进展汇报 / 总结下这周"时用。全基于真实记录，默认只出草稿不自动发。
version: 1.0.0
platforms: [linux, macos]
metadata:
  hermes:
    tags: [research, review, report]
    category: research
---

## When to Use
- 用户说"帮我写周报 / 这周做了啥 / 生成进展汇报 / 总结下这周"。
- 跨周汇总；`evening-review` 是单天复盘，这里是一周维度。

## Procedure

1. **定时间范围**：默认本周一 → 今天（用户给了范围就用）。

2. **读真实状态（别编）**：
   - 专注：`research-assistant focus-stats --since <周一日期>` + `research-assistant focus-log --limit 30`（次数 + 时长）。
   - 时间轴：读 `~/.hermes/research/state/timeline/<本周各天>.md`。
   - 飞书 Todo：用 `lark-task` 看本周完成 / 未完成。
   - 开放循环：`research-assistant loops-list`（还悬着的；可 `--domain work`/`research` 分组列）。

3. **汇总成周报**：
   ```
   本周完成：…（飞书 Todo 勾掉的 + 时间轴里的产出）
   专注投入：N 次、共 M 分钟
   进行中 / 没做完：…
   还悬着的（开放循环）：…
   下周重点 / 建议：…
   ```

4. **默认只出草稿**：要发给导师 / 存进文档，走 `draft-reply`（预览确认）或 `lark-doc`，**不自动发**。

## Pitfalls
- 全部基于真实状态文件 + 飞书 Todo，**别编没发生的**。
- 外发 / 存共享文档先预览确认。
- 读不到某项（如本周没专注记录）就如实说"无"，别凑数。

## Verification
- "帮我写周报" → 读 focus-stats / timeline / Todo / loops、按 5 段汇总、是草稿不自动发。
