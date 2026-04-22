#!/usr/bin/env bash
# update-docs-readme.sh — 更新 docs/README.md 的文件清单
# 在 ocp 之前调用

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
DOCS_README="$REPO_DIR/docs/README.md"

# 生成文件列表
FILE_LIST=$(cd "$REPO_DIR" && git ls-tree -r HEAD --name-only | grep -v ".gitkeep" | sort)

# 更新 README
cat > "$DOCS_README" << EOF
# 追踪文件清单

> 本目录通过 symlink 追踪真实文件。修改后用 \`ocp\` 提交会自动更新本文件。

## 最后更新

$(date "+%Y-%m-%d %H:%M")

## 追踪文件列表

\`\`\`
$FILE_LIST
\`\`\`
EOF

echo "✅ docs/README.md 已更新"
