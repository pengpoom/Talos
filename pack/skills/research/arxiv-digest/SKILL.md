---
name: arxiv-digest
description: 每天从 arXiv 抓取用户方向的新论文，狠筛 3-5 篇并推送到飞书。由 cron 定时触发。
version: 1.0.0
platforms: [linux, macos]
metadata:
  hermes:
    tags: [research, arxiv, digest]
    category: research
---

## When to Use
- 由 cron 每天定时触发（默认 09:00）。
- 用户主动说"看看今天的论文 / 来份论文日报"。

## Procedure

1. **抓候选**：运行
   ```
   research-assistant fetch --prefs ~/.hermes/research/prefs.yaml
   ```
   - 退出码 0：stdout 是去重后的候选论文 JSON 数组（含 id/title/summary/authors/link/published）。
   - 退出码非 0：抓取失败。**不要**继续，直接执行下面的「失败处理」。

2. **狠筛 + 排序（判断活）**：读 `~/.hermes/research/prefs.yaml` 的 `arxiv.keywords` 与 `arxiv.max_per_day`。
   - 按"与用户方向的相关度"给候选打分排序。
   - 只保留前 `max_per_day` 篇（默认 5）。宁缺毋滥，弱相关的砍掉。

3. **写日报正文（markdown）**：每篇一块，包含：
   - 标题（加粗）+ arXiv 链接
   - 一句话"它讲了啥"
   - 一句话"**为什么和你相关**"
   - 建议动作：`精读` / `扫一眼` / `跳过`
   把正文存成临时文件，例如：
   ```
   /tmp/arxiv-digest.md
   ```

4. **归档 + 标记已读**：运行
   ```
   research-assistant commit --ids <逗号分隔的入选 id> --digest-file /tmp/arxiv-digest.md --date <YYYY-MM-DD> --timezone <prefs.timezone>
   ```
   - 这一步把入选论文写进 `seen.jsonl`（明天不再重复推）并归档日报。
   - **务必在确认要推送之后、作为最后一步**执行（失败就别推、也别 commit）。

5. **推送**：把第 3 步的日报正文作为本次回复的最终内容输出。cron 的 `deliver: feishu` 会把它发到 home chat。

## 失败处理（第 1 步非 0 时）
- 给用户发一句软提示，例如："今天 arXiv 没抓到（可能它在抽风）。回我『重试』我就再来一次。"
- 不要 commit、不要污染 seen.jsonl。
- 可选：用 cronjob 工具挂一个 1 小时后的一次性重试。

## Pitfalls
- 不要在抓取失败时还硬编一份"空日报"——会把 seen 弄脏。
- `commit` 的 `--ids` 必须是**入选**那几篇的 id，不是全部候选。
- max_per_day 是硬上限，别超。

## Verification
- 干跑：`research-assistant fetch` 能打印候选 JSON。
- 端到端：`hermes cron run <job_id>` 触发后，飞书 home chat 收到日报，且 `~/.hermes/research/state/papers/` 下出现当天 `digest-*.md`、`seen.jsonl` 增长。
