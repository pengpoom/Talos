# Hermes 科研搭子

在 [Hermes Agent](https://github.com/NousResearch/hermes-agent) 之上的科研助手。Plan 1：基础设施 + arXiv 论文日报。

## 前置
- 已跑起来的 Hermes（飞书 gateway 能对话）。
- 已设好飞书 home chat：在飞书对 Hermes 发 `/set-home`。
- 已装 `feishucli`（后续功能用）。

## 安装
```
git clone <this-repo> && cd hermes-poss
bash install.sh
```
然后编辑 `~/.hermes/research/prefs.yaml`，填上你真实的 `arxiv.categories` 与 `keywords`。

## 自测
```
# 1) 机械活：能抓到候选
research-assistant fetch --prefs ~/.hermes/research/prefs.yaml | head

# 2) 全量单测
pip install -e ".[dev]" && pytest -q
```

## 端到端（论文日报）
1. 按 install.sh 末尾提示注册 cron（自然语言最省事）。
2. 立刻触发一次：`hermes cron run <job_id>`（或在飞书说"来份论文日报"）。
3. 预期：飞书 home chat 收到 3–5 篇精选日报；`~/.hermes/research/state/papers/` 出现当天 `digest-*.md`，`seen.jsonl` 增长。
4. 再触发一次：之前推过的不再出现（去重生效）。

## 日循环（Plan 2）
装好后，每天会自动：
- **08:30 晨间规划** —— 帮你定 1-3 件、拆到下一步，写进 today.json
- **22:00 晚间复盘** —— 复盘今天、记时间轴、把没做完的转入开放循环

手动触发体验：在飞书说"帮我规划下今天" / "复盘下今天"。
状态文件在 `~/.hermes/research/state/`：`today.json`、`open_loops.json`、`timeline/<date>.md`。

## 目录
- `src/research_assistant/` — 机械活 Python 包（含单测）
- `pack/` — 可分发的包（SOUL 人设 / 技能 / 配置模板 / cron 模板）
- `install.sh` — 装进 `~/.hermes/`
- `docs/superpowers/` — 设计 spec 与实施计划
