# mylocalrag-weekly-promotion-queue-report

## 1. 业务意图（一句话）
每周五 17:30 生成 L5 升格队列周报，通过 announce 推送。

## 2. 触发时机
- schedule: `30 17 * * 5`（周五 17:30）
- tz: `Asia/Shanghai`
- 为什么这个点：周末前复盘本周升格情况

## 3. 数据来源
- 运行 python3 /Users/hm/.openclaw/workspace/scripts/mylocalrag-queue-report.py --skeleton
- 或 GET http://127.0.0.1:3030/api/wiki-vault/promotion-queue?writeReport=0

## 4. 输出产物
- 格式：纯文本周报
- 关键字段：本周队列变化、待处理候选数、已升格数
- 若队列为空：输出「本周无待处理升格候选 ✅」

## 5. 交付
- mode: announce
- channel+to: feishu → user:ou_3c3ad01561a915fe50731a0d71965963
- failureDestination: 继承全局

## 6. 静默条件
- 若队列为空（approvedSyntheses==0 且无 pending）：静默（NO_REPLY）

## 7. 幂等与副作用
- 跑 2 次：无副作用，GET 请求幂等

## 8. 成本预算
- session: `isolated`
- model: 默认
- thinking: `off`
- tools 白名单: `exec`
- lightContext: 是
