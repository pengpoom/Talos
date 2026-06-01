# Hermes 科研搭子

在 [Hermes Agent](https://github.com/NousResearch/hermes-agent) 之上的科研搭子：arXiv 论文日报 + 日循环（晨间规划 / 晚间复盘）+ 开放循环巡检 + 专注陪伴。

## 前置
- 已跑起来的 Hermes（飞书 gateway 能对话）。
- 已设好飞书 home chat：在飞书对 Hermes 发 `/set-home`。
- 已装 `feishucli`（后续功能用）。

## 安装
```
git clone https://github.com/pengpoom/Talos.git && cd Talos
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

## 换个领域用（不动代码）
抓别的方向的论文，只改 `~/.hermes/research/prefs.yaml` 的 `arxiv` 段，改完下次 `fetch` 自动生效（不用重启，也不用动技能 / cron）：
```yaml
arxiv:
  categories: [cs.RO, cs.LG]           # 换成目标领域的 arXiv 分类
  keywords: ["robotic manipulation"]   # 换成目标主题；留空 = 只按分类抓
  max_per_day: 5
```
查询逻辑是 `(分类 OR …) AND (关键词 OR …)`，两段都可只填一个：只填 `categories` 抓该领域全部新论文；只填 `keywords` 跨分类按词抓。

常见领域分类示例：神经科学 `q-bio.NC`；凝聚态/量子 `cond-mat.str-el, quant-ph`；优化/数学 `math.OC, math.AP`；统计 `stat.ML`；经济金融 `econ.EM, q-fin.TR`。完整代码见 <https://arxiv.org/category_taxonomy>。

> 领域**不在 arXiv 上**（如临床医学→PubMed、生物→bioRxiv）才需要加新数据源——代码已预留 `source` 口子，但尚未实现。
> 给**另一个人**整套用：他另备一份 `prefs.yaml`（`name` / `timezone` / `style`）+ 自己的飞书 bot 与 cron 投递目标。

## 日循环（Plan 2）
装好后，工作日自动（混合方案：Todo 落飞书、其余落 research-assistant）：
- **09:00 晨间规划** —— 浮出悬着的开放循环，帮你定 1-3 件、拆到下一步，确认后**写进飞书 Todo**（App 可见，不再写 today.json）
- **22:00 晚间复盘** —— 读飞书 Todo 看今天做了啥、记时间轴、把没做完的转入开放循环

手动触发体验：在飞书说"帮我规划下今天" / "复盘下今天"。
状态文件在 `~/.hermes/research/state/`：`open_loops.json`、`timeline/<date>.md`、`focus.json`、`focus_log.jsonl`。

## 巡检 + 专注（Plan 3）
- **17:30 开放循环巡检（每天）** —— 跑 `loops-due`，挑该跟进的开放循环提醒你；没有就不打扰，提醒过的当天不重复。
- **专注陪伴（按需）** —— 在飞书说"陪我专注 30 分钟写 intro"，开一次 body-doubling 会话，陪你开始、到点收尾（自动记进时间轴 + `focus_log.jsonl`）。

新增状态文件：`focus.json`（当前专注会话）、`focus_log.jsonl`（专注历史）。

## 目录
- `src/research_assistant/` — 机械活 Python 包（含单测）
- `pack/` — 可分发的包（SOUL 人设 / 技能 / 配置模板 / cron 模板）
- `install.sh` — 装进 `~/.hermes/`
- `docs/superpowers/` — 设计 spec 与实施计划
