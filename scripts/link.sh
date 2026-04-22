#!/usr/bin/env bash
# link.sh — 新机器上把仓库文件链回原位置
# 用法: ./scripts/link.sh

set -euo pipefail
REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"

# ===== 映射表：仓库内相对路径 :: 本机绝对路径 =====
declare -a LINKS=(
  "cron/jobs.json::/Users/hm/.openclaw/cron/jobs.json"
  "mcp/messaging-sender/::/Users/hm/messaging-sender/"
  "docs/::/Users/hm/docs/"
)
# =========================================================

for entry in "${LINKS[@]}"; do
  SRC="$REPO_DIR/${entry%%::*}"
  DEST="${entry##*::}"
  mkdir -p "$(dirname "$DEST")"
  if [[ -e "$DEST" && ! -L "$DEST" ]]; then
    echo "⚠ 跳过（目标已存在且非软链接）: $DEST"
    continue
  fi
  ln -sfn "$SRC" "$DEST"
  echo "✓ 链接: $DEST -> $SRC"
done
