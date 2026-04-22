# OpenClaw Cron 制造标准

> 目标：造出一条**合格、可预期、不扰民**的 cron job。
>
> 适用时机：新建一条 cron、或者重构一条老 cron 之前。
>
> 用法：按本文件从上到下走完一遍，再 `openclaw cron add`。全流程大约 15~30 分钟/job。

---

## 第 0 步 — 先问三个问题（过不了就别做 cron）

在动手之前，如实回答：

1. **这件事一定要 LLM 做吗？**
   纯规则能解决的（阈值判断、格式转换、固定查询）→ 写脚本，别用 cron + LLM。
2. **这件事一定要定时吗？**
   事件驱动更合适的（Gmail 新邮件、Webhook、PR merged）→ 走 `hooks.mappings`，不是 cron。
3. **失败了谁会看？**
   没有明确 oncall → 先配好 `failureDestination` 再造。不然就是定时制造"无人管的幻觉输出"。

⚠ 三问有任一个答"否"或"不知道"，STOP。

---

## 第 1 步 — 填设计画布（不写完不准写 message）

新建 `cron/drafts/<name>.md`，把下面 8 项填掉。**这份画布后续也留在仓库里**，就是这个 job 的 README。

```markdown
# <name>

## 1. 业务意图（一句话）
<例：每个工作日早上总结昨天 merged 的 PR，发给研发群>

## 2. 触发时机
- schedule: `0 9 * * 1-5`
- tz: `Asia/Shanghai`
- 为什么这个点：<例：对齐晨会前 15 分钟>
- 允许抖动：是 / 否（top-of-hour 默认 stagger 5min）

## 3. 数据来源（每一项必须有对应 MCP tool 或明确来源）
- github.list_merged_prs(repo, since=1d)
- 其他：<列出>
- ⚠ 禁止在 prompt 里写"请调 https://..."——必须是 tool

## 4. 输出产物
- 格式：markdown 卡片 / 纯文本 / 结构化 JSON
- 关键字段：<列出>
- 长度上限：<例：≤ 800 字>

## 5. 交付
- mode: announce / webhook / none
- channel + to: <具体值或 vars 引用>
- failureDestination: 继承全局 / 覆盖为 <xxx>

## 6. 静默条件（关键，80% 扰民问题出在这）
明确列出"不发"的情形，每条对应产出 `NO_REPLY`：
- 数据为空时
- 命中阈值 X 以下时
- <其他>

## 7. 幂等与副作用
- 跑 2 次会怎样：<例：重复发消息，用户会烦>
- 对策：<例：用 sessionTarget=custom 记录上次 last_seen_id；或加 idempotency 工具>
- 如果执行到一半崩溃：<例：下次 retry 无副作用>

## 8. 成本预算
- 预估 tokens/run：<数量级>
- 选型：
  - session: isolated / main / session:xxx  — 理由：<>
  - model: <> — 理由：<>
  - thinking: off / low / medium / high — 理由：<>
  - tools 白名单: [...] — 最小集
  - lightContext: 是 / 否
```

**卡点自检**：如果第 3、6 项写不具体，说明你还没想清楚，不要进下一步。

---

## 第 2 步 — 按 4 段式骨架写 message

OpenClaw 的 `payload.message` 是唯一和 LLM 对话的地方。**固定 4 段，顺序不变**：

```
[意图] 一句话说清做什么，禁止多意图。

[数据] 明确列工具调用及参数。格式：
- 调用 <tool_name>({...})
- 若需串联：先 A，再基于 A 的结果调 B

[输出] 明确格式和目的地：
- 用 <output_tool> 发送
- 格式：<markdown / JSON schema>
- 长度 ≤ N 字

[静默] 显式说 NO_REPLY 触发条件：
- 当 <条件> 时，只回复单行 "NO_REPLY" 并结束，不调用任何发送工具
```

**好例子：**

```
[意图] 汇报昨天 org/repo 新 merged 的 PR。

[数据] 调用 github.list_merged_prs({repo:"org/repo", since:"1d"})。

[输出] 用 lark.send_card 发到 {{channels.dev}}。
格式：markdown 卡片，每个 PR 一行「#号 标题（作者）」，底部总数加粗。长度 ≤ 500 字。

[静默] 当 github.list_merged_prs 返回空数组时，回复单行 "NO_REPLY" 并结束。
```

