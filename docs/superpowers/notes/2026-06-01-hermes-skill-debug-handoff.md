# 交接 note：Hermes 技能不执行 的调试现状

> 给在 Mac mini 上接手的 Claude。先读 `docs/superpowers/specs/` 和 `docs/superpowers/plans/` 了解全貌，本文件是当前卡点。

## 项目状态
- Plan 1/2/3/3.1 全部完成，`PYTHONPATH=src python -m pytest -q` → **67 passed**。
- 仓库本地名 **Talos**（曾叫 hermes-poss）。5 个技能在 `pack/skills/research/`：arxiv-digest、morning-plan、evening-review、open-loop-tracker、focus-buddy。
- 部署：`bash install.sh`（`cp -r pack/skills/research/.` 到 `~/.hermes/skills/research/`）。**改技能/SOUL 后必须 `hermes gateway restart`**（技能在 gateway 启动时载入）。

## 卡点：Hermes agent 不执行我们技能里的 CLI 步骤
现象：飞书说"陪我专注"/"帮我规划今天" → agent 只用 SOUL 人设 + Hermes 原生提醒应付，**不跑** `research-assistant focus-start`/`today-set-plan`，状态文件不更新。

已排除的（都验过了）：
- ✅ terminal 工具是通的：让 agent「在终端运行 `research-assistant focus-status`」，它真跑了、回 `{"active": false}`。
- ✅ `research-assistant` 在 Hermes 环境里够得着（无 PATH 问题）。
- ✅ CLI 本身正常（手动跑都对，67 测绿）。

→ 所以病根是：**技能没被 Hermes 加载/触发执行**（agent 没把 SKILL.md 的命令步骤当成要执行的动作）。

## 怀疑方向（在 Mac mini 直接查）
1. **`~/.hermes/skills/research/DESCRIPTION.md`**：很可能是技能索引（"有哪些技能/何时用"）。我们的 5 个技能可能**没登记进去**——install.sh 从没动过它。先 `cat` 它。
2. **对比预装示例技能的格式**：`~/.hermes/skills/research/{blogwatcher,polymarket,research-paper-writing}/` 是 Hermes 自带的"正确格式"参照。对比它们的 SKILL.md（frontmatter 字段、命令声明方式）vs 我们的。
3. **Hermes 如何决定调用技能 + 执行命令**：翻 Hermes 文档/源码/运行日志，看技能触发与命令执行机制。
4. 另一个旁证：曾有**一次** `focus-start` 真的执行了（写出过 focus.json），但之后多次没有 → 像是偶发，更像"技能没被稳定触发"。

## 修复后怎么验
- 改完 5 个技能（格式或登记）→ `hermes gateway restart` → 飞书"帮我规划今天，记一件事：写测试" → `cat ~/.hermes/research/state/today.json` 应有内容。
- 状态文件位置：`~/.hermes/research/state/`：`today.json`、`open_loops.json`、`focus.json`、`focus_log.jsonl`、`timeline/<date>.md`。

## 约束（沿用）
- 中文回复；不加多余注释；不改已有函数签名；边写边跑 pytest。
- **git 操作只给命令、不替用户执行。**
