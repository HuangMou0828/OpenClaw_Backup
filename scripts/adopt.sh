#!/usr/bin/env bash
# adopt.sh — 把散落文件收编进仓库
# 用法: ./scripts/adopt.sh <原文件绝对路径> <cron|mcp|docs>
# 示例: ./scripts/adopt.sh /some/path/config.json cron

set -euo pipefail

SRC="${1:-}"
CATEGORY="${2:-}"
[[ -z "$SRC" || -z "$CATEGORY" ]] && { echo "用法: $0 <原路径> <cron|mcp|docs>"; exit 1; }

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
DEST_DIR="$REPO_DIR/$CATEGORY"
FILENAME="$(basename "$SRC")"
DEST="$DEST_DIR/$FILENAME"

[[ -e "$SRC" ]] || { echo "源文件不存在: $SRC"; exit 1; }
[[ -d "$DEST_DIR" ]] || { echo "无效分类目录: $CATEGORY"; exit 1; }
[[ -L "$SRC" ]] && { echo "$SRC 已经是软链接，跳过"; exit 0; }
[[ -e "$DEST" ]] && { echo "仓库内已存在同名文件: $DEST，请手动处理"; exit 1; }

mv "$SRC" "$DEST"
ln -s "$DEST" "$SRC"
echo "✓ 已收编: $SRC -> $DEST"
