---
name: local-distill-me
description: 把一套「CLAUDE.local.md 索引 + ~/.claude/shared 共享规则」私有指令体系移植到一个项目，并为多 git worktree 配置统一的、不会漂移的私有规则。当用户说「把这套 CLAUDE.local.md / 私有规则体系搬到 XX 项目」「给这个项目配 shared 规则」「多个 worktree 怎么共享 Claude 规则」「移植 soul/commit 红线那套」时触发。
---

# local-distill-me — 引导式配置向导

把三层私有指令体系移植到任意项目：

- **通用层** `~/.claude/shared/_common/`：所有项目共享（soul / memory / code-review + 5 个 agent 编排骨架），改一处全局生效。
- **项目层** `~/.claude/shared/<slug>/`：本项目特有规则（提交前红线 / 日志约定 / 业务沉淀 / subagents 索引）。
- **索引** 各 worktree 根的 `CLAUDE.local.md` **软链**到 `~/.claude/shared/<slug>/CLAUDE.local.md`（唯一权威，gitignored，多 worktree 零漂移）。

## 调用方式

- `/local-distill-me`：在**目标项目目录**触发，向导自动探测当前项目。
- `/local-distill-me <slug>`：带参时，`<slug>` 作为共享规则目录名的提示。
- 自然语言："把 CLAUDE.local.md 那套搬到这个项目" 等。

> **本 skill 是引导式向导**：不要闷头跑完脚本就抛骨架。按下面 6 步逐步带用户走，能点选就用 `AskUserQuestion`，每步给反馈，结尾只留一个明确待办。

---

## Step 0 · 探测 & 开场（只读，先别问）

并行执行只读探测，然后用一句话回显，不让用户猜：

```bash
ROOT="$(pwd)"                                  # 或用户指明的项目根
git -C "$ROOT" rev-parse --show-toplevel 2>/dev/null   # 是否 git 仓库 + 真实根
git -C "$ROOT" worktree list 2>/dev/null               # 有几个 worktree
ls -d ~/.claude/shared/<slug> 2>/dev/null              # 已接入过？
ls -d ~/.claude/shared/_common ~/.claude/shared/_template 2>/dev/null  # 是否首次（需自举）
```

开场白示例：「检测到项目 **my-app**（git 仓库，2 个 worktree）。`~/.claude/shared/my-app` 还没建——这是首次接入。下面带你配一下。」

- 若拿到 git 顶层目录，**用它当项目根**（而非裸 `pwd`），避免在子目录触发时跑偏。
- 若 `shared/<slug>` 已存在 → 这是「再次运行」，走 Step 1 的意图分支。

## Step 1 · 确认 slug & 意图（`AskUserQuestion`）

**新接入**（`shared/<slug>` 不存在）——确认 slug：
- 默认 = 项目目录 basename。用 `AskUserQuestion` 给：`用默认「<basename>」(推荐)` / `我要改个名`。
- slug 不能带斜杠；与 `~/.claude/shared/` 下已有目录重名要提示换名。

**再次运行**（`shared/<slug>` 已存在）——问意图，用 `AskUserQuestion`：
- `新增 worktree 软链`（最常见：开了新 worktree 来补软链）
- `重填某个规则骨架`（commit-preflight / business-summary / logging / subagents）
- `全量校验`（只检查软链 + dangling，不改东西）
- 选定后跳到对应步骤，**不要重复初始化**。

## Step 2 · 预览 & 确认（一句话 + 一次确认）

跑脚本前先讲清楚要做什么，强调非破坏：

> 我将：① 建 `~/.claude/shared/<slug>/` 规则骨架；② 把 **N 个 worktree** 的 `CLAUDE.local.md` 软链到唯一权威索引（原有真实文件会先备份成 `.bak`）；③ 向各 worktree `.gitignore` 追加一行忽略。**已存在的不覆盖、幂等可重跑。** 开始吗？

轻量确认即可（非破坏操作，别啰嗦多轮）。

## Step 3 · 跑确定性脚手架

```bash
${CLAUDE_PLUGIN_ROOT}/skills/local-distill-me/scripts/init.sh <slug> <显式项目根>
```

- **显式传项目根**（Step 0 探测到的 git 顶层），不要依赖 cwd。
- 脚本会自举 `_common`/`_template`（首次）、渲染骨架、发现并软链所有 worktree、配 `.gitignore`。
- 解析输出，把 `[new]/[link]/[fix]/[ok]/[skip]` 翻成人话汇报（例：「新建了 4 个规则骨架，软链了 2 个 worktree」）。

## Step 4 · 引导填规则骨架（向导灵魂，逐项 · 每项可跳过/延后）

脚手架落下的是**空骨架**，逐个带用户填实。每项都先说"这是干嘛的"，再用最省事的方式收集：

