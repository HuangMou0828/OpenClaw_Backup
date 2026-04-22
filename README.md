# OpenClaw Config

黄谋的 OpenClaw + AI 工具配置仓库。

## 结构

```
openclaw-config/
├── cron/                  ← OpenClaw cron jobs（symlink 回 ~/.openclaw/cron/jobs.json）
├── mcp/
│   └── messaging-sender/  ← MCP server（symlink 回 ~/messaging-sender/）
└── docs/                  ← 笔记分类（symlink 回 ~/docs/）
```

## 日常使用

```bash
# 克隆到新机器后，恢复 symlink
ln -s ~/openclaw-config/cron/jobs.json ~/.openclaw/cron/jobs.json
ln -s ~/openclaw-config/mcp/messaging-sender ~/messaging-sender
ln -s ~/openclaw-config/docs ~/docs
```

```bash
# 查看当前追踪的文件
git ls-tree -r HEAD --name-only | grep -v '.gitkeep'

# 提交改动
git add -A && git commit -m "update" && git push
```
