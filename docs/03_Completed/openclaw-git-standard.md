# OpenClaw Git 操作标准

> 适用：本人所有 git 仓库（dotfiles/config/MCP/笔记），以 `~/openclaw-config` 为基准。
>
> 原则：**原子提交、规范 message、git log 即 changelog、不写无意义文档**。

---

## 1. 提交规范

### 1.1 Commit message 格式

```text
<type>(<scope>): <subject>

[可选 body]
```

- `<type>`：`feat` / `fix` / `chore` / `docs` / `refactor` / `style` / `test`
- `<scope>`：顶层目录或子模块名（`cron` / `mcp` / `docs` / `scripts` / `mcp/messaging-sender` 等），不确定就省略
- `<subject>`：命令式现在时、英文小写起手、句末无句号、≤ 60 字符

**Type 用法对照**

| type | 何时用 | 例 |
|---|---|---|
| `feat` | 新增功能/文件/集成 | `feat(mcp): import discord-beautifier` |
| `fix` | 修 bug 或错误配置 | `fix(cron): correct ai-news cron timezone` |
| `chore` | 构建/配置/依赖等非功能改动 | `chore: extend .gitignore for python artifacts` |
| `docs` | 仅文档 | `docs: add cron migration guide` |
| `refactor` | 不改行为的重构 | `refactor(scripts): split link.sh into helpers` |
| `style` | 仅格式（空格/缩进）| `style: format jobs.json` |
| `test` | 仅测试 | `test(mcp): add messaging-sender smoke test` |

### 1.2 何时写 body

| 写 body | 不写 body |
|---|---|
| 解释**为什么**（不显然的取舍）| subject 已自描述 |
| 破坏性改动（注明 BREAKING） | 单纯的 docs/chore |
| fix 类需描述根因 + 解法 | 重命名/移动文件 |

body 与 subject 之间必须空一行。每行 ≤ 72 字符。

---

## 2. 原子提交

**一个 commit = 一个完整意图**，能被独立 revert。

| 反例 | 正确做法 |
|---|---|
| 修 bug + 顺手 refactor 无关代码 | 拆两个 commit |
| 加 feature + 改 gitignore + 改 docs 一起 | 拆三个 commit |
| 引入新模块 + scrub 模块内 secret 一起 | scrub 单独成 commit |

**当一次 working tree 改动包含多个意图时**：

```bash
git add <文件>           # 只 stage 一个意图相关的文件
git add -p <文件>        # 同一文件内拆 hunk
git commit -m "..."
# 重复，把剩下的拆出来
```

---

## 3. 日常工作流

### 3.1 标准流

```bash
git status                # 看清动了什么
git diff                  # 看具体内容
git add <path>            # 显式选文件，避免 -A
git diff --cached         # 复核 staged 内容
git commit -m "<type>(<scope>): <subject>"
git push                  # main 直推
```

### 3.2 禁用的快捷写法

```bash
# ❌ 这条会让所有改动塞一个 commit + 用空洞 message
alias ocp='git add -A && git commit -m "update" && git push'

# ✅ 推荐改造：只做 push（前面手动 status/add/commit）
alias ocp='git push'
alias ocs='git status'
alias ocd='git diff'
```

### 3.3 临时收起改动

```bash
git stash push -m "wip: <说明>"   # 写说明，半年后还认识
git stash list
git stash pop
```

---

## 4. Secret 防泄漏（三道闸 + 兜底）

### 4.1 三道闸

1. **gitignore**：`config.json` / `.env` / `*.pem` / `*.key` / `secrets/` 默认忽略
2. **提交前自查**：

   ```bash
   git diff --cached | grep -iE "(token|secret|password|api_key|bearer)" && echo "⚠️ 复核"
   ```

3. **GitHub Push Protection**：自动扫描，但只是兜底，不能依赖

### 4.2 万一漏了

| 状态 | 处理 |
|---|---|
| 仅 commit、未 push | `git reset --mixed <good-commit>` 重做，不用 amend |
| 已 push 到 remote | **立刻去对应平台 revoke 并重发** token；改 `git filter-repo` 清史只是补救，token 已被记录 |

**绝对不做的事**：

