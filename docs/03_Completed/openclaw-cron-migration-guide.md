# OpenClaw Cron 治理指南（精简版）

> 适用规模：10~20 个 cron job，intent 异质、复用度不高。
>
> 核心思路：**不做模板编译**。`openclaw cron list --json` 就是 source of truth，改动走 **diff + patch + 原生 CLI**。只投资那些 10 个 job 都能吃到红利的动作。
>
> 使用方式：把本文件交给 OpenClaw agent 顺序执行。每一步带 Verify，不过不进下一步。

---

## 投资范围（只做这四件）

| # | 动作 | 为什么值得做 |
|---|------|-------------|
| 1 | `jobs.json` 纳入 git，建立 diff 工作流 | 改动可 review / 可回滚，成本几乎为零 |
| 2 | 抽 2~3 个 agent 预设，卸掉重复的系统提示/模型/工具白名单 | 10 个 job 至少能共享 2-3 种"人设"，改一处全局生效 |
| 3 | 把 prompt 里重复出现的**技术动作**换成 MCP tool 调用 | prompt 越短越稳；工具是真正可复用的原子 |
| 4 | 设全局 `failureDestination` | 一次配置，10 个 job 全体获得失败兜底告警 |

**不做的事**（明确砍掉）：
- ❌ 写编译器 / mustache 模板 / Makefile — 10 个 job 压不出复用，纯负担
- ❌ 批量按 intent 归类模板 — job 天然异质
- ❌ 全部分支逻辑外移到 hooks — 除非某条 job 真有复杂分支，否则不碰
- ❌ Custom session 统一改造 — 只在明确受益的 1~2 条上用

---

## Phase 0 — 备份与入仓（安全网）

### 0.1 快照 + git

**Action**
```bash
mkdir -p cron
cp ~/.openclaw/cron/jobs.json cron/jobs.json
openclaw cron list --json > cron/jobs.list.json

git add cron/ && git commit -m "chore: snapshot openclaw cron baseline"
git tag pre-migration
```

**Verify**
```bash
git tag | grep pre-migration
jq 'length' cron/jobs.json
```

**完成标志**：仓库里有 baseline，`pre-migration` tag 已打。

---

### 0.2 快速过一眼 intent

**Action**：让 agent 读 `cron/jobs.json`，生成 `cron/INVENTORY.md`：

```markdown
| name | schedule | session | agent | delivery | 一句话 intent | message 行数 |
|------|----------|---------|-------|----------|--------------|-------------|
```

同时在文件末尾回答两个问题（供人看）：
- 哪些 job 的"系统提示/输出风格/工具白名单"可以共用？→ 这些是 Phase 2 的 agent 候选
- 哪些"技术动作短语"在 ≥3 个 job 的 message 里出现？→ 这些是 Phase 3 的 MCP tool 候选

**Verify**：人工扫一遍 `INVENTORY.md`，确认上述两问有具体答案。

⚠ **HUMAN CHECKPOINT**：如果两问的答案都是"没有明显共性"，那 Phase 2、3 可以跳过，直接做 Phase 4 收尾。

---

## Phase 1 — 建立 diff+patch 工作流（替代编译）

目标：以后改 cron = 改 `cron/jobs.json` + git diff + 用原生 CLI 推上去。

### 1.1 写两个小脚本（30 行内，非编译器）

