---
name: paper-reader
description: 深读一篇论文，输出结构化精读笔记（贡献/方法/实验/与你方向的关系/存疑）。用户说"帮我读这篇论文 [链接/arxiv id] / 精读一下 XXX / 这篇讲了啥 / [arxiv 链接] 帮我看看"时用。结论标出处可回查，不脑补。
version: 1.0.0
platforms: [linux, macos]
metadata:
  hermes:
    tags: [research, paper, reading]
    category: research
---

## When to Use
- 用户给一篇论文（arXiv 链接/ID、PDF、或飞书文档）说"帮我读 / 精读 / 这篇讲了啥 / 帮我看看"。
- 把**一篇**论文读透；`arxiv-digest` 是"找+筛多篇"，这里是"深读单篇"。

## Procedure

1. **拿到并读全**：
   - arXiv 链接/ID → `web_extract` 读 abstract（`arxiv.org/abs/<id>`）或全文 PDF（`arxiv.org/pdf/<id>`）。
   - 用户贴的 PDF/文本 → 直接用；飞书文档 → `lark-doc` 读。
   - 读不到全文就说明，只基于 abstract 读，别脑补全文细节。

2. **结构化精读，输出**：
   ```
   一句话贡献：…
   解决什么问题 / 动机：…
   方法核心：…（关键 idea，别堆术语）
   实验 & 结论：…（数据集 / 指标 / 主要结果）
   跟你方向的关系：…（读 ~/.hermes/research/prefs.yaml 的 keywords，说"为什么和你相关"）
   存疑 / 可借鉴：…（局限、能挪用到你工作的点）
   ```

3. **结论可回查**：关键结论标出处（第几节 / 图表 / 原文），别给无来源的断言。

4. **可选收尾**：
   - 问要不要把笔记**存成飞书文档**（`lark-doc`）；存了就**接着问要不要进论文库**（`paper-library` 入库，带上笔记链接 + 你的 Zotero 链接）。
   - 若刚推进了某个开放循环（如"读 X 的实验部分"），问要不要 `research-assistant loops-resolve`。

## Pitfalls
- 结论**带出处**，读不到的别编（科研结论要可回查）。
- 别只复述 abstract 当精读；够得着全文就读方法 / 实验。
- "跟你方向的关系"要具体，别套话。

## Verification
- 给个 arXiv 链接说"精读" → 输出上面 6 段、关键结论带出处、有"为什么和你相关"。
