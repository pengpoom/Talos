---
name: meeting-to-actions
description: 把会议纪要拆成可执行待办（事/负责人/截止），确认后写进飞书 Todo。用户说"把这段会议纪要拆成 Todo / 总结这个会议 / 帮我拆会议待办 / 这个会的待办整理下"时用。只把"我的"待办写进飞书，别人的标出不替建；外发先预览。
version: 1.0.0
platforms: [linux, macos]
metadata:
  hermes:
    tags: [work, meeting, todo]
    category: work
---

## When to Use
- 用户说"把这段会议纪要拆成 Todo / 帮我拆会议待办 / 这个会整理下待办 / 总结这个会议"。
- 把会议内容变成可执行任务；纯总结会议走 `lark-minutes`/`lark-doc`，这里是"拆成 Todo"。

## Procedure

1. **拿到纪要**：
   - 用户贴的文本 → 直接用。
   - 飞书妙记 → `lark-minutes` 读纪要 / AI 产物；会议 → `lark-vc` 取纪要；飞书文档 → `lark-doc`。

2. **提取**：
   - **决定 / 结论**（会上拍板的）。
   - **待办**：每条标 事 + 负责人 + 截止（能推就推，推不出标"待定"）。
   - **风险 / 待跟进**。

3. **给确认清单**：把待办列给用户过目，问"这些写进飞书 Todo 吗？"

4. **确认后写飞书 Todo**：
   - 用 `lark-task` 把**用户自己的**待办建进飞书 Todo（按 `feishu-personal-productivity-workflows` 约定：当天分区、截止按会上定的）。
   - **别人的待办**不替别人建 Todo，但可建成**你自己的开放循环**（"我要跟进谁"）：`research-assistant loops-add --domain work --owner <那人> --next-action "催<那人><做啥>" --priority <high|medium>`，这样巡检会提醒你去跟进。要立刻催走 `draft-reply`。
   - 涉及"代用户承诺截止"的，标出来让用户确认。

5. **可选**：会议结论存飞书文档 / 出个群通知草稿（`draft-reply`，预览后发）。

## Pitfalls
- 只把**用户自己的**待办写进飞书 Todo；别人的标出不替建。
- 承诺截止 / 代别人表态先确认，别自作主张。
- 外发（群通知 / 纪要）先预览，不自动发。

## Verification
- 贴一段纪要说"拆成 Todo" → 列出 决定 / 待办(事+人+截止) / 风险，确认后才写飞书 Todo，别人的不替建。
