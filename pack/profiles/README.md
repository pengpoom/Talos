# pack/profiles —— Talos 多 bot（profile）模板

Talos 把「科研 / 工作 / 总管」做成各自独立的 **Hermes profile**（= 独立飞书 bot + 独立人格 + 独立技能），但**共用一个后台**（时间轴 / 开放循环 / 专注 / 项目）。各 bot 读自己的域、改动互相可见；只有总管单写飞书 Todo。

- **总管**（默认 profile `~/.hermes`）：跨域规划 / 复盘、单写飞书 Todo。由 `install.sh` 装。
- **专科 bot**（本目录的模板）：research / work（可扩展 personal），由 `setup-profile.sh` 装。

## 起一个专科 bot
```bash
./setup-profile.sh research 研究bot --bot-name 小研 --user-address 老板
./setup-profile.sh work     工作bot --bot-name 小作 --user-address 老板
```
脚本会：建 profile → 从你本地默认 profile 拷大脑（provider，不来自 repo）→ 钉 `RESEARCH_HOME`（共享后台）→ 按 `skills.txt` 部署技能 → 渲染人格（替换 `{{BOT_NAME}}`/`{{USER_ADDRESS}}`）→ 铺记忆脚手架。

之后**人工**：① 飞书开放平台新建一个 app；② 填 `APP_ID/SECRET` 进该 profile 的 `.env`；③ 开 scope（科研→base/docx，工作→im/contact）；④ `<name> gateway start`；⑤ 飞书 DM 它走配对。

## 每个 type 目录
- `SOUL.md` —— 人格模板（占位 `{{BOT_NAME}}` `{{USER_ADDRESS}}`）。
- `skills.txt` —— 技能清单（含 `/` 的从 `pack/skills/` 拷；`lark-*` 从默认 profile 拷）。
- `description.txt` —— `hermes profile describe` 用。
- `_shared/` —— 通用记忆模板 + env 模式。

## 个人数据
渲染后的 SOUL、填好的记忆、`.env`、`auth.json` 全在 `~/.hermes/profiles/<name>/`，**不在本 repo**，不会进 GitHub。

设计文档：`docs/superpowers/plans/2026-06-14-multi-profile-generalization.md`