- ❌ 用 `git push --force` 试图"覆盖泄漏的历史"——token 已经在第三方扫描器里了
- ❌ 把 secret commit 后用 `--amend` 解决——commit hash 变了，但旧对象还在 reflog

### 4.3 secret 该放哪

| 类型 | 推荐位置 |
|---|---|
| 真 secret（token/password） | macOS Keychain → `~/.zshrc` 启动加载 |
| 派生配置文件（如 `config.json`） | gitignored，从 env 用 render 脚本生成 |
| 公开标识（app_id / channel_id） | 直接进 zshrc 或代码（非 secret） |

详见 `openclaw-dotfiles-guide.md`。

---

## 5. 分支与发布

### 5.1 分支策略

- **main 直推**：personal monorepo 不需要 PR
- **分支只用于实验**：`exp/<topic>`，跑通就 merge 回 main 然后删

### 5.2 版本里程碑

需要标记节点时用 **annotated tag**，不写 CHANGELOG.md：

```bash
git tag -a v0.4 -m "secrets to keychain, 4-service connectivity verified"
git push --tags
```

GitHub Release 页面会自动从 tag 之间的 commit 生成 changelog——这就是为什么 commit message 必须规范。

### 5.3 不要写 CHANGELOG.md

理由：

- `git log --oneline` 已经是 changelog
- `git log v0.3..v0.4 --oneline` 是 release notes
- 单独维护 CHANGELOG 总会忘记同步，反而误导

---

## 6. README 分层规范

| 层级 | 内容（必有） | 不写 |
|---|---|---|
| **根 README** | 一句话定位 / 目录地图 / Onboarding / Secrets 总览 / 子模块链接 | 子模块细节、changelog |
| **子目录 README** | 这部分的工作流、约定、命令、陷阱 | 重复 root 内容 |

**不要把 changelog 塞进 README**——那是给"第一次看见这个项目的人"读的，不是流水账。

参考样板：`cron/README.md`（工作流型）。

---

## 7. 紧急回滚

| 场景 | 命令 |
|---|---|
| 撤销最后一个 commit，保留改动 | `git reset --soft HEAD^` |
| 撤销最后一个 commit，丢弃改动 | `git reset --hard HEAD^` |
| 已 push 想公开撤销 | `git revert <hash>` (生成反向 commit) |
| 找回误删的 commit | `git reflog` 找 hash → `git reset --hard <hash>` |
| 单文件回到上一个版本 | `git checkout HEAD~1 -- <file>` |

`reset` 改写历史只能用于**未 push** 的 commit。已 push 的一律用 `revert`。

---

## 8. Cheatsheet

```bash
# 看
git status -s                              # 简洁状态
git log --oneline -10                      # 近 10 条
git log --all --graph --oneline -20        # 图形化
git diff                                   # 未 stage 改动
git diff --cached                          # 已 stage 改动
git diff <branch1>..<branch2>              # 分支差异

# 选择性 stage
git add <path>
git add -p <path>                          # 拆 hunk

# 提交
git commit -m "<type>(<scope>): <subject>"
git commit                                 # 打开编辑器写 body

# 同步
git fetch
git pull --rebase                          # 避免无意义的 merge commit
git push

# 修正最近一次（仅未 push）
git commit --amend                         # 改 message 或追加文件

# 查找
git log --all --grep="<关键词>"            # 找含关键词的 commit
git log -S "<代码片段>"                    # 找引入/删除该代码的 commit
git blame <file>                           # 行级溯源

# 标签
git tag -a v0.x -m "..."
git push --tags
```

---

## 9. 落地动作（一次性）

> 把这份标准生效到 `~/openclaw-config`，做完一次即可：

1. 改 `~/.zshrc` 中的 `ocp` alias：去掉 `git add -A && git commit -m "update"`，只保留 `git push`
2. 在根 `README.md` 顶部加一行链接到本文档
3. 此后每次 commit 自查：是否符合 §1 message 格式 + §2 原子性
4. 每达到一个稳定节点：`git tag -a v0.x -m "..." && git push --tags`

---

## 10. 一行总结

> **看清楚（status/diff）→ 选对了（add 显式）→ 说人话（type+scope+subject）→ 别乱推（main 直推但每条都站得住）。**
