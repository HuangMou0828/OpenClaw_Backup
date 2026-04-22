# Openclaw 散落文件统一版本管理（Symlink 方案）

> 目标：把散落在本机各处的 `cron`、`mcp` 配置文件，以及新增的 `docs` 文档，集中到**一个 git 仓库**里管理。
>
> 核心思路：
> - **真实文件搬到仓库里**，原位置留一个软链接（symlink）指向仓库 → 程序读取的还是原路径，完全无感。
> - **纯文档（docs）没有"原位置"，直接在仓库里新建即可，不需要 symlink。**

---

## 一、最终结构预览

仓库目录（建议放在 `~/openclaw-config`）：

```
~/openclaw-config/
├── README.md
├── .gitignore
├── cron/                  # 真实文件在这里
│   └── openclaw.cron
├── mcp/
│   └── server.json
├── docs/                  # 纯文档：直接新建，不用 symlink
│   └── runbook.md
└── scripts/
    ├── adopt.sh           # 把散落文件「收编」进仓库
    └── link.sh            # 在新机器上把仓库文件链回原位置
```

原本散落的位置 → 收编后变成软链接：

```
/etc/cron.d/openclaw         →  symlink →  ~/openclaw-config/cron/openclaw.cron
~/.config/mcp/server.json    →  symlink →  ~/openclaw-config/mcp/server.json
（docs 没有原位置，无需 symlink）
```

---

## 二、两类文件的处理方式（重点）

| 类型 | 例子 | 处理方式 |
|---|---|---|
| **有原位置的配置文件** | cron 文件、mcp config | `adopt.sh` 收编：mv 真实文件进仓库 + 原位置建 symlink |
| **纯文档（无原位置）** | runbook.md、笔记 | **直接在 `docs/` 里新建文件**，不需要任何 symlink |

只有第一类需要折腾 symlink，第二类就是普通仓库用法。

---

## 三、初始化仓库（一次性，3 分钟）

```bash
mkdir -p ~/openclaw-config/{cron,mcp,docs,scripts}
cd ~/openclaw-config

git init -b main
printf "*.log\n.DS_Store\n.env\n" > .gitignore
cat > README.md <<'EOF'
# Openclaw Config

散落文件统一管理仓库。

- `cron/` — cron 配置（symlink 到原位置）
- `mcp/`  — mcp 配置（symlink 到原位置）
- `docs/` — 纯文档，直接编辑

新机器恢复：克隆后执行 `./scripts/link.sh`
EOF

git add .
git commit -m "init: scaffold cron/mcp/docs"
```

可选：推到 GitHub（**含敏感信息务必用私有仓库**）

```bash
git remote add origin git@github.com:<you>/openclaw-config.git
git push -u origin main
```

---

## 四、核心脚本（两个，复制即用）

### 1. `scripts/adopt.sh` —— 把散落文件收编进仓库

```bash
#!/usr/bin/env bash
# 用法: ./scripts/adopt.sh <原文件绝对路径> <cron|mcp>
# 示例: sudo ./scripts/adopt.sh /etc/cron.d/openclaw cron
#       ./scripts/adopt.sh ~/.config/mcp/server.json mcp

set -euo pipefail

SRC="${1:-}"
CATEGORY="${2:-}"
[[ -z "$SRC" || -z "$CATEGORY" ]] && { echo "用法: $0 <原路径> <cron|mcp>"; exit 1; }

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
DEST_DIR="$REPO_DIR/$CATEGORY"
FILENAME="$(basename "$SRC")"
DEST="$DEST_DIR/$FILENAME"

[[ -e "$SRC" ]] || { echo "源文件不存在: $SRC"; exit 1; }
[[ -d "$DEST_DIR" ]] || { echo "无效分类目录: $DEST_DIR"; exit 1; }
[[ -L "$SRC" ]] && { echo "$SRC 已经是软链接，跳过"; exit 0; }
[[ -e "$DEST" ]] && { echo "仓库内已存在同名文件: $DEST，请手动处理"; exit 1; }

mv "$SRC" "$DEST"
ln -s "$DEST" "$SRC"
echo "✓ 已收编: $SRC -> $DEST"
```

### 2. `scripts/link.sh` —— 新机器上把仓库文件链回原位置

维护一份 **原始路径清单**，新机器克隆仓库后跑一遍即可还原所有 symlink。

