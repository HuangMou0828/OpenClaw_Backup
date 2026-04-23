# Dreaming 问题排查完整报告

## 结论

Dreaming 的**4888 条待提升、recallCount 全为 0、每日 promoted 极少**，是 OpenClaw Dreaming 对命名 agent 场景**支持不完整**导致的功能缺口，不是配置错误或门槛设置问题。

---

## 现象

- Dreaming UI：「4888 等待中 · 4 今日已提升」
- 几乎所有候选条目的 `recallCount = 0`
- `short-term-recall.json` 有 4892 条，全是 `memory/YYYY-MM-DD.md` 里的运营日志片段
- `session-corpus/` 目录不存在，`session-ingestion.json` 从未生成

---

## 排查过程

### 1. session 数据实际位置确认
- 实际路径：`~/.openclaw/agents/main/sessions/`（160 个 jsonl 文件）
- Dreaming 内置默认路径：`~/.openclaw/sessions/`（不存在）

### 2. 根因分析
- 用了命名 agent（main），session 数据在 `agents/main/sessions/`
- Dreaming 的 `sessionCorpusDir` 没有适配命名 agent 目录结构，指向默认的 `~/.openclaw/sessions/`
- 这是**功能不完整**，不是写错——OpenClaw 可能只测试过默认 agent 场景

### 3. fallback 机制确认
- changelog v2026.4.10 提到："harden request-scoped diary **fallback** so scheduled dreaming **only falls back on the dedicated subagent-runtime error**"
- fallback 是**有意的 resilience 设计**，但只针对 subagent-runtime error，不应常态触发
- 当前 fallback 常态化触发，是因为 corpus 采集器始终为空（命名 agent 路径不匹配）

### 4. 噪音来源
- 之前做 history backfill，把 `memory/` 下所有 daily notes 回填进 dreaming 队列
- 这些全是运营日志（cron 记录、heartbeat 结果、健康巡检报告），不是知识记忆
- 在 fallback 模式下，这些噪音占满了 recall 队列

---

## 关键发现

### changelog 证据
- fallback 只应在 "dedicated subagent-runtime error" 时触发，不应常态
- changelog 中**完全没有提到命名 agent 场景**的支持或限制说明
- v2026.4.11 开始有跨天 session-corpus 的 bug（#65472），说明 corpus 采集本身就是脆弱的功能

### 相关 GitHub Issues
| # | 标题 | 状态 |
|---|------|------|
| #70104 | REM re-pins to stale corpus, 0 promoted every night | open |
| #65472 | session-corpus not generated when session spans multiple days | open |
| #68876 | filter cron-triggered sessions from dreaming corpus | open |

---

## 准确的问题定性

> Dreaming 的 session corpus 采集器没有适配命名 agent 的目录结构（`agents/<name>/sessions/`），导致始终处于 fallback 模式。这是**功能缺口**：文档和 changelog 均未说明 Dreaming 对命名 agent 的支持边界，用户无从得知这一限制。

---

## 当前状态

- Dreaming REM 阶段仍在运行（DREAMS.md 有 Dream Diary 输出）
- 降级运行：依赖 daily memory 而非 session 语料
- 4892 条噪音不影响其他功能
- OpenClaw 4.21 三个 issue 均 open 未修复

---

## 建议

1. **等官方修复**：#70104/#65472/#68876 修复后，命名 agent 场景的 corpus 采集可能恢复正常
2. **清理噪音**（可选）：
   ```bash
   openclaw memory rem-backfill --rollback
   openclaw memory rem-backfill --rollback-short-term
   ```
3. **给官方提 issue**：如果需要，可以在 #70104 下补充"命名 agent 路径不匹配"的发现，帮助团队定位

---

## 时间线

- 14:08 — 开始排查 4888 等待中现象
- 14:39 — 确认 session-corpus 目录为空
- 14:43 — 找到 session 数据实际在 `agents/main/sessions/`
- 14:48 — 确认是命名 agent 路径不匹配，非写错
- 14:51 — 确认 fallback 是有意的 resilience 机制
- 15:28 — 查 changelog，确认 fallback 只应针对 subagent-runtime error，命名 agent 场景从未被提及
