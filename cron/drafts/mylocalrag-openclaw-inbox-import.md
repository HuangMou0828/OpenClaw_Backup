# mylocalrag-openclaw-inbox-import

## 1. 业务意图（一句话）
每天 18:00 消费 ~/.openclaw/knowledge/inbox，将新增/归档/失败的条目汇总发给黄谋。

## 2. 触发时机
- schedule: `0 18 * * *`
- tz: `Asia/Shanghai`
- 为什么这个点：下班前，让黄谋知道今天沉淀了哪些内容
- 允许抖动：是（默认 stagger 5min）

## 3. 数据来源
- POST http://127.0.0.1:3030/api/openclaw-knowledge/import（请求体 {}）
- GET http://127.0.0.1:3030/api/wiki-vault/promotion-queue?writeReport=0
- ⚠ 用 MCP 工具 `exec` 调用 curl，不在 prompt 里手写 http 链接

## 4. 输出产物
- 格式：纯文本
- 关键字段：新增数、归档数、失败数、升格候选数
- 长度上限：≤ 300 字

## 5. 交付
- mode: none（消息由 feishu-sender MCP 发出，runner 不二次推送）
- channel + to: feishu → user:ou_3c3ad01561a915fe50731a0d71965963
- failureDestination: 继承全局（失败告警 → 黄谋飞书）

## 6. 静默条件
- 当 imported=0 且 archived=0 且 failed=0 时 → NO_REPLY
- 当 API 返回 HTTP 403（额度不足）时 → NO_REPLY
- 当 promotion-queue 为空时 → 消息中不追加候选提示（不属于静默，正常行为）

## 7. 幂等与副作用
- 跑 2 次：重复发消息（用户会看到两条同步报告） → **本 job 已要求 delivery=none，发消息全走 MCP，幂等由 MCP 内部处理**
- 如果执行到一半崩溃：下次重跑无副作用（import API 本身幂等）

## 8. 成本预算
- session: `isolated` — 理由：独立 job，不需要主会话上下文
- model: 默认（MiniMax-M2.7-highspeed）— 理由：轻量查询+格式化，无需强推理
- thinking: `off` — 理由：纯规则数据格式化，不需要 LLM 推理
- tools 白名单: `exec` — 理由：只需调 3030 API，其他工具不需要
- lightContext: 是 — 理由：workspace 上下文对纯数据任务无意义
