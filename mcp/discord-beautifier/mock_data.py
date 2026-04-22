"""
固定测试数据 — 用于反复调试 Discord 渲染样式，不消耗真实 API token
每次调整后重新运行 test_loop.py 即可
"""

# ─────────────────────────────────────────────
# 1. AI 每日热点简报
# ─────────────────────────────────────────────
AI_NEWS_MOCK = """## 🔥 本日最重要的3条

### 1️⃣ 智元机器人发布六大AI模型，宣布"具身智能部署元年"开启

4月17日，由彭志辉（稚晖君）与邓泰华联合创立的智元机器人在合作伙伴大会上，一口气推出六大AI基座模型（覆盖运动/交互/作业三大智能）、七大生产力解决方案，并首次公开 AIMA 全栈生态技术体系。智元同步宣布已量产下线机器人一万台，目标2026年成为"部署态元年"，推动机器人从"展品"变为可自主承担工业与商业任务的"商品"。数据飞轮是行业最大瓶颈——全球高质量具身数据合计不足50万小时，智元因此选择走开源开放路线。

📍 https://36kr.com/p/3770721219035649

---

### 2️⃣ OpenAI 高管连续离职、项目终止，战略重心转向企业市场

本周 Kevin Weil（GPT-4o 负责人）与 Bill Peebles（Sora 联创）相继离开 OpenAI，公司同时关闭 Sora 项目及 OpenAI For Science 团队。TechCrunch 报道称，OpenAI 正在从消费级"moonshot"项目全面收缩，转向企业 AI 变现。

📍 https://techcrunch.com/2026/04/17/kevin-weil-and-bill-peebles-exit-openai/

---

### 3️⃣ 具身智能融资大爆发：4.55亿美元单笔融资创中国纪录

量子位报道，中国具身智能领域本周诞生 4.55 亿美元单笔融资（高瓴+红杉联合押注），刷新行业纪录。同期，智元开放生态平台发布、18 家具身顶尖势力组建 RoboChallenge 联盟。

📍 https://www.qbitai.com/2026/04/402388

---

## 🏭 产业大事件

- **DeepSeek 首次启动融资：估值不低于千亿美元** — 据爱范儿援引多方信源，DeepSeek 正首次启动正式融资流程，估值不低于 1000 亿美元。作为已开源 DeepSeek-V3 等强力模型的黑马公司，其融资动向将显著影响国内大模型格局。
📍 https://www.ifanr.com/1662774

- **Cursor 正洽谈 20 亿美元新融资，估值 500 亿美元** — TechCrunch 独家报道，AI 编程工具 Cursor 正在与 a16z、Thrive 等谈判超 20 亿美元融资，估值达 500 亿美元，企业端增长迅猛。
📍 https://techcrunch.com/2026/04/17/sources-cursor-in-talks/

- **美国 40% 数据中心项目延期停工** — Financial Times 卫星图像与地面数据综合分析显示，微软、Oracle、OpenAI 等的在建数据中心中，近 40% 可能无法按期完工，劳动力短缺、电力瓶颈和本地阻力是主因。
📍 https://arstechnica.com/ai/2026/04/construction-delays-hit-40-of-us-data-centers-planned-for-2026/

- **Meta AI 支出传导至硬件：Quest 头显涨价 50-100 美元** — Meta 归咎于全球内存芯片价格飙升（由数据中心 AI 投资驱动），VR 头显涨幅约 12-20%。
📍 https://arstechnica.com/ai/2026/04/metas-ai-spending-spree-is-helping-drive-up-the-cost-of-memory-chips

---

## 🤖 模型技术

- **智元发布GO-2/GO-3系列具身模型** — GO-2模型已发布，Q3将推出GO-3，数据规模达GO-2数十至百倍，具备复杂任务规划推演能力。

- **π0.7发布，VLA架构押出机器人GPT-3时刻** — 新型VLA（视觉-语言-动作）模型架构引发行业震动，DeepMind、OpenAI、Tesla 纷纷跟进。

- **谷歌发布最强具身大脑：波士顿机器狗瞬间"人模人样"** — 谷歌具身智能团队发布新模型，使波士顿动力机器狗实现高度拟人的动作与环境交互能力。

---

## 💡 今日洞察

具身智能正以远超预期的速度成为 AI 资本新主线，数据、硬件、商业模式三重瓶颈同步突破前夜。
"""


