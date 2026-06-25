# local-distill-me

把一套「`CLAUDE.local.md` 轻量索引 + `~/.claude/shared/` 共享规则」的私有指令体系，
**纯本地、安全（不联网、不上传、不入库）地蒸馏**并移植到任意项目，并为多个 git worktree
配置统一、不会漂移的私有规则。

源自一个长期多 worktree 项目的实践沉淀，抽象成可复用机制。全程只读写本机文件，
私有规则始终留在你自己机器上。

---

## 解决什么问题

直接把规则写进项目仓库的 `CLAUDE.md` 有两个痛点：

1. **私有规则不该入库**：个人调试约定、提交前红线、记忆检索习惯等，不适合提交到团队仓库。
2. **多 worktree 会漂移**：同一 repo 开多个 worktree 时，散落在各 worktree 的私有规则副本会逐渐不一致。

本 skill 用**三层 + 软链**架构解决：

| 层 | 位置 | git | 作用 |
|---|---|---|---|
| 公共 | 仓库根 `CLAUDE.md` | tracked | 团队共享的通用项目说明（本 skill 不动它） |
| 私有索引 | 各 worktree 根 `CLAUDE.local.md` | **gitignored** | 软链 → 共享目录的唯一权威索引 |
| 共享规则 | `~/.claude/shared/` | 仓库之外 | 规则正文（通用层 `_common/` + 项目层 `<slug>/`） |

规则正文放在 home 下（任何 worktree 之外），每个 worktree 的 `CLAUDE.local.md` 都**软链到同一份权威索引** → 改一处全 worktree 生效，物理上不可能漂移。`@` 前缀=每会话强制加载，裸路径=按需读取。

---

## 安装

随 **`old-bird` 插件**分发（manji 市场）。在 Claude Code 里：

```
/plugin marketplace add kaelinda/agent-marketplace   # 已加过市场可跳过
/plugin install old-bird@manji
```

装好后在**目标项目目录**的会话里输入 `/local-distill-me` 即可。详见 [QUICKSTART.md](./QUICKSTART.md)。

---

## 目录结构

```
# skill 本体（随 old-bird 插件安装，无需手动管理）
<old-bird 插件目录>/skills/local-distill-me/
├── SKILL.md                 # 触发定义 + 交互流程（给 Claude 读）
├── README.md                # 本文件（给人读）
├── QUICKSTART.md            # 5 分钟上手
├── scripts/init.sh          # 确定性引擎：脚手架 + 发现 worktree + 软链 + 配 .gitignore
├── scripts/install-hook.sh  # 可选：装 post-checkout 钩子，新建 worktree 自动软链
└── assets/                  # _common/_template 快照，换机/重装自举用
    ├── _common/
    └── _template/

# 运行产物（脚本生成在你的 home 下，仓库之外，永不入 git）
~/.claude/shared/
├── _common/                 # 通用层：所有项目共享，改一处全局生效
│   ├── soul.md              #   LLM 写代码通用准则
│   ├── memory.md            #   记忆检索/写入规范
│   ├── code-review.md       #   review 默认范围
│   └── agents/              #   5 个去平台化 playbook 骨架
├── _template/               # 新项目脚手架（含 {{PROJECT}} 占位符）
│   ├── CLAUDE.local.md.tmpl
│   └── project-rules/*.tmpl
└── <slug>/                  # 每个项目一个目录
    ├── CLAUDE.local.md      #   ← 唯一权威索引，worktree 软链到这
    ├── personal.md          #   跨 worktree 私有笔记
    └── project-rules/       #   项目特有规则（提交红线/日志/业务/subagents）
```

---

## 用法

### 引导式向导（推荐入口）

在**目标项目目录**的 Claude Code 会话里输入：

```text
/local-distill-me            # 自动探测当前项目
/local-distill-me <slug>     # 带参时 <slug> 作为共享规则目录名的提示
```

也可以直接对 Claude 说「把 CLAUDE.local.md 那套搬到这个项目」。

向导会一步步带你走：**探测项目 → 确认 slug（可点选）→ 预览 → 跑脚手架 → 引导填规则骨架（自动扫开关让你勾选）→ 收尾校验**。全程可点选、非破坏、幂等。再次在已接入项目里触发，会问你意图（新增 worktree / 重填规则 / 校验），不重复初始化。

### 纯脚本逃生口（CI / 非交互）

不需要向导的交互填骨架时，直接跑确定性引擎。脚本相对自身定位 assets，放哪都能跑：

- **会话内**由 Claude 自动调用，路径用 `${CLAUDE_PLUGIN_ROOT}`，你无需关心。
- **手动 / CI** 里跑，先定位已装插件里的脚本：

```bash
INIT=$(find ~/.claude -path '*old-bird/skills/local-distill-me/scripts/init.sh' | head -1)
"$INIT" [<slug>] [<project-root>]
```

