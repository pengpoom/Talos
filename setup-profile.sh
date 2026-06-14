#!/usr/bin/env bash
# setup-profile.sh —— 一键起一个 Talos 专科 bot（Hermes profile），共用总管的后台。
#
# 用法:
#   ./setup-profile.sh <type> <profile-name> [--bot-name 名字] [--user-address 称呼]
# 例:
#   ./setup-profile.sh research 研究bot --bot-name 小研 --user-address 老板
#   ./setup-profile.sh work     工作bot --bot-name 小作 --user-address 老板
#
# 个人数据（creds / 记忆事实 / 渲染后的人格）全部落在 ~/.hermes，不进本 repo。
set -euo pipefail

REPO="$(cd "$(dirname "$0")" && pwd)"
HERMES="${HERMES_HOME:-$HOME/.hermes}"

TYPE="${1:-}"; NAME="${2:-}"
if [ -z "$TYPE" ] || [ -z "$NAME" ]; then
  echo "用法: ./setup-profile.sh <research|work> <profile-name> [--bot-name X] [--user-address Y]"; exit 1
fi
shift 2
BOT_NAME="${TYPE}-bot"; USER_ADDRESS="你"
while [ $# -gt 0 ]; do
  case "$1" in
    --bot-name) BOT_NAME="$2"; shift 2;;
    --user-address) USER_ADDRESS="$2"; shift 2;;
    *) echo "未知参数: $1"; exit 1;;
  esac
done

TPL="$REPO/pack/profiles/$TYPE"
[ -d "$TPL" ] || { echo "✗ 没有这个类型模板: $TYPE （看 pack/profiles/）"; exit 1; }
PROF="$HERMES/profiles/$NAME"

echo "==> 1/7 建 profile: ${NAME}（type=${TYPE}, bot=${BOT_NAME}）"
if [ -d "$PROF" ]; then echo "    已存在，复用"; else hermes profile create "$NAME" --no-skills >/dev/null; fi

echo "==> 2/7 装大脑 + 基础配置（从默认 profile 拷，不来自 repo）"
# --no-skills 建的 profile 不带 config.yaml/.env，从默认拷一份完整的（含 model/provider/全部 env）
[ -f "$PROF/config.yaml" ] || cp "$HERMES/config.yaml" "$PROF/config.yaml"
[ -f "$PROF/auth.json" ] || { [ -f "$HERMES/auth.json" ] && cp "$HERMES/auth.json" "$PROF/auth.json"; }
[ -f "$PROF/.env" ] || cp "$HERMES/.env" "$PROF/.env"
# 清空继承来的飞书 creds —— 每个 bot 必须用自己独立的 app，否则撞 token 锁
tmp="$PROF/.env.tmp"
sed -E 's|^FEISHU_APP_ID=.*|FEISHU_APP_ID=|; s|^FEISHU_APP_SECRET=.*|FEISHU_APP_SECRET=|; s|^FEISHU_HOME_CHANNEL=.*|FEISHU_HOME_CHANNEL=|' "$PROF/.env" > "$tmp" && mv "$tmp" "$PROF/.env"
echo "    ✓ config.yaml + auth.json + .env 就位（飞书 creds 已清空待你填）"

echo "==> 3/7 钉 RESEARCH_HOME（共享后台，必须）"
ENVF="$PROF/.env"; touch "$ENVF"
if grep -q '^RESEARCH_HOME=' "$ENVF"; then echo "    已钉"; else
  printf '\n# 共享 research 后台（与总管等共用一份；不钉会落到本 profile 自己的 HOME）\nRESEARCH_HOME=%s/research\n' "$HERMES" >> "$ENVF"
  echo "    ✓ RESEARCH_HOME=$HERMES/research"
fi

echo "==> 4/7 部署技能（按 $TYPE/skills.txt）"
while IFS= read -r raw; do
  line="${raw%%#*}"; line="$(echo "$line" | xargs 2>/dev/null || true)"
  [ -z "$line" ] && continue
  case "$line" in
    lark-*) src="$HERMES/skills/$line";   dst="$PROF/skills/$line";;
    */*)    src="$REPO/pack/skills/$line"; dst="$PROF/skills/$line";;
    *)      echo "    ⚠ 跳过无法识别: $line"; continue;;
  esac
  if [ -d "$src" ]; then mkdir -p "$(dirname "$dst")"; rm -rf "$dst"; cp -r "$src" "$dst"; echo "    ✓ $line"
  else echo "    ⚠ 缺源（跳过）: $src"; fi
done < "$TPL/skills.txt"

echo "==> 5/7 渲染人格 SOUL（替换 {{BOT_NAME}}/{{USER_ADDRESS}}）"
sed -e "s|{{BOT_NAME}}|$BOT_NAME|g" -e "s|{{USER_ADDRESS}}|$USER_ADDRESS|g" "$TPL/SOUL.md" > "$PROF/SOUL.md"
echo "    ✓ $PROF/SOUL.md"

echo "==> 6/7 铺记忆脚手架（不覆盖你已填的）"
mkdir -p "$PROF/memories"
for m in USER MEMORY; do
  tpl="$TPL/$m.template.md"; [ -f "$tpl" ] || tpl="$REPO/pack/profiles/_shared/$m.template.md"
  dst="$PROF/memories/$m.md"
  if [ -s "$dst" ]; then echo "    · $m.md 已有内容，跳过"; else
    sed -e "s|{{BOT_NAME}}|$BOT_NAME|g" -e "s|{{USER_ADDRESS}}|$USER_ADDRESS|g" "$tpl" > "$dst"; echo "    ✓ 铺 $m.md"
  fi
done

echo "==> 7/7 写 profile 描述"
[ -f "$TPL/description.txt" ] && hermes profile describe "$NAME" "$(cat "$TPL/description.txt")" >/dev/null 2>&1 || true

cat <<EOF

✅ ${BOT_NAME}（profile=${NAME}）骨架就绪。接下来【人工】这几步：

  1. 飞书开放平台新建一个独立 app（token 锁不让多 bot 共用一个 app）：
     开「机器人」能力 + 事件订阅选「长连接」并加 im.message.receive_v1，发布版本。
  2. 把 APP_ID / APP_SECRET 填进:  $PROF/.env
       FEISHU_APP_ID=...
       FEISHU_APP_SECRET=...
  3. 开该 bot 需要的 scope（research→base/docx, work→im/contact）。
  4. 填记忆事实:  $PROF/memories/USER.md  和  MEMORY.md
  5. 启动:        $NAME gateway start
  6. 飞书里 DM 它走配对，然后:  hermes -p $NAME pairing list / approve

共享后台已钉好——它和总管读写同一份时间轴/循环/专注/项目。
EOF
