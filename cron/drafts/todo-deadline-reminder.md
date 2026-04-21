# todo-deadline-reminder

## 1. 业务意图（一句话）
每个工作日 17:00 检查当日截止的飞书任务，生成提醒文本并通过 announce 推送。

## 2. 触发时机
- schedule: `0 17 * * 1-5`（周一至周五 17:00）
- tz: `Asia/Shanghai`
- 为什么这个点：下班前提醒，用户有时间处理今日截止任务

## 3. 数据来源
- 执行 `python3 /Users/hm/.openclaw/workspace/scripts/feishu-todo-refine.py`
- 脚本输出纯文本即为报告内容

## 4. 输出产物
- 格式：纯文本提醒
- 直接输出脚本结果，不调用任何发送工具（announce delivery 自动推送）

## 5. 交付
- mode: announce（输出文本，runner 自动推送飞书）
- failureDestination: 继承全局

## 6. 静默条件
- 若脚本输出为空或仅含空白字符，静默（NO_REPLY）

## 7. 幂等与副作用
- 跑 2 次：无副作用，读取型操作
- 执行到一半崩溃：OpenClaw 重试

## 8. 成本预算
- session: `isolated`
- model: 默认
- thinking: `off`（纯脚本执行+结构化输出）
- tools 白名单: `exec`（调用 Python 脚本）
- lightContext: 是
