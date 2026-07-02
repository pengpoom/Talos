---
name: lit-review
description: 综述模式——并行精读多篇论文再汇成对比综述。用 delegate_task 一篇派一个子 agent 同时读，各回精读要点，父 agent 汇成"方法/数据/结论/分歧 + 每篇与你方向的关系"。用户说"并行读这几篇 / 把这几篇 X 方向的汇成综述 / 帮我对比这几篇"时用。
version: 1.0.0
platforms: [linux, macos]
metadata:
  hermes:
    tags: [research, paper, review, multi-agent]
    category: research
---

## When to Use
- "并行读这 5 篇 / 同时读这几篇"。
- "把这几篇 <方向> 的汇成综述 / 对比一下这几篇"。
- 手上有一批（3+ 篇）同方向论文，想要**横向对比**而不是一篇篇串读。

## 机制：delegate_task 并行 + 父 agent 汇总
`delegate_task` 是 Hermes 内置工具，能在本对话里 spawn 隔离的子 agent 并行干活，只回摘要。综述就用它：**一篇一个子 agent 同时精读 → 收回各自要点 → 你（父 agent）汇总**。

## Procedure

1. **列清单**：拿到要读的论文（用户给的链接 / arXiv id / 标题）。读 `prefs.yaml` 的 `keywords` 知道用户方向。

2. **并行派精读**（一篇一个子 agent）：用 `delegate_task` 批量派，每篇一个任务：
   ```
   delegate_task(tasks=[
     {goal: "精读论文 <链接/arXiv id>：返回 ① 一句话贡献 ② 方法 ③ 数据集/指标/关键结果(带数值) ④ 结论 ⑤ 与「<用户方向>」的关系。结论带出处，读不到的不脑补。",
      toolsets: ["web_search","web_extract"], role: "leaf"},
     ... 每篇一条 ...
   ])
   ```
   - 子 agent **只读不写**（隔离、不碰库/记忆），各自返回结构化要点。
   - **并发上限约 3**：超过 3 篇会排队、自动跑完，没关系；只是别一次塞太多（>8 篇分两批）。

3. **父 agent 汇成对比综述**（收齐子 agent 的返回后）：
   ```
   一、各篇一句话贡献
   二、横向对比：方法 / 数据集 / 主指标·结果 / baseline（能比就列成表）
   三、共识与分歧：大家都同意啥、在哪分歧
   四、每篇与你方向（<keywords>）的关系、值不值得深读
   五、建议：先精读哪 1-2 篇 / 哪些只需扫
   ```
   **结论带出处**（哪篇、哪节）；子 agent 没给实数的地方别补。

4. **可选落库**：综述出来后问"要不要把这几篇入论文库 + 提实验数据" → 走 `paper-library`（入库去重）+ `paper-data-extractor`（补字段，便于以后比对）。并顺手 `research-log` 记一条 `[研究·读]`。

## Pitfalls
- **子 agent 只读不汇总**：综述由父 agent 收齐后写，别让子 agent 互相看（它们隔离）。
- **读不到就如实说**（某篇打不开/无全文），别让子 agent 编。
- **并发约 3**：N 大就排队/分批，别期望 20 篇瞬间出。
- **落库是父 agent 的活**（子 agent 不写库/记忆）。
- 综述结论**带出处**，数值不脑补。

## Verification
- "并行读这 3 篇 X 的" → 看到 spawn 了多个子 agent 并行精读 → 最后一份带对比表 + 与用户方向关系的综述。
- 综述后可一键入库 + 提数据 + 记研究日志。