**反例**（不要这么写）：

```
❌ 每天早上帮我看一下仓库有啥新 PR，整理一下发给大家，如果没有也可以说一声。
```
问题：没有具体工具、没有格式、"没有也可以说一声" 会制造扰民消息。

---

## 第 3 步 — 选 session / model / thinking / tools（最小够用原则）

| 决策 | 默认选择 | 何时偏离 |
|------|---------|---------|
| session | `isolated` | 需要跨次记忆（上次看到哪条）→ `session:<name>` |
| model | 项目里最便宜且够用的（如 gpt-5.4-mini） | 真正需要强推理才上 opus/o3 |
| thinking | `off` 或 `low` | 多步工具编排/分支判断才上 `medium` |
| tools | 白名单列出用到的 | 不写 `--tools` = 全部工具 = 浪费注意力 + 攻击面大 |
| lightContext | 默认开（`--light-context`） | 需要 workspace 上下文才关 |

**经验数**：每日高频 cron（>1 次/天），thinking 默认必须 `off` 或 `low`。`medium` 以上要写明理由。

### 3.1 session 三种模式该怎么选

| 模式 | 适用 | 风险 |
|------|------|------|
| `isolated`（**默认**） | 90% 的日常 job。每次冷启动，结果可重现 | 无跨次记忆；需要"背景"时靠 prompt + tool 默认参数解决 |
| `main` | 只在需要打断主会话（提醒、系统事件）时用 | 污染主上下文；非提醒类不要用 |
| `session:<name>` | 明确需要跨次连续性（"上次看到哪条"、"基于上周基线" ） | 上下文漂移、token 增长、调试困难 |

### 3.2 custom session 的正确模式：**last-run marker，别靠 session 记忆**

反模式：`--session "session:daily-report" --message "按之前的风格继续汇报"` —— 靠 session 里残留的对话"记得"风格。短期能跑，三周后风格漂移且无法复现。

正确模式：**状态外移到工具，session 只做薄记忆**。

```
[数据]
- 调用 state.get({key:"pr-report:last_seen_pr_id"}) 拿上次处理到的游标
- 调用 github.list_merged_prs({repo, since_pr_id: <上一步结果>})
- 处理完后调 state.set({key:"pr-report:last_seen_pr_id", value:<最新 id>})
```

其中 `state.get/set` 是你侧一个极简的 KV MCP tool（一个文件、一个 redis key 都行）。这样：
- 换模型 / 换 session 都不影响业务连续性
- 状态可 dump / 可重置 / 可 review
- 冷启动也能跑（首次 `get` 为空时按全量处理）

**除非**你明确在做 multi-turn 对话式任务（极少见），否则别让业务状态存在 session 里。

### 3.3 delivery 字段 ↔ CLI flag 对照

OpenClaw 的 delivery 概念在 JSON 和 CLI 里字段名不一致，写 cron 时容易懵：

| JSON 字段（`delivery.mode`） | CLI flag | 行为 |
|---|---|---|
| `"announce"` | `--announce --channel <ch> --to <to>` | agent 没发消息时，runner 兜底把最终输出发到指定渠道 |
| `"webhook"` | （通过 job 配置 JSON 设置 webhook URL） | POST finished event 到 URL |
| `"none"` | `--deliver none`（部分版本 `--no-deliver`） | runner 不兜底；agent 可自行调 `message` 工具发 |

**易错点**：
- `--deliver none` **不等于** "不发消息"。如果 agent 自己调了 `lark_send_card`，照样会发。想完全静默就让 prompt 输出 `NO_REPLY`。
- `--announce` 不指定 `--channel` / `--to` 时，OpenClaw 会尝试用"当前/上次"的 chat 路由，可能发到你不想发的地方。**永远显式指定 channel+to**。
- `failureDestination` 只在 `sessionTarget="isolated"` 或主 delivery 是 `webhook` 时生效（见文档）。

---

## 第 4 步 — 命名与调度约定

### 命名：`<domain>-<intent>-<cadence>`

```
pr-daily-report          ✅
sentry-hourly-digest     ✅
standup-weekly-summary   ✅
check-stuff              ❌  太泛
morning-thing            ❌  无 domain
```

### 调度：

