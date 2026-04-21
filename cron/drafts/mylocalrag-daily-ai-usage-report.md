# mylocalrag-daily-ai-usage-report

## 1. 业务意图（一句话）
每天 20:30 生成 myLocalRAG AI 使用复盘报告，通过 announce 推送。

## 2. 触发时机
- schedule: `30 20 * * *`（每天 20:30）
- tz: `Asia/Shanghai`
- 为什么这个点：晚间复盘全天 AI 使用情况

## 3. 数据来源
- 运行 python3 /Users/hm/.openclaw/workspace/scripts/mylocalrag-daily-summary.py
- 或 GET http://127.0.0.1:3030/api/daily-summary

## 4. 输出产物
- 格式：纯文本报告
- 关键字段：今日对话数、Token 消耗、Top Queries、洞察
- 长度：适中

## 5. 交付
- mode: announce
- channel+to: feishu → user:ou_3c3ad01561a915fe50731a0d71965963
- failureDestination: 继承全局

## 6. 静默条件
- 若获取失败：输出「获取日报失败，请检查服务状态」并静默

## 7. 幂等与副作用
- 跑 2 次：无副作用，GET 请求幂等

## 8. 成本预算
- session: `isolated`
- model: 默认
- thinking: `off`
- tools 白名单: `exec`
- lightContext: 是
