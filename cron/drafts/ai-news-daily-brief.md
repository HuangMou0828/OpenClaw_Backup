# ai-news-daily-brief

## 1. 业务意图（一句话）
每天 10:00 抓取中英文 AI 新闻 RSS，生成 Discord 富媒体日报并发送到指定频道。

## 2. 触发时机
- schedule: `0 10 * * *`
- tz: `Asia/Shanghai`
- 为什么这个点：上午工作时间，用户能看到最新 AI 动态
- 允许抖动：是（默认 stagger 5min）

## 3. 数据来源
- 36氪 RSS: `https://36kr.com/feed`
- 爱范儿 RSS: `https://www.ifanr.com/feed`
- AIBase: `https://news.aibase.cn/daily`
- 量子位 RSS: `https://qbitai.com/feed`（带 User-Agent 头）
- VentureBeat: `https://venturebeat.com/feed/
- TechCrunch AI: `https://techcrunch.com/category/artificial-intelligence/feed/
- Ars Technica AI: `https://arstechnica.com/ai/feed/
- ⚠ 用 `exec` 工具调用 curl 并行抓取，RSS 解析用 python3

## 4. 输出产物
- 格式：Discord embed（通过 MCP `format_ai_news` 生成）
- 结构：头条3条 + 产业4-5条 + 模型3-4条 + 洞察2条，总计≤15条
- 每条含标题 + 摘要（100-250字）+ 链接

## 5. 交付
- mode: none（MCP 工具直接发，不走 announce）
- channel: Discord channel ID: `1495054057931538432`
- failureDestination: 继承全局

## 6. 静默条件
- 本 job 为每日日报，**不禁静默**（正常和异常都要有输出）
- 全部 RSS 源均失败时：输出「所有新闻源均获取失败，请检查网络」并结束

## 7. 幂等与副作用
- 跑 2 次：每天重复发送，用户会看到两条相同的日报
- 对策：RSS 天然不同日期内容不同，不做去重（已在生成端处理）
- 执行到一半崩溃：OpenClaw 重试，不影响已发送的消息（消息已发不可撤回）

## 8. 成本预算
- session: `isolated` — 理由：独立任务，不需要主会话上下文
- model: 默认（MiniMax-M2.7-highspeed）— 理由：需要内容理解和摘要生成
- thinking: `medium` — 理由：需要判断新闻价值、去重、摘要提炼
- tools 白名单: `exec,format_ai_news,send_discord_text` — 理由：抓取+格式化+发送三步
- lightContext: 是 — 理由：workspace 上下文对新闻聚合无意义
