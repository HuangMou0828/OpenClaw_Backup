#!/usr/bin/env bash
# 从环境变量（由 ~/.zshrc 从 macOS Keychain 加载）生成
# mcp/messaging-sender/config.json。重装机器或轮换密钥后跑一次即可。
#
# Usage:
#   bash scripts/render-messaging-config.sh

set -euo pipefail

DEST="$(cd "$(dirname "$0")/.." && pwd)/mcp/messaging-sender/config.json"

: "${FEISHU_APP_ID:?FEISHU_APP_ID 未设置（检查 ~/.zshrc）}"
: "${FEISHU_APP_SECRET:?FEISHU_APP_SECRET 未设置（检查 Keychain：security find-generic-password -a \"\$USER\" -s feishu-app-secret -w）}"
: "${DISCORD_BOT_TOKEN:?DISCORD_BOT_TOKEN 未设置（检查 Keychain：security find-generic-password -a \"\$USER\" -s discord-bot-token -w）}"

umask 077
cat > "$DEST" <<EOF
{
  "feishu": {
    "app_id": "${FEISHU_APP_ID}",
    "app_secret": "${FEISHU_APP_SECRET}"
  },
  "discord": {
    "bot_token": "${DISCORD_BOT_TOKEN}"
  }
}
EOF
chmod 600 "$DEST"

echo "✓ Rendered $DEST (mode 600)"