- `<slug>`：共享规则目录名，默认 = 项目目录 basename
- `<project-root>`：项目根目录，默认 = 当前目录（`pwd`）

> 逃生口只做脚手架 + 软链（下面「脚本做了什么」），**不含**向导的引导填骨架。

### 脚本做了什么

1. 建 `~/.claude/shared/<slug>/project-rules/`，从 `_template` 渲染骨架（替换 `{{PROJECT}}`）
2. 建空 `personal.md`、生成权威 `CLAUDE.local.md`
3. `git worktree list` 发现所有 worktree（非 git 项目则只处理根目录）
4. 逐个 worktree：把 `CLAUDE.local.md` 软链到权威索引（原有真实文件先备份为 `.bak.<时间戳>`）
5. 确保每个 worktree 的 `.gitignore` 忽略 `CLAUDE.local.md` 与 `.bak`

### 跑完还要做一件事

脚手架落下的是**骨架**，必须结合项目实际填实（这一步是真正价值）：

- `project-rules/commit-preflight.md`：grep 项目里的测试沙盒 / mock / 本地拦截开关（`TEST_MODE` / `MOCK` / `DEBUG` / 本地 flag 等），把真实开关填进「提交前必回滚」清单
- `project-rules/business-summary.md`：登记「改了 X 模块要同步 Y skill」
- `project-rules/subagents.md`：默认指向 `_common/agents/` 通用骨架，要特化再覆盖
- **可选规则**（默认也落了空骨架，不用就删文件 + 删索引对应条目，**都走按需读取**）：
  - `pitfalls.md` 坑点/反模式（踩到即记、过时即删，只留 Top-N）
  - `architecture-invariants.md` 架构红线（不可违背的硬约束）
  - `release-checklist.md` 发布/合并前必查 gate
  - `glossary.md` 项目术语/缩写表
  - `logging-conventions.md` 日志/埋点约定（有规范才填）

---

## 关键特性

- **纯本地、不联网**：只读写本机文件（项目 worktree + `~/.claude/shared/`），不上传任何内容。
- **幂等**：重复运行不破坏已有内容；已正确软链的 worktree 跳过，已存在的规则文件不覆盖。
- **多 worktree 零漂移**：所有 worktree 软链到同一权威文件；新增 worktree 后再跑一次即可补软链——或装可选的 `post-checkout` 钩子（向导会问），新建 worktree **自动**补软链，零手动。
- **不 commit**：脚本只改 worktree 内的软链与 `.gitignore`，绝不替你提交。`.gitignore` 那一行是 tracked 改动，需你自己确认提交。
- **不 clobber**：已有规则文件一律跳过，保护你已填的内容。
- **可换机自举**：插件自带 `assets/` 内置 `_common`/`_template` 快照，新机器上装好 `old-bird` 插件后、`~/.claude/shared/` 为空时脚本自动还原。

---

## 通用层 vs 项目层 —— 怎么分

- **放 `_common/`（跨项目通用）**：行为准则、记忆规范、review 默认范围、playbook 骨架。改一次所有项目生效。
- **放 `<slug>/project-rules/`（项目特有）**：带具体业务 / 平台 / 文件名 / 开关名的规则。绝不上浮到 `_common/`。

判断标准：这条规则换个项目还成立吗？成立 → `_common/`；只对本项目成立 → `project-rules/`。

---

## 迁移已有的 bespoke 项目

如果项目已经有一套手写的 `~/.claude/shared/<slug>/`（文件名和模板不同，如 `commit-status-sync.md` 而非 `commit-preflight.md`），**不要直接跑 init.sh 的脚手架**（会落下用不到的模板骨架）。改为：

1. 手写 / 调整权威 `~/.claude/shared/<slug>/CLAUDE.local.md`，通用条目改引 `_common/*`，项目条目保留
2. 只复用脚本的软链部分（或手动 `ln -s` 各 worktree）

例如一个含三个 worktree 的既有项目即按此方式迁移：三个 worktree 软链到权威索引，通用规则改走 `_common/`，项目规则原样保留。

---

## 排错

| 现象 | 原因 / 处理 |
|---|---|
| 改了某 worktree 的 `CLAUDE.local.md` 没生效到别处 | 你编辑的是软链指向的同一文件，本就是全局生效；若变成独立文件说明软链被断开，重跑 init.sh 修复 |
| `CLAUDE.local.md` 出现在 `git status` | `.gitignore` 没忽略它，重跑 init.sh 或手动补 `CLAUDE.local.md` 到 `.gitignore` |
| 会话没加载到某规则 | 检查 `CLAUDE.local.md` 里 `@` 引用的文件是否真实存在（dangling import 会被静默跳过） |
| 换了新机器规则全没了 | `~/.claude/shared/` 不在 git 里，需单独同步；装好 `old-bird` 插件后跑一次 init.sh 会从插件自带 `assets/` 自举出 `_common`/`_template` |
