# 多 Profile 泛用化方案（开源可复现的多 bot 架构）

## Context（为什么）

目前的三 bot 架构（总管 / 小研 / 小作）是**手工直接在 `~/.hermes` 搭出来的**——repo 里一点没捕获。后果：

- 别人 clone Talos、跑 `install.sh`，只会装**单个默认 bot**，起不了多 bot；
- 换台机器也得手工重来；
- 而个人数据（记忆事实、Feishu creds、bot 名字）和**通用骨架**（人格类型、技能集、共享后台模式）现在是混在一起的。

目标：把多 bot 架构**提炼成 repo 里的通用模板 + 一键安装脚本**，让 Talos 成为「别人能复现的系统」，个人数据全程留本地、永不进 GitHub。

## 两层分离（核心原则）

| 层 | 位置 | 内容 | 进 GitHub？ |
|---|---|---|---|
| **通用骨架** | repo `~/Project/Talos` | 人格模板、技能清单、记忆模板（占位）、安装脚本 | ✅ |
| **个人实例** | 运行时 `~/.hermes` | 填好的 SOUL（带名字）、记忆事实、`.env`(creds)、`auth.json`、共享后台数据 | ❌ 永不 |

人格本身（科研专科 / 工作专科 / 总管）**是通用的**；只有 **bot 名字（小研/小作）+ 用户事实 + creds** 是个人的。模板用占位符，安装时注入。

## repo 结构（新增）

```
pack/profiles/
  _shared/
    env.snippet            # RESEARCH_HOME 钉共享后台 + Feishu creds 占位
    USER.template.md       # 用户画像脚手架（占位 + 填写指引）
    MEMORY.template.md     # 记忆脚手架（占位）
  research/
    SOUL.md                # 科研专科人格，参数化 {{BOT_NAME}} {{USER_ADDRESS}}
    skills.txt             # 技能清单：paper-reader/paper-library/arxiv-digest/
                           #   focus-buddy/open-loop-tracker/project-tracker +
                           #   lark-{shared,base,doc,task,calendar,im,contact,drive,wiki,markdown}
    description.txt        # hermes profile describe 用
  work/
    SOUL.md                # 工作专科人格
    skills.txt             # draft-reply/project-review/meeting-to-actions +
                           #   open-loop-tracker/project-tracker/focus-buddy + lark 子集
    description.txt
  README.md                # 多 bot 架构说明（总管+专科、共享后台、谁写Todo、domain 路由）
setup-profile.sh           # 一键起一个专科 bot
```

> 总管 = 默认 profile（`~/.hermes`），已由现有 `install.sh` + `SOUL.snippet.md` 处理，不动。本方案只加**专科 bot**（research/work，可扩展 personal）的复现能力。

## `setup-profile.sh <type> <name> [--bot-name 小研] [--user-address 老板]`

按顺序自动做（把今天手工踩的坑全固化进去）：

1. `hermes profile create <name>` —— 新 profile。
2. **装大脑**：从**用户自己的默认 profile** 拷 provider 配置（`config.yaml` 的 `custom_providers` + `model` 块 + `auth.json` 的 `credential_pool`）。所有 bot 共用同一 LLM，凭证来自用户本地、**不来自 repo**。
3. **钉共享后台**：往新 profile 的 `.env` 追加 `RESEARCH_HOME=$HOME/.hermes/research`。**这步是必须的**——不钉的话 `research_home()` 会落到 profile 自己的 HOME，看不到共享后台（今天真踩过这个 bug）。
4. **部署技能**：按 `pack/profiles/<type>/skills.txt`，从 `pack/skills/` 拷自定义技能、从默认 profile 拷需要的 `lark-*`。
5. **渲染人格**：`SOUL.md` 模板替换 `{{BOT_NAME}}`/`{{USER_ADDRESS}}` → 写进 profile 的 `SOUL.md`。
6. **铺记忆脚手架**：`USER.template.md`/`MEMORY.template.md` → profile 的 `memories/`（用户自己填事实，repo 里只有占位）。
7. **打印 next steps**（必须人工做的）：① 飞书开放平台**新建一个 app**（token 锁不让多 bot 共用一个 app）；② 填 `APP_ID/SECRET` 进 `.env`；③ 开该 bot 需要的 scope（科研→base/docx，工作→im/contact）；④ `<name> gateway start`；⑤ 飞书里 DM 它走配对。

## 参数化（去个人化）

- `{{BOT_NAME}}`：小研/小作/…（人格自称）。
- `{{USER_ADDRESS}}`：老板/…（bot 怎么称呼用户）。
- 二者从命令行传或留通用默认（如 `{{BOT_NAME}}`→"研究助手"）。**模板里只有 `{{占位符}}`，安装时才注入；repo 不含任何真实人名/称呼。**

## 个人数据隔离

- 渲染后的 SOUL（带名字）、填好的 USER.md/MEMORY.md、`.env`、`auth.json` —— 全在 `~/.hermes/profiles/<name>/`，**不在 repo 树内**。
- `.gitignore` 兜底：确保任何 `*.env`、`auth.json`、profile 实例都不会被误加。
- 开源前一次性历史清理（squash 干净初始 commit），去掉早期提交里的域名/私密 message。

## 已知坑（固化进脚本/文档，别让别人再踩）

- **RESEARCH_HOME 必钉**（否则不共享后台）。
- **一 bot 一飞书 app**（token 锁）。
- **每个新 bot 要配对**（DM → `hermes -p <name> pairing approve`）。
- **scope 按 bot 分**（科研 base/docx，工作 im/contact），面更窄更安全。
- **bundled-sync**：`.no-bundled-skills` 标记挡不住 gateway 重启时的 re-seed，杂技能会回来——**无害**（on-demand 不误触发），文档里说明、不强求清。
- **provider fallback**：多 bot 一起轰一个 provider，503 概率放大，建议 `hermes fallback add`。

## Verification（怎么验方案成立）

- 在一台**干净机器/新 HOME** 上：`clone → install.sh → setup-profile.sh research 研究bot → setup-profile.sh work 工作bot`，填 creds 后三 bot 都能起、且共享后台（一个 bot 写时间轴，另一个读得到）。
- `git grep` 跟踪文件零个人标识；`setup` 产物全部落在 `~/.hermes`、`git status` 干净。
- 改 bot 名字/用户称呼只需传参，不动 repo。
```
