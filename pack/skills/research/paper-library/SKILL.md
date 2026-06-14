---
name: paper-library
description: 维护一个飞书 Base 论文库（索引）：读过的论文存一行（元数据 + 笔记链接 + Zotero 链接），能按方向/状态/标签查。全文留 Zotero、笔记在飞书文档，库只存索引不存 PDF。用户说"存进论文库 / 加进库 / 我读过哪些 X / 查论文库"时用。
version: 1.2.0
platforms: [linux, macos]
metadata:
  hermes:
    tags: [research, paper, library, knowledge]
    category: research
---

## When to Use
- **入库**："把这篇存进论文库 / 加进库 / 记到库里"（通常接在 `paper-reader` 读完之后）。
- **查库**："我读过哪些 <方向> 的 / 论文库里有啥 / 我之前读过 <主题> 吗 / 查一下论文库"。

## 三层定位（别搞混）
- **全文 PDF** → 本地 **Zotero**（本库**不存 PDF**，只存指向它的链接）。
- **深读笔记** → **飞书云文档**（`paper-reader` 写的，本库存它的链接）。
- **索引 / 库本身** → **飞书 Base**（本库 = 这张表，只存元数据 + 链接）。

## A. 找 / 建论文库 Base（一次性）
**先读本地缓存**：`cat ~/.hermes/research/state/paper_library.json`。
- 有 `base_token` → **直接用它**，跳过下面的搜索（省掉 `search:docs:read`，不再要授权）。
- 没有（文件不存在/为空）→ 才用 `lark-base` 找名为 **「论文库」** 的 Base；还没有就**创建一次**，建一张表，字段：
```
标题(文本) / 作者(文本) / arXiv ID(文本) / 方向(文本) / 相关度(单选:高/中/低)
/ 状态(单选:待读/在读/读完) / 标签(文本) / 笔记链接(URL) / Zotero链接(URL) / 添加日期(日期)
```
（具体建表 / 字段命令载入 `lark-base`。）

**拿到 / 建好后立刻缓存**，写本地 state（之后免搜）：
```
~/.hermes/research/state/paper_library.json
{"base_token":"<token>","table_id":"<tbl...>","name":"论文库"}
```
> ⚠️ **token 只进本地 state，绝不写进本 SKILL 源码**。Base token 是「某个用户自己飞书里那张表」的地址，按人不同、别人无权访问；写死在技能里对别人无效，还会把私人库地址泄进公开仓库。每个用户首次自建自存，各用各的。

**硬规则：库必须是飞书 Base（多维表格），不能用 Docx 里的表格代替**（Docx 表静态、不能筛/查/排序，不是索引）。如果建 Base 失败（常见：缺 `base:app:create` 权限 → `missing_scope`）→ **明确告诉用户"建论文库需要开通飞书多维表格权限（`base:app:create`），去 [权限管理] 开通后重新授权"、给授权链接、停在这里**，**绝不退而求其次建成 Docx 糊弄**。

## B. 入库（加一行）
1. **先去重**：用 `lark-base` 按 标题 / arXiv ID 查这篇是否已在库；在了就**更新那行**（别建重复）。
2. **填一行**：从 `paper-reader` 的精读结果 / 用户给的信息填：标题、作者、arXiv ID、方向（按 prefs.keywords）、相关度、标签、状态（默认"读完"）、添加日期。
3. **链接**：
   - **笔记链接** = 飞书文档笔记的 URL（`paper-reader` 存的，有就链）。
   - **Zotero 链接** = 用户提供的 `zotero://select/...` 或 item key（**没有就留空，别瞎编**）。
4. 回执"已入库：<标题>，方向 X、相关度 Y"。

## C. 查库（搜 / 筛）
用 `lark-base` 按 方向 / 标签 / 状态 / 相关度 筛，或关键词搜标题：
- "我读过哪些 agent memory 的" → 按 方向 / 标签 / 标题含关键词 筛 → 列出 **标题 + 笔记链接**。
- 列出时给 标题 + 方向 + 笔记链接，让用户点开看笔记 / Zotero。

## Pitfalls
- **库必须是 Base（多维表格），不是 Docx 表**；建不了就让用户开 `base:app:create` 权限，**别用 Docx 顶替**。
- **先读 `~/.hermes/research/state/paper_library.json` 拿 token**，别每次都搜库（搜要 `search:docs:read`）；建/找到后写回缓存。**token 不进技能源码**（按人不同、私人数据）。
- **scope 授权是按人一次性的，token 缓存救不了它**：每个用户首次建库要自己授 base 域那组 scope（`base:app:create`/`table:read`/`field:read·create·update`/`record:create·read`），飞书要求逐个授（一次性要全 base 域会报 `malformed scope`）。授完进 token，后续不再要。
- **不存 PDF 进飞书**——全文留 Zotero，库只存链接。
- **入库先去重**（标题 / arXiv ID），别建重复行。
- Zotero 链接没有就留空，别编。
- 相关度 / 方向拿不准就问用户一句，别乱填。

## Verification
- 入库：读完一篇 → "存进论文库" → Base 多一行（元数据 + 笔记链接），去重生效。
- 查库："我读过哪些 X 方向的" → 列出库里匹配的 标题 + 链接。