1. **提交前红线 `commit-preflight.md`**（最重要）：
   - 主动扫候选开关：`grep -rnE "TEST_MODE|MOCK|DEBUG|skipAuth|localhost|isDev|USE_.*_ENTRY" <项目根>/src 2>/dev/null`（路径按项目调整）。
   - 用 `AskUserQuestion`（`multiSelect: true`）把命中项列出来，让用户勾选「调试时打开、提交前必须关」的那些。
   - 按勾选填 `~/.claude/shared/<slug>/project-rules/commit-preflight.md` 的清单表（文件 / 变量 / 干净态 / 打开态含义）。
   - 零命中 → 告诉用户"没扫到明显开关"，留空表 + 说明以后怎么补。

2. **业务沉淀 `business-summary.md`**：
   - 问："有没有『改了 X 模块要同步某个 skill / 文档』的约定？" 这是映射关系，用**自由输入**收集（不适合点选）。
   - 有则记进去；没有就留空，说明它是可选项。

3. **可选规则（批量选，`AskUserQuestion` · `multiSelect: true`）**：脚手架默认把这几个可选规则也落了空骨架。问「本项目要启用哪些？」：
   - `日志约定` logging-conventions —— 有统一日志 / 埋点规范才需要
   - `坑点/反模式` pitfalls —— 代码看不出的隐性知识。**记录约定**：踩到 / 发现即追加（`日期 | 坑 | 根因 | 规避规则`），过时即删，只留 Top-N，**刻意不进强制加载**（避免吃每会话上下文）
   - `架构红线` architecture-invariants —— 不可违背的硬约束（"X 不与 Y 共享""别绕过 IPC"等）
   - `发布前必查` release-checklist —— 合 release / master 前的 gate
   - `术语表` glossary —— 项目黑话 / 缩写 / 状态码语义
   处理：
   - **选中的**：简述用途，问要不要现在 seed 几条真实内容（可"以后再填"，留空骨架即可）。坑点特别说明它是"踩到即记、过时即删"的活文档。
   - **没选的**：删对应 `project-rules/*.md` + 删权威 `CLAUDE.local.md` 里该条「按需读取」项（保持索引无悬空）。

4. **subagents 索引 `subagents.md`**：
   - 默认指向 `_common/agents/` 通用骨架，多数项目无需动。
   - 简短问一句"要为某个 playbook 做项目特化吗"，一般保持默认即可。

> 用户随时可说"先跳过/以后再填"——尊重，记下哪些待填，进收尾。

## Step 5 · 可选：装「新建 worktree 自动软链」钩子（`AskUserQuestion`）

软链被 gitignore，所以**新建 worktree 不会自动带上 CLAUDE.local.md**——默认得回来再跑一次向导补软链。可装一个 git `post-checkout` 钩子让它自动补：

- 用 `AskUserQuestion` 问：「装『新建 worktree 自动软链』钩子吗？」
  - `装（推荐）` —— 以后新建 worktree 零手动，自动补软链
  - `不装` —— 每次手动跑向导补
- 选「装」→ 跑 `${CLAUDE_PLUGIN_ROOT}/skills/local-distill-me/scripts/install-hook.sh <slug> <repo-root>`，把结果汇报。
- 钩子是项目级 `.git` 配置：**不入库、不影响协作者、所有 worktree 共享同一份**；只在缺软链时补，非破坏，幂等。
- 若脚本返回非 0（打印 `[skip]`）——「已有他人的 post-checkout 钩子」或「core.hooksPath 被 husky 等重定向」——**不要硬装**，把它打印的手动片段原样转达用户，让其自行决定。

## Step 6 · 收尾 & 校验

```bash
for w in $(git -C <项目根> worktree list --porcelain | awk '/^worktree /{sub(/^worktree /,"");print}'); do readlink "$w/CLAUDE.local.md"; done
```

- 确认所有 worktree 的 `readlink` 指向**同一**权威索引（零漂移）。
- 确认权威 `CLAUDE.local.md` 里 `@` 引用的文件都真实存在（无 dangling import）。
- **明确只留一个手动待办**：`.gitignore` 的新增行是 tracked 改动，给确切命令让用户提交，例：
  `git -C <项目根> add .gitignore && git commit -m "chore: gitignore CLAUDE.local.md"`
- 一句日常提示：以后改规则直接编辑 `~/.claude/shared/<slug>/...`（项目规则）或 `~/.claude/shared/_common/...`（全局通用），**所有 worktree 下次会话自动生效**，不用再跑本向导；只有新增 worktree 时回来跑一次补软链。

---

## 红线

- **交互只在本层做**：用 `AskUserQuestion` / 对话收集，**绝不**给 `init.sh` 加 `read` 之类交互（Bash 工具无 stdin，会挂）。
- **不要 commit**：脚本和向导都不替用户提交；`.gitignore` 改动交用户确认。
- **不要 clobber**：已存在的规则文件一律跳过，不覆盖用户已填内容。
- **通用 vs 项目分清**：只有真正跨项目通用的规则才进 `_common/`；带具体业务/平台/文件名的规则留 `<slug>/project-rules/`。
- **显式传项目根**给 init.sh，别靠 cwd。
