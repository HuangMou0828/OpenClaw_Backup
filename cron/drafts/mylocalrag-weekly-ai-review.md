# mylocalrag-weekly-ai-review

## 1. 业务意图（一句话）
每周一 09:30 生成 myLocalRAG AI 使用复盘和 skill 候选建议，通过 announce 推送。

## 2. 触发时机
- schedule: `30 9 * * 1`（周一 09:30）
- tz: `Asia/Shanghai`
- 为什么这个点：周初复盘，开启新一周工作

## 3. 数据来源
- GET http://127.0.0.1:3030/api/review（body: {"recentDays": 7, "minRepeatedPrompt": 2}）
- 可选：POST http://127.0.0.1:3030/api/summary（分析高频低质量 prompt）
- ⚠ 用 exec 工具调用 curl

## 4. 输出产物
- 格式：纯文本周报
- 关键字段：本周对话数、Token 消耗、重复 Prompt 分析、Skill 候选建议
- 长度：适中（结构化报告）

## 5. 交付
- mode: announce
- channel+to: feishu → user:ou_3c3ad01561a915fe50731a0d71965963
- failureDestination: 继承全局

## 6. 静默条件
- 若服务不可用：输出「服务不可用，请检查 3030 服务状态」并静默

## 7. 幂等与副作用
- 跑 2 次：GET 请求幂等，报告内容因时间不同自然不同
- 执行到一半崩溃：OpenClaw 重试，无数据污染

## 8. 成本预算
- session: `isolated`
- model: 默认
- thinking: `off`
- tools 白名单: `exec`
- lightContext: 是
