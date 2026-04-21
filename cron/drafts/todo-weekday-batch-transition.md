# todo-weekday-batch-transition

## 1. 业务意图（一句话）
每个工作日 20:20 将当日待办任务批量流转到指定状态。

## 2. 触发时机
- schedule: `20 20 * * 1-5`（周一至周五 20:20）
- tz: `Asia/Shanghai`
- 为什么这个点：下班后批量处理

## 3. 数据来源
- 执行 `python3 /Users/hm/.openclaw/workspace/scripts/preformat-todo-today.py`
- 解析输出第一行：NO_TASKS 或 HAS_TASKS
- 若 HAS_TASKS：读取 /tmp/openclaw_todo_today.json

## 4. 输出产物
- 格式：纯文本流转报告
- 直接输出，不调用飞书消息工具

## 5. 交付
- mode: announce
- failureDestination: 继承全局

## 6. 静默条件
- 若 preformat 输出第一行是 NO_TASKS：输出「今日无截止待办 ✅」并静默

## 7. 幂等与副作用
- 流转操作：多次执行可能重复流转（依赖飞书 API 幂等性）
- 对策：脚本应检查任务状态，已流转则跳过

## 8. 成本预算
- session: `isolated`
- model: 默认
- thinking: `off`
- tools 白名单: `exec,feishu_task_task`（流转动作需要）
- lightContext: 是
