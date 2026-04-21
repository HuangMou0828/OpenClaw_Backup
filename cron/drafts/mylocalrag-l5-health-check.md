# mylocalrag-l5-health-check

## 1. 业务意图（一句话）
每天 09:00 检查 myLocalRAG 3030 服务状态和 promotion queue，异常时告警，正常时静默。

## 2. 触发时机
- schedule: `0 9 * * *`
- tz: `Asia/Shanghai`
- 为什么这个点：上班前完成巡检，发现问题有充足时间处理
- 允许抖动：是（默认 stagger 5min）

## 3. 数据来源
- GET http://127.0.0.1:3030/api/health
- GET http://127.0.0.1:3030/api/wiki-vault/promotion-queue?writeReport=0
- ⚠ 用 MCP 工具 `exec` 调用 curl，不在 prompt 里手写原始 http 链接

## 4. 输出产物
- 格式：纯文本巡检报告
- 关键字段：服务状态（ok/error）、workspace 路径、待处理升格数、进行中数
- 长度上限：≤ 300 字

## 5. 交付
- mode: announce（agent 输出报告文本，runner 自动推送）
- channel + to: feishu → user:ou_3c3ad01561a915fe50731a0d71965963
- failureDestination: 继承全局

## 6. 静默条件
- 当 health.ok == true 且无待处理升格候选时 → NO_REPLY（服务健康无需报告）
- ⚠ 注意：正常时不应该发报告，只在异常时才推送

## 7. 幂等与副作用
- 跑 2 次：无副作用，GET 请求幂等
- 执行到一半崩溃：OpenClaw runner 重试，无数据污染风险

## 8. 成本预算
- session: `isolated` — 理由：独立巡检任务，不需要主会话上下文
- model: 默认（MiniMax-M2.7-highspeed）— 理由：简单状态判断，不需要强推理
- thinking: `off` — 理由：纯结构化数据判断，不需要 LLM 推理
- tools 白名单: `exec` — 理由：只需调 3030 API
- lightContext: 是 — 理由：workspace 上下文对纯服务状态巡检无意义
