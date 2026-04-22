#!/usr/bin/env bash
# update-docs-readme.sh — 更新时间戳
# docs/README.md 不再需要全局文件清单

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
DOCS_README="$REPO_DIR/docs/README.md"

# 更新时间戳
sed -i.bak "s/最后更新.*/最后更新：$(date '+%Y-%m-%d %H:%M')/" "$DOCS_README" 2>/dev/null || true
rm -f "${DOCS_README}.bak"

echo "✅ docs/README.md 时间戳已更新"
