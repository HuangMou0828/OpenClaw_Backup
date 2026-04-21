# OpenClaw Cron 管理

Source of truth: `cron/jobs.json`（从 `openclaw cron list --json` 导出）

## 工作流

### 改 cron 流程
```
1. openclaw cron list --json > cron/jobs.json   # 先同步最新
2. ./cron/diff.sh                              # 确认当前无差异
3. openclaw cron add ...   或  openclaw cron edit <id> ...
4. openclaw cron list --json > cron/jobs.json   # 改动推回文件
5. ./cron/diff.sh                              # 确认改动符合预期
6. git add -A && git commit -m "feat: ..."
```

### Re-sync（live 被旁路修改过）
```bash
openclaw cron list --json > cron/jobs.json
./cron/diff.sh
```

### 回滚
```bash
git checkout <tag/commit> -- cron/jobs.json
./cron/apply.sh --dry-run   # 先看差异
./cron/apply.sh --force     # 确认后推上去
```

## 脚本说明

| 脚本 | 作用 |
|------|------|
| `./diff.sh` | 对比本地 jobs.json 与 live，无差异输出"✅ 一致" |
| `./apply.sh` | 把本地 jobs.json 逐条 push 到 live，**默认询问确认** |

### apply.sh 用法
```bash
./apply.sh --dry-run   # 只打印要做什么，不执行
./apply.sh --force     # 不询问，直接执行（危险）
./apply.sh             # 逐条询问（默认）
```

## 添加新 cron 示例
```bash
openclaw cron add \
  --name "test-cron" \
  --cron "0 9 * * *" \
  --tz "Asia/Shanghai" \
  --session isolated \
  --message "回复 OK" \
  --deliver none \
  --delete-after-run
```

## 删除 cron
```bash
openclaw cron remove <jobId>
```

## 常用命令
```bash
openclaw cron list --json
openclaw cron show <id>
openclaw cron run <id>
openclaw cron runs --id <id> --limit 5
openclaw cron status
```