# ─────────────────────────────────────────────
# 2. L5 健康巡检
# ─────────────────────────────────────────────
L5_HEALTH_MOCK = """## 结论
✅ 系统正常，无紧急问题。Health/Lint/Promotion-Queue 三个接口均返回 ok=true。

## Vault 健康
- lint 状态：✅ 通过（66 笔记，10 个 medium 级问题，无 high/low 问题）
- 主要问题：10 个 weak-summary 问题（均为 syntheses 目录下笔记缺少摘要）
  - syntheses/🌟-2025-01-24-agency-problem.md
  - syntheses/🌟-2025-01-24-llm-evaluation-fundamentals.md
  - syntheses/🌟-2025-01-26-mutable-declarative-distributed-systems.md
  - syntheses/🌟-2025-02-04-evaluating-a-singular-capability.md
  - syntheses/🌟-2025-02-05-capability-vs-skill-focus.md
  - syntheses/🌟-2025-02-06-reasoning-about-context-usage.md
  - syntheses/🌟-2025-03-25-llm-agent-protocols.md
  - syntheses/🌟-2025-04-10-cot-scaling-laws.md
  - syntheses/🌟-2025-04-22-the-agentic-loop.md
  - syntheses/🌟-2025-04-22-the-agentic-loop-v2.md
- 断链数：0 ✅
- 孤立笔记：0 ✅
- 重复标题：0 ✅

## 执行统计
- 总 Vault 笔记数：66
- issues_high：0
- issues_medium：10
- 断链数：0
- 孤立笔记：0
- 重复标题：0

## Promotion Queue
- 队列总数：11
- 待晋升：11
"""


# ─────────────────────────────────────────────
# 3. AI 使用日报
# ─────────────────────────────────────────────
AI_USAGE_DAILY_MOCK = """# AI 使用日报

日期：2026-04-19
置信度：medium

## 今日概览
- 会话数：12
- 消息数：67
- 平均消息数：5.6
- 主要 provider：cherry / deepseek / minimax

## 高频主题
1. 飞书日历 (8次)
2. Discord 消息发送 (6次)
3. 记忆系统维护 (5次)
4. 定时任务管理 (4次)

## 重复问题模式
- 「帮我查一下今天的日历」出现 3 次 → 建议封装为 skill
- 「发送消息到 Discord」出现 4 次 → 已有重复工具调用

## Skill 候选
1. **飞书日历快捷查询** — 触发条件：用户询问今天/明天的日历安排
   输入：日期（默认今天）→ 输出：日程列表
2. **Discord 消息转发** — 触发条件：需要把内容发到 Discord
   输入：内容和 channel → 输出：message_id

## 今日可沉淀经验
- errors 候选：Discord embed color 字段类型错误（int 而非 hex）
- patterns 候选：cron job 状态检查规范化流程

## 明日建议
1. 封装飞书日历查询为独立 skill
2. 修复 Discord color 字段传递问题
3. 优化记忆晋升触发间隔

## 需要用户确认
- 是否需要将「飞书日历查询」封装为正式 skill？
"""


# ─────────────────────────────────────────────
# 4. 记忆晋升报告
# ─────────────────────────────────────────────
MEMORY_PROMOTE_MOCK = """# 记忆晋升报告

日期：2026-04-19 08:00

## 晋升结果
- 待晋升：3 条
- 晋升：2 条
- 归档：0 条
- 降级：1 条（type: tech，超过30天未验证）

## ✅ 已晋升（2条）

**批量清理前先写 memory/ 日期文件记录，避免误删重要内容**
来源：[ERR-20260415-A]
置信度：high

**streaming 配置调试应先查文档再试，不要试错式配置**
来源：[ERR-20260414-A]
置信度：high

## ❌ 已归档（0条）

无

## 📌 已降级（1条）

- `type: tech` + 超过 30 天未验证 → confidence 降一级
  条目：npm install -g 更新时被 kill 进程会留下不完整的全局包

---
[promoted: 2026-04-19, pending: 3, promoted: 2, archived: 0, degraded: 1]
"""


# ─────────────────────────────────────────────
# 5. Inbox 导入报告
# ─────────────────────────────────────────────
INBOX_IMPORT_MOCK = {
    "message": "同步完成：新增3条,归档1条,跳过2条\n\n另有 5 条升格候选待处理：\n1. 2026-04-15 Daily Log\n2. synthesis\n3. 批量清理前先查memory记录\n4. 批量清理前应该如何避免误删关键记忆\n5. 如何避免批量清理配置文件夹时误删重要内容",
    "summary": {
        "total": 6,
        "imported": 3,
        "archived": 1,
        "skipped": 2,
        "failed": 0
    }
}