**Action**
```bash
cat > cron/diff.sh <<'EOF'
#!/usr/bin/env bash
# 对比本地 cron/jobs.json 和 live cron
set -e
openclaw cron list --json > /tmp/openclaw-live.json
diff -u <(jq -S . /tmp/openclaw-live.json) <(jq -S . cron/jobs.json) || true
EOF

cat > cron/apply.sh <<'EOF'
#!/usr/bin/env bash
# 把本地改动按 job 粒度推到 live（不覆盖 jobs.json 整体，走 CLI 保证兼容）
set -e
jq -c '.[]' cron/jobs.json | while read -r job; do
  name=$(jq -r '.name' <<< "$job")
  # 按 name 查 live 是否存在
  id=$(openclaw cron list --json | jq -r --arg n "$name" '.[] | select(.name==$n) | .id' | head -1)
  if [ -z "$id" ]; then
    echo "ADD  $name"
    # 交互式确认，避免误伤
    read -p "  push new job '$name'? [y/N] " ok && [[ "$ok" == "y" ]] || continue
    # 真实参数从 $job 里拼，见 README 示例；此处留给人工 / agent 补齐
  else
    echo "EDIT $name ($id)"
    read -p "  patch '$name'? [y/N] " ok && [[ "$ok" == "y" ]] || continue
  fi
done
EOF
chmod +x cron/*.sh
```

**说明**：`apply.sh` 故意保持**半自动 + 逐条确认**。10 个 job 量级完全够用，也避免把自动化做成新黑盒。

**Verify**
```bash
./cron/diff.sh   # 首次应输出空（刚快照）
```

---

### 1.2 README 写清楚工作流

**Action**
```bash
cat > cron/README.md <<'EOF'
# OpenClaw Cron 管理

Source of truth: `cron/jobs.json`（从 `openclaw cron list --json` 导出）

## 改动流程
1. `./cron/diff.sh` 看是否与 live 一致（应该一致；否则先 re-sync）
2. 编辑 `cron/jobs.json`（直接改 JSON）或通过 `openclaw cron edit` 改 live
3. `./cron/diff.sh` 看差异
4. `./cron/apply.sh` 逐条确认推上去
5. `openclaw cron list --json > cron/jobs.json && git commit`

## Re-sync（当 live 被旁路修改过）
openclaw cron list --json > cron/jobs.json
git diff cron/jobs.json   # 人工审核

## 回滚
git checkout pre-migration -- cron/jobs.json
./cron/apply.sh
EOF
```

**Verify**：`cat cron/README.md`，流程对得上。

**完成标志**：以后每次改 cron 都走这套 diff + commit，不再手工记录改了什么。

---

## Phase 2 — 抽 Agent 预设（按 INVENTORY 的实际情况酌情做）

> **前置判断**：Phase 0.2 找出了 ≥2 组可共用"人设"的 job，才做这一 Phase。否则跳过。

### 2.1 起草 agent（数量跟着实际共性走，2 个就 2 个）

以"报告类"举例：

**Action**
```bash
mkdir -p agents
cat > agents/reporter.yaml <<'EOF'
id: reporter
system: |
  你是值班汇报 Agent。
  - 外部数据必须通过工具获取，不要编造
  - 输出简洁的 markdown 卡片，关键数字加粗
  - 数据为空时回复单行 "NO_REPLY" 结束
tools: [github_*, sentry_*, lark_send_card, lark_send_text]
model: openai/gpt-5.4-mini
thinking: medium
EOF
```

加载方式依你 gateway 版本（通常在 `~/.openclaw/config.json5` 的 `agents` 字段引用，或 CLI 注册；以 `openclaw --help` / `openclaw agent --help` 为准）。

**Verify**
```bash
openclaw agent list 2>/dev/null || echo "check gateway docs for agent loading"
```

---

### 2.2 冒烟：新建一个一次性 cron 用这个 agent

**Action**
```bash
openclaw cron add \
  --name "smoke-reporter" \
  --at "60s" \
  --session isolated \
  --agent reporter \
  --message "回复 NO_REPLY" \
  --deliver none \
  --delete-after-run
```

**Verify**（~90s 后）
```bash
openclaw cron runs --limit 3
```

**完成标志**：agent 能被 cron 正常调起。

---

### 2.3 迁移候选 job 到这个 agent

对 INVENTORY 里标过"可用 reporter"的 job：

**Action**
```bash
# 每条单独做，确认一条再做下一条
openclaw cron edit <jobId> --agent reporter
# 从 message 里删掉现在被 agent 系统提示覆盖的段落（风格指令、工具提示等），保留业务意图
openclaw cron edit <jobId> --message "精简后的 message"

# 立刻强制跑一次验证
openclaw cron run <jobId>
sleep 20
openclaw cron runs --id <jobId> --limit 1
```

