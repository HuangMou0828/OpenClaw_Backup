# memory-weekly-refine

## 1. 业务意图（一句话）
每周日晚上扫描过去7天的日记文件，提取重复出现的模式和重要决策，精炼到长期记忆

## 2. 触发时机
- schedule: `0 22 * * 0`
- tz: `Asia/Shanghai`
- 为什么这个点：周日晚上，一周结束时总结，不影响工作日
- 允许抖动：是（非关键时间点）

## 3. 数据来源（每一项必须有对应 MCP tool 或明确来源）
- read_file：读取过去7天的 `~/.openclaw/workspace/memory/YYYY-MM-DD.md`
- read_file：读取当前 `~/.openclaw/workspace/MEMORY.md`
- write_file：追加精炼内容到 MEMORY.md
- ⚠ 不需要外部 API，纯本地文件操作

## 4. 输出产物
- 格式：markdown 追加到 MEMORY.md
- 关键字段：
  - 重复出现的错误模式（≥2次）
  - 重要决策和里程碑
  - 新发现的最佳实践
- 长度上限：≤ 500 字（避免过度膨胀）

## 5. 交付
- mode: announce
- channel + to: feishu:user:ou_3c3ad01561a915fe50731a0d71965963
- failureDestination: 继承全局

## 6. 静默条件（关键，80% 扰民问题出在这）
明确列出"不发"的情形，每条对应产出 `NO_REPLY`：
- 过去7天没有任何日记文件时
- 扫描后未发现任何值得精炼的内容（无重复模式、无重要决策）
- MEMORY.md 已经包含所有提取的内容（去重）

## 7. 幂等与副作用
- 跑 2 次会怎样：可能重复追加相同内容到 MEMORY.md
- 对策：
  - 每次追加前检查 MEMORY.md 是否已包含相同内容
  - 使用日期标记（`## Weekly Refine YYYY-MM-DD`）避免重复
  - 如果本周已经 refine 过，输出 NO_REPLY
- 如果执行到一半崩溃：下次 retry 会重新扫描，无数据丢失风险

## 8. 成本预算
- 预估 tokens/run：~8K tokens（读7个日记文件 + MEMORY.md + 分析 + 写入）
- 选型：
  - session: isolated — 理由：无需跨次记忆，每次独立分析
  - model: sonnet — 理由：需要理解和提取模式，mini 不够
  - thinking: medium — 理由：需要识别重复模式和重要性判断
  - tools 白名单: [read, write] — 最小集，只需文件读写
  - lightContext: 否 — 需要访问 workspace 文件
