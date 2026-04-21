# Cron Jobs Inventory

共 11 条 job，采集时间：2026-04-21

| name | schedule | session | agent | delivery | 一句话 intent | 技术动作 |
|------|----------|---------|-------|----------|--------------|---------|
| mylocalrag-l5-health-check | 0 9 * * * | current | main | feishu→黄谋 | myLocalRAG L5 健康巡检（服务+队列） | lsof:3030 / GET /api/health / GET /api/wiki-vault/promotion-queue |
| mylocalrag-openclaw-inbox-import | 0 18 * * * | current | main | feishu→黄谋 | inbox 兜底导入 | python3 mylocalrag-inbox-import.py |
| mylocalrag-daily-ai-usage-report | 30 20 * * * | current | main | feishu→黄谋 | 每日 AI 使用复盘 | lsof:3030 / POST /api/review / message工具发送 |
| mylocalrag-weekly-ai-review | 30 9 * * 1 | current | main | feishu→黄谋 | 每周 AI 使用复盘+skill候选 | lsof:3030 / POST /api/review / POST /api/prompt-score / POST /api/prompt-optimize |
| mylocalrag-weekly-promotion-queue-report | 30 17 * * 5 | current | main | feishu→黄谋 | Promotion Queue 周报 | python3 mylocalrag-queue-report.py --skeleton |
| 工作日待办截止提醒 | 0 17 * * 1-5 | current | main | feishu→黄谋 | 飞书待办截止提醒 | python3 feishu-todo-refine.py |
| 工作日待办批量流转 | 20 20 * * 1-5 | current | main | feishu→黄谋 | 飞书待办批量流转+报告 | python3 preformat-todo-today.py / MCP transition_node |
| daily-memory-promote | 0 */8 * * * | current | main | feishu→黄谋 | 每8小时晋升 .learnings→MEMORY.md | bash cron-update-state.sh / read .learnings/*.md |
| EvoMap每日观测报告 | 0 21 * * * | current | main | feishu→黄谋 | EvoMap 进化观测日报 | node index.js / read evolution_solidify_state.json / read personality_state.json |
| AI每日热点简报 | 0 10 * * * | isolated | main | Discord | AI 热点简报发 Discord | ai-news-digest skill |
| Memory Dreaming Promotion | 0 3 * * * | main | - | 无 | memory-core 自动晋升（systemEvent） | 无外部调用 |

---
## Phase 2 Agent 预设判断

**可共用人设的 job**：无。所有 job 业务 intent 差异大，没有两个 job 共享同一套"系统提示+工具白名单+模型配置"。

- myLocalRAG 系列：虽有关联，但每个 job 的 prompt 逻辑差异大（health / review / report / queue）
- 飞书待办系列：两个 job intent 不同（提醒 vs 流转）

**结论：Phase 2 可跳过。** 如需优化，考虑针对"myLocalRAG 系列"单独建一个 agent（3-4 个 job 共用），但投入收益比一般。

---

## Phase 3 MCP 工具判断

**≥3 个 job 共用的技术动作**：

| 技术动作 | 出现在几个 job | 现状 | 决定 |
|---------|--------------|------|------|
| `lsof -i :3030` + 3030 API 调用 | 3个（l5-health / daily-review / weekly-review） | prompt 里手写 curl | 可抽象，但 3030 是本地服务，建通用工具有限 |
| python3 xxx.py 脚本调用 | 4个（inbox-import / weekly-queue / todo-remind / todo-flow） | 各 job 独立脚本 | 脚本本身是幂等的，可考虑合并到同一脚本通过参数区分 |
| 发飞书消息 | 9个 | message 工具 | 已有 MCP，不需要新建 |

**≥3 个 job 共用的技术动作只有一组**：`lsof:3030 + 3030 API` 出现在 3 个 myLocalRAG job。

**结论：Phase 3 可跳过。** 3030 API 是 myLocalRAG 内部接口，建通用 MCP 收益有限。

---

## 总结

| Phase | 结论 |
|-------|------|
| Phase 0.1 | ✅ 已完成：备份 + git |
| Phase 0.2 | ✅ 已盘点完毕 |
| Phase 2 Agent预设 | ⏭ 跳过（无明显人设共性） |
| Phase 3 MCP工具 | ⏭ 跳过（共用动作不足以值得建工具） |
| Phase 4 failureDestination | ✅ 建议做（一次配置全员受益） |
