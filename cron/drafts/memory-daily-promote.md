# memory-daily-promote

## 1. 业务意图（一句话）
每天 03:00 把 .learnings 下 pending 条目晋升到 MEMORY.md，保持长期记忆。

## 2. 触发时机
- schedule: `0 3 * * *`
- tz: `Asia/Shanghai`
- 为什么这个点：凌晨 3 点，所有日间工作已完成，不干扰主会话
- 允许抖动：是（默认 stagger 5min）

## 3. 数据来源
- 读取 `~/.openclaw/workspace/.learnings/ERRORS.md`
- 读取 `~/.openclaw/workspace/.learnings/LEARNINGS.md`
- 读取 `~/.openclaw/workspace/.learnings/FEATURES.md`
- 读取 `~/.openclaw/workspace/MEMORY.md`（检查已 promote 条目，避免重复）
- ⚠ 全部是本地文件读取，用 `read` 工具，不用 exec

## 4. 输出产物
- 格式：文本，直接追加写入 MEMORY.md
- 关键字段：promote 结果统计（promoted N 条、archived N 条、degraded N 条）
- 长度上限：≤ 500 字

## 5. 交付
- mode: none（直接写文件，不发消息）
- failureDestination: 继承全局（失败告警 → 黄谋飞书）

## 6. 静默条件
- 当三个 .learnings 文件均无 pending 条目时 → NO_REPLY
- 当距上次成功执行不足 4 小时 → NO_REPLY（调用 state check）

## 7. 幂等与副作用
- 跑 2 次：可能重复 promote 同一条目 → **已promote 条目不重复 promote（去重）**
- 执行到一半崩溃：MEMORY.md 可能写入不完整的 promote 结果 → 下次运行前检查格式完整性

## 8. 成本预算
- session: `main` — 理由：需要写 MEMORY.md，main session 有 workspace 写权限
- model: 默认（MiniMax-M2.7-highspeed）— 理由：判断 promote 标准需要 LLM 推理
- thinking: `medium` — 理由：需要判断 confidence level、是否符合 promote 标准
- tools 白名单: `read,memory_search,memory_get` — 理由：只读判断，最后写用 exec
- lightContext: 否 — 理由：需要完整 workspace 上下文判断内容质量
