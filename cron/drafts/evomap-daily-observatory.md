# evomap-daily-observatory

## 1. 业务意图（一句话）
每天 21:00 运行 EvoMap 更新数据，生成人类可读的进化观测报告并发送到飞书。

## 2. 触发时机
- schedule: `0 21 * * *`
- tz: `Asia/Shanghai`
- 为什么这个点：收盘后观测，全天数据已收集完毕

## 3. 数据来源
- 运行 /Users/hm/.openclaw/workspace/evolver/index.js（工作目录：/Users/hm/.openclaw/workspace/evolver）
- 读取 evolution_solidify_state.json、personality_state.json

## 4. 输出产物
- 格式：纯文本中文报告（禁止 Markdown 表格）
- 关键字段：信号列表、选中基因、人格状态、策略、简报
- 长度：适中

## 5. 交付
- mode: none
- 发送：调用 messaging-sender/send_to_feishu({receive_id: "ou_3c3ad01561a915fe50731a0d71965963", receive_id_type: "open_id", msg_type: "text", content: "{\"text\":\"" + 报告全文 + "\"}"})
- failureDestination: 继承全局

## 6. 静默条件
- 本 job 为每日报告，**不禁静默**

## 7. 幂等与副作用
- 跑 2 次：会生成两份相同报告并发送两次（EvoMap 自身逻辑）
- 执行到一半崩溃：OpenClaw 重试，可能生成重复报告但不影响数据

## 8. 成本预算
- session: `isolated`
- model: 默认
- thinking: `medium`（需要理解 EvoMap 状态生成分析）
- tools 白名单: `exec,read`（读文件+跑脚本）
- lightContext: 是