**Verify**：人工看目标渠道产物，格式、内容无回退。

**完成标志**：每迁完一条 `cron list --json > cron/jobs.json && git commit -m "refactor: move <name> to reporter agent"`。

⚠ **HUMAN CHECKPOINT**：每迁一条就提交一次，出问题 `git revert` 回得来。

---

## Phase 3 — 抽 MCP 工具（只动那些 ≥3 个 job 共用的技术动作）

> **前置判断**：Phase 0.2 找出了 ≥3 个 job 共用的"技术动作"。否则跳过。
>
> 本 Phase **不教**怎么写 MCP tool（独立工程）。只给**识别 → 换入**的流程。

### 3.1 列候选

**Action**：写 `tools/TODO.md`：

```markdown
| 技术动作 | 出现在几个 job | 现状 | 决定 |
|---------|--------------|------|------|
| 拉今日 merged PR | 4 | 无工具，prompt 手写 curl | 新建 github.list_merged_prs |
| 发飞书卡片 | 7 | 已有 lark_send_card | 直接替换 |
| 查 Sentry top error | 2 | 只 2 个 job，不值 | 暂不做 |
```

**Verify**：列表里每条都有"决定"。**少于 3 个 job 共用的一律不做**。

---

### 3.2 替换进 message

工具就绪后，按 job 逐个替换：

**Action**（示例）
```bash
openclaw cron edit <jobId> --message "拉 org/repo 今天 merged 的 PR（用 github.list_merged_prs），汇总关键点，通过 lark_send_card 发到 oc_xxx。"
openclaw cron run <jobId>
```

**Verify**：强制跑一次，确认工具被调用且结果正常。

**完成标志**：改一条 commit 一条。

---

## Phase 4 — 失败告警兜底（一次配置全员受益）

### 4.1 全局 failureDestination

**Action**：编辑 `~/.openclaw/config.json5`：

```json5
{
  cron: {
    failureDestination: {
      mode: "announce",
      channel: "lark",
      to: "oc_oncall_group_id"
    }
  }
}
```

重启 gateway。

**Verify**：人为造一个失败 job（`--message "调用不存在的工具 xxx_fake_tool"`），观察 oncall 群是否收到失败通知。

```bash
openclaw cron add --name "fail-smoke" --at "30s" --session isolated --agent reporter \
  --message "请调用 xxx_fake_tool 并等待结果" --delete-after-run
```

**完成标志**：oncall 群收到失败通知；`fail-smoke` 已自动清除。

---

## Phase 5 — 收尾

### 5.1 同步快照 + tag

**Action**
```bash
openclaw cron list --json > cron/jobs.json
git add -A && git commit -m "feat: openclaw cron governance v1"
git tag governance-v1
```

### 5.2 往后的日常

- 新 cron：直接 `openclaw cron add ...`，跑通后 `openclaw cron list --json > cron/jobs.json && git commit`
- 改 cron：`openclaw cron edit <id> ...`，同上
- 合适的场景（人设能匹配）就 `--agent reporter`；不合适就 inline message，**不强求套**

---

## 附录 A — 回滚

```bash
git checkout pre-migration -- cron/jobs.json
./cron/apply.sh           # 逐条确认把老状态推回去
```

## 附录 B — 常用命令

```bash
openclaw cron list --json
openclaw cron show <id>
openclaw cron run <id>
openclaw cron runs --id <id> --limit 10
openclaw cron status
openclaw logs --follow
```

## 附录 C — 完成判定

- [ ] `git tag` 有 `pre-migration` 和 `governance-v1`
- [ ] `cron/jobs.json` 与 live 一致（`./cron/diff.sh` 输出空）
- [ ] 至少 1 个 agent 被 ≥3 个 job 复用（若 Phase 2 跳过则免）
- [ ] 失败告警演练通过
- [ ] README 写明改动流程