- **必须显式写 `--tz`**，别依赖 gateway 默认
- **整点高峰**（`0 9 * * *`）利用默认 5min stagger，别加 `--exact` 除非业务必须
- **日/周同时出现就分开**：`0 9 * * 1-5`（工作日）+ `0 10 * * 6,0`（周末），别写一条靠 prompt 判断
- **文档坑点**：`0 9 15 * 1` 会被解析为"每月 15 号 OR 每周一"，不是"15 号且周一"。要"且"关系用 `0 9 15 * +1`

---

## 第 5 步 — 上线前冒烟（分级，别一刀切）

> 冒烟做重了会被绕过，做轻了会漏扰民。按下表分级，**Tier A 每条必做，Tier B 按场景加**。

| 场景 | 必做层级 | 预计耗时 |
|------|---------|---------|
| 新建一条 cron | **Tier A** | 2~3 min |
| 重构老 cron（改 message / 换工具 / 换 agent） | **Tier A + B** | 8~12 min |
| 高频 cron（≥ 1 次/小时）、对外群发类 | **Tier A + B** 且至少跑一次真实触发 | +5 min 观察 |
| 只改文案一个字 | 直接 `openclaw cron run <id>` 实跑一次即可 | 1 min |

**Tier A —— 不可跳过**：静默路径 + 正常路径。这两个挡住 80% 的扰民。
**Tier B —— 该做**：失败告警链路 + 成本核对。这两个挡住账单爆炸和静默故障。

---

### Tier A.1 —— 空数据路径（验证静默）

**Action**：临时改 message，让数据工具返回空（或用 mock 参数）。

**Verify**
```bash
openclaw cron add --name "smoke-<name>-silent" --at "30s" --session isolated \
  --message "<改过的 message，强制空数据>" --deliver none --delete-after-run
sleep 60
openclaw cron runs --limit 1
# 确认：run 成功完成，最终输出为 "NO_REPLY" 或被 OpenClaw 识别为静默
```

**通过标准**：无任何渠道发送。

### Tier A.2 —— 正常路径（验证格式）

**Action**
```bash
openclaw cron add --name "smoke-<name>-normal" --at "30s" --session isolated \
  --message "<正式 message>" \
  --announce --channel <测试渠道> --to <个人 chat_id，不发群> \
  --delete-after-run
```

**Verify**：你个人 chat 收到产物，格式与画布第 4 项一致，长度在预算内。

### Tier B.1 —— 失败路径（验证告警）

**Action**：改 message 让它调一个不存在的工具。

```bash
openclaw cron add --name "smoke-<name>-fail" --at "30s" --session isolated \
  --message "请调用 xxx_fake_tool 并等待结果" --delete-after-run
```

**Verify**：`failureDestination` 指定的渠道收到失败通知。

### Tier B.2 —— 成本核对（验证预算）

**Action**：正式 cron 跑一次，查 runs：
```bash
openclaw cron runs --id <id> --limit 1
```

**Verify**：token 消耗和画布第 8 项预估同一量级；否则先调（砍 thinking、砍工具、砍 lightContext、砍 message 啰嗦段）再上线。

**本场景要求的层级全过** → 删除 smoke 产物 → 正式 `openclaw cron add`。

**快捷片段**（Tier A 常用，复制改名即可）：
```bash
# A.1 静默
openclaw cron add --name "smk-$N-silent" --at "30s" --session isolated \
  --message "$MSG_EMPTY_DATA" --deliver none --delete-after-run

# A.2 正常（发给个人）
openclaw cron add --name "smk-$N-ok" --at "30s" --session isolated \
  --message "$MSG" --announce --channel lark --to "$MY_CHAT" --delete-after-run
```

---

## 第 6 步 — 正式创建并登记

**Action**
```bash
openclaw cron add \
  --name "<name>" \
  --cron "<expr>" --tz "<tz>" \
  --session isolated \
  --agent <agent-if-applicable> \
  --message "<final message>" \
  --model <model> --thinking <level> \
  --tools <comma-list> \
  --announce --channel <ch> --to <to>

openclaw cron list --json > cron/jobs.json
git add cron/jobs.json cron/drafts/<name>.md
git commit -m "feat(cron): add <name>"
```

**完成标志**：
- `cron/drafts/<name>.md` 画布归档
- `cron/jobs.json` 同步
- git 一条原子提交

---

## 反模式清单（发现一条重构一条）

