#!/usr/bin/env bash
set -euo pipefail

REPO="$(cd "$(dirname "$0")" && pwd)"
HERMES="${HERMES_HOME:-$HOME/.hermes}"
RESEARCH="$HERMES/research"

echo "==> 安装 Python 包"
PIP="${PIP:-}"
if [ -z "$PIP" ]; then
  if command -v pip  >/dev/null 2>&1; then PIP="pip"
  elif command -v pip3 >/dev/null 2>&1; then PIP="pip3"
  elif python3 -m pip --version >/dev/null 2>&1; then PIP="python3 -m pip"
  else
    echo "    找不到 pip。先装 Python 3（macOS：brew install python），或用 PIP=... 指定。" >&2
    exit 1
  fi
fi
echo "    用 $PIP"
$PIP install -e "$REPO"

echo "==> 建目录"
mkdir -p "$RESEARCH/state/papers" "$RESEARCH/state/timeline" \
         "$HERMES/skills/research"

echo "==> 配置文件"
if [ ! -f "$RESEARCH/prefs.yaml" ]; then
  cp "$REPO/pack/prefs.example.yaml" "$RESEARCH/prefs.yaml"
  echo "    已生成 $RESEARCH/prefs.yaml —— 记得填你的方向关键词"
else
  echo "    已存在 $RESEARCH/prefs.yaml，跳过"
fi

echo "==> 安装技能"
cp -r "$REPO/pack/skills/research/." "$HERMES/skills/research/"

echo "==> 合并 SOUL 人设（幂等）"
SOUL="$HERMES/SOUL.md"
touch "$SOUL"
if grep -q "BEGIN research-assistant persona" "$SOUL"; then
  python3 - "$SOUL" "$REPO/pack/SOUL.snippet.md" <<'PY'
import re, sys
soul_path, snip_path = sys.argv[1], sys.argv[2]
soul = open(soul_path, encoding="utf-8").read()
snip = open(snip_path, encoding="utf-8").read()
soul = re.sub(
    r"<!-- BEGIN research-assistant persona.*?END research-assistant persona -->",
    lambda _m: snip.strip(), soul, flags=re.S)
open(soul_path, "w", encoding="utf-8").write(soul)
PY
  echo "    已更新 SOUL 人设片段"
else
  printf "\n\n%s\n" "$(cat "$REPO/pack/SOUL.snippet.md")" >> "$SOUL"
  echo "    已追加 SOUL 人设片段"
fi

echo
echo "==> 还差最后一步：注册定时任务（cron 的确切 CLI 参数因 Hermes 版本而异）"
echo "    方式 A（推荐，自然语言）：在飞书对 Hermes 说（逐条）："
echo '      "每天早上9点跑 arxiv-digest 技能，结果发飞书"'
echo '      "每天早上8点半跑 morning-plan 技能，结果发飞书"'
echo '      "每天晚上10点跑 evening-review 技能，结果发飞书"'
echo "    方式 B（命令行）：参考 \`hermes cron --help\`，按 pack/cron/jobs.snippet.json 注册"
echo
echo "完成。先 \`research-assistant fetch\` 自测，再用 cron 跑一次端到端。"