```bash
#!/usr/bin/env bash
# 用法: ./scripts/link.sh

set -euo pipefail
REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"

# ===== 在这里维护映射：仓库内相对路径::本机绝对路径 =====
declare -a LINKS=(
  "cron/openclaw.cron::/etc/cron.d/openclaw"
  "mcp/server.json::$HOME/.config/mcp/server.json"
)
# =========================================================

for entry in "${LINKS[@]}"; do
  SRC="$REPO_DIR/${entry%%::*}"
  DEST="${entry##*::}"
  mkdir -p "$(dirname "$DEST")"
  if [[ -e "$DEST" && ! -L "$DEST" ]]; then
    echo "⚠ 跳过（目标已存在且非软链接）: $DEST"
    continue
  fi
  ln -sfn "$SRC" "$DEST"
  echo "✓ 链接: $DEST -> $SRC"
done
```

授权：

```bash
chmod +x ~/openclaw-config/scripts/*.sh
```

---

## 五、把现有散落文件迁进来

对每个 cron / mcp 文件，重复这两步；docs 直接跳过 symlink。

```bash
cd ~/openclaw-config

# 1) 收编 cron / mcp（自动 mv + 建 symlink）
sudo ./scripts/adopt.sh /etc/cron.d/openclaw cron
./scripts/adopt.sh ~/.config/mcp/server.json mcp

# 2) docs：直接在仓库里新建/编辑，不需要 adopt
vim docs/runbook.md

# 3) 顺手把 cron/mcp 的路径登记到 link.sh 的 LINKS 数组里（为了换机器能恢复）

# 4) 提交
git add .
git commit -m "adopt: initial cron/mcp/docs"
git push
```

> 💡 验证：`ls -l /etc/cron.d/openclaw` 应该显示 `-> /Users/hm/openclaw-config/cron/openclaw.cron`，cron 服务读取行为不变。

---

## 六、日常维护（极简）

| 场景 | 操作 |
|---|---|
| 改了 cron / mcp 配置 | **直接编辑 `~/openclaw-config/<分类>/xxx`**（或编辑原路径，反正是同一个文件），然后 `git add . && git commit -m "update xxx" && git push` |
| 加一篇文档 | `vim ~/openclaw-config/docs/xxx.md` → 提交 |
| 新增散落配置文件要纳管 | `./scripts/adopt.sh <路径> <cron\|mcp>` → 在 `link.sh` 登记 → 提交 |
| 换电脑 | `git clone … ~/openclaw-config && cd ~/openclaw-config && ./scripts/link.sh` |
| 想看哪些文件被管 | `find ~/openclaw-config -type f -not -path '*/\.git/*'` |
| 误删原位置 symlink | `./scripts/link.sh` 重建即可 |

建议把常用操作做成别名，写到 `~/.zshrc`：

```bash
alias oc='cd ~/openclaw-config'
alias ocs='cd ~/openclaw-config && git status'
alias ocp='cd ~/openclaw-config && git add -A && git commit -m "update" && git push'
```

---

## 七、几个常见坑

1. **权限文件**：`/etc/cron.d/` 下的文件需要 root，`adopt.sh` 前面加 `sudo`。cron 要求文件属主为 root，软链接本身权限不重要，但**指向的真实文件**最好保持 root 可读。
2. **用绝对路径建 symlink**：脚本里已经是绝对路径（`ln -s "$DEST" "$SRC"`），跨目录最稳。
3. **敏感信息**：含 token / 密钥的文件务必用**私有仓库**，或在 `.gitignore` 里排除。
4. **某些程序不跟随 symlink**：极少见。如果遇到，对那个文件改用 bare 方案或直接 `cp` + 手工同步。
5. **macOS Spotlight / Time Machine**：symlink 是透明的，不影响。

---

## 八、给 openclaw 的执行清单（直接抄）

- [ ] 执行「三、初始化仓库」全部命令
- [ ] 创建 `scripts/adopt.sh` 和 `scripts/link.sh`，内容见「四」
- [ ] `chmod +x ~/openclaw-config/scripts/*.sh`
- [ ] 让我列出当前散落的 cron / mcp 文件绝对路径，逐个执行 `adopt.sh`（`/etc` 下加 `sudo`）
- [ ] 把已收编的路径登记到 `link.sh` 的 `LINKS` 数组里
- [ ] 把现有 docs 文件 `cp` 或新建到 `~/openclaw-config/docs/`
- [ ] `git add . && git commit -m "init adopt" && git push`
- [ ] （可选）追加第六节的 zsh 别名到 `~/.zshrc`

完成后，今后维护就一条规则：**直接改仓库里的文件 → 提交**。