| 反模式 | 症状 | 修正 |
|--------|------|------|
| 单 job 多 intent | message 里有"另外还要..."/"顺便..." | 拆成两条 cron |
| 自然语言调 API | "请调 https://api.github.com/..." | 包成 MCP tool，prompt 只写工具名 |
| 无静默条件 | 每天都发、哪怕无数据 | 显式写 NO_REPLY 触发条件 |
| 奢侈 thinking | 日常摘要用 `thinking: high` | 改成 `low` 或 `off`；省下的钱给真需要的 job |
| prompt 里重复 agent 内容 | 用了 `--agent reporter` 但 message 又写"输出要用 markdown 卡片..." | 删掉 message 里和 agent system 重复的段落 |
| 没 `--tz` | 跨时区切换后触发点漂移 | 所有 cron 显式 tz |
| 全量 tools | 不写 `--tools`，默认放开 | 白名单最小集 |
| 交付目标硬编码群 ID | 换群要改 prompt | 用 agent / vars / config 抽离 |
| main session 滥用 | 非提醒类也走 main，污染主会话 | 默认 isolated；main 需画布里写明理由 |
| 把 retry 交给 LLM | prompt 里"如果失败就重试三次" | 失败交给 OpenClaw `cron.retry` 配置 |

---

## 工具白名单怎么写（自建 tools/INDEX.md）

标准里说 "白名单列出用到的"，但你真正要回答的是：**你们 MCP server 里有哪些工具？哪些能组合出哪些能力？** 这份速查没人替你攒，值得花一小时建一次，长期回报极高。

### 做法

**Action**
```bash
mkdir -p tools
# 1. 把本地 gateway 挂的 MCP server 全量工具导出（命令依版本）
openclaw tools list --json > tools/_raw.json 2>/dev/null \
  || echo "如果没有这个子命令，去 ~/.openclaw/config.json5 读 mcpServers 逐个 list"

# 2. 用 jq 过一遍，每个工具留下 name + description + 关键参数
jq '[.[] | {name, desc: .description, args: .inputSchema.properties | keys?}]' \
   tools/_raw.json > tools/INDEX.json
```

然后人工写 `tools/INDEX.md`：按**能力领域**分组，不是按 MCP server 分组。

```markdown
# Tools Index

## 发送消息
- lark_send_text(chat_id, text)    — 纯文本，<= 2000 字
- lark_send_card(chat_id, card)    — 卡片，支持 markdown
- ⚠ 不要用 exec 来 curl 飞书 webhook，走 lark_send_* 会带重试和格式校验

## 取数据（只读）
- github.list_merged_prs(repo, since, limit)
- sentry.top_errors(project, env, limit)
- db.query(sql)                    — ⚠ 只允许 SELECT；修改走下面的 exec

## 执行类（有副作用，白名单要最窄）
- exec(cmd)                        — 运行 shell；任何 cron 用到都要 review
- write_file(path, content)        — 写本地文件
- state.get / state.set            — KV 状态（last-run marker 用）

## 安全边界
- read 家族 → 默认可用
- exec / write_file → 只在明确需要的 cron 里白名单放开
- 跨租户/跨环境数据 → 拒绝默认放开
```

### 怎么用到 cron 里

写新 cron 前，先去 `tools/INDEX.md` 找"我要的能力已经有工具了吗？"：
- **有** → `--tools <name1>,<name2>` 只放它们
- **无且通用** → 新建 MCP tool（独立工程）
- **无且一次性** → 允许 `exec` 但写明"仅限本 job，三个月后重新评估"

**INDEX.md 每季度 review 一次**，新增工具登记、废弃工具打 ⚠️ deprecated。这份文件是新人上手 cron 的第一读物。

---

## 画布速查（复制粘贴即可）

```markdown
# <name>
1. 意图：
2. schedule / tz：
3. 数据工具：
4. 输出格式 + 长度上限：
5. 交付：
6. 静默条件：
7. 幂等：
8. 成本：session / model / thinking / tools / lightContext
```

---

## 附：和管理指南的关系

- **本文件**（制造标准）：**每次造一条** cron 时遵循
- `openclaw-cron-migration-guide.md`（管理指南）：cron 群体的**存量**怎么放 git、怎么 diff、怎么回滚

两者独立，不互相依赖。存量没做管理的，也可以先按本文件开始**保证新建的都是合格品**，存量慢慢迭代。
