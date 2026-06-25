# QUICKSTART — local-distill-me

从零到落地的最短路径。预计 5 分钟跑通第一个项目。

> 前置：已安装 Claude Code，目标项目是个 git 仓库（非 git 也能用，只是没有 worktree 自动发现）。

---

## 0. 安装

本 skill 随 **`old-bird` 插件**分发（manji 市场）。在 Claude Code 里：

```
/plugin marketplace add kaelinda/agent-marketplace   # 已加过市场可跳过
/plugin install old-bird@manji
```

确认 Claude Code 能看到它：在任意会话里输入 `/` 看是否出现 `local-distill-me`，或直接对 Claude 说「把 CLAUDE.local.md 那套搬过来」。

> 想绕过市场直接用，也可以把仓库里的 `plugins/old-bird/skills/local-distill-me/` 拷到 `~/.claude/skills/local-distill-me/`——但推荐走插件，能跟随市场更新。

---

## 1. 初始化 + 接入项目（推荐：引导式向导）

进到**目标项目目录**，在 Claude Code 会话里输入：

```text
/local-distill-me
```

向导会一步步带你走，全程可点选、非破坏：

1. **探测**：自动认出当前项目、是否 git 仓库、几个 worktree、是否首次接入。
2. **确认 slug**：默认用项目目录名，给你确认或改名。
3. **预览 + 确认**：讲清要建什么、软链哪些 worktree，再动手。
4. **跑脚手架**：建 `~/.claude/shared/<slug>/`，软链所有 worktree，配 `.gitignore`（首次还会自举 `_common`/`_template`）。
5. **引导填规则**：自动扫你代码里的"调试开关"让你勾选纳入提交红线，问日志规范有无……（见 §3）。
6. **可选钩子**：问你要不要装一个 git `post-checkout` 钩子——以后**新建 worktree 自动补软链**，免得每次手动跑（见 §4）。
7. **收尾**：校验软链 + 告诉你唯一要手动做的事（commit `.gitignore` 那一行）。

> **纯脚本逃生口**（CI / 不需要交互填骨架时）：脚本相对自身定位 assets，放哪都能跑。
>
> - 会话内由 Claude 自动调用，路径用 `${CLAUDE_PLUGIN_ROOT}`，你无需关心。
> - 手动 / CI 里跑，先定位已装插件里的脚本，再执行：
>
> ```bash
> INIT=$(find ~/.claude -path '*old-bird/skills/local-distill-me/scripts/init.sh' | head -1)
> "$INIT" [<slug>] [<project-root>]
> ```
>
> 等价于上面第 1、4 步的确定性部分——只建脚手架 + 软链，**不含** §3 的引导填骨架。

---

## 2. 验证软链 + 加载

```bash
# 软链指向唯一权威索引
readlink ~/code/my-app/CLAUDE.local.md
# → ~/.claude/shared/my-app/CLAUDE.local.md

# git 已忽略它（不会误提交）
git -C ~/code/my-app check-ignore CLAUDE.local.md   # 输出 CLAUDE.local.md = 已忽略
```

在该项目里**新开一个 Claude Code 会话**，问它「现在加载了哪些 soul / 提交红线规则」，确认通用层（`soul.md`）和项目层（`commit-preflight.md`）已进上下文。`@` 前缀的是每会话强制加载，裸路径的是按需读取。

---

## 3. 把项目规则骨架填实（关键价值）

> §1 的向导会**自动带你做这一步**（扫开关 → 勾选 → 填表）。下面是它在底层做的事，也是不走向导时的手动版参考。

脚手架落下的是**空骨架**，要结合项目实际填。最重要的是提交前红线：

```bash
# 先扫项目里有没有"调试时打开、提交前必须关"的开关
grep -rnE "TEST_MODE|MOCK|DEBUG|localhost|skipAuth" src/ | head
```

把命中的真实开关填进 `~/.claude/shared/my-app/project-rules/commit-preflight.md` 的清单表，例如：

```markdown
| 文件 | 变量 / 标记 | 干净提交态 | 打开态意味着 |
|---|---|---|---|
| `src/api/client.ts` | `const USE_MOCK` | `false` | 走本地 mock 数据，不打真实后端 |
```

其余骨架按需处理：

- `business-summary.md`：登记「改了 X 模块要同步 Y skill / 文档」。没有就留空。
- `subagents.md`：默认指向 `_common/agents/` 通用骨架；要特化某个 playbook 再在 `project-rules/agents/` 覆盖。
- **可选规则**（向导会问你启用哪些；不用就删文件 + 删索引条目，**都走按需读取**）：
  - `pitfalls.md` 坑点/反模式——**踩到即记、过时即删**（`日期 | 坑 | 根因 | 规避规则`），只留 Top-N，不进强制加载
  - `architecture-invariants.md` 架构红线 · `release-checklist.md` 发布前必查 · `glossary.md` 术语表 · `logging-conventions.md` 日志约定

> 交给 Claude 做更快：直接说「按这个项目实际，把 commit-preflight 和 business-summary 填一下」，它会先 Explore 代码再填。

---

## 4. 多 worktree：新增 worktree 后补软链

> **装了钩子就免手动**：如果初始化时选了装 `post-checkout` 钩子（§1 步骤 6），新建 worktree 会**自动**补软链，本节可跳过。没装才需要下面的手动补。

新开 worktree 后，在项目里**再次输入 `/local-distill-me`**——向导探测到是「已接入」会问你意图，选**「新增 worktree 软链」**即可，它只补新 worktree、不重复初始化。

钩子原理：软链被 gitignore，git 不会把它带进新 worktree；`post-checkout` 钩子在新 worktree 检出时检测到缺软链就补上（项目级 `.git` 配置，不入库、所有 worktree 共享同一份）。手动装（先定位脚本同 §1 逃生口）：

```bash
HOOK=$(find ~/.claude -path '*old-bird/skills/local-distill-me/scripts/install-hook.sh' | head -1)
"$HOOK" <slug> <repo-root>
```

```text
git -C ~/code/my-app worktree add ~/code/my-app-feature -b feature
# 然后在会话里：/local-distill-me  →  选「新增 worktree 软链」
```

幂等：已正确软链的 worktree 跳过，已填的规则文件不覆盖。验证所有 worktree 指向同一文件：

```bash
for w in my-app my-app-feature; do readlink ~/code/$w/CLAUDE.local.md; done
# 两行应完全相同 → 物理上不可能漂移
```

---

## 5. 日常使用

| 想做的事 | 怎么做 |
|---|---|
| 改某项目的规则 | 直接编辑 `~/.claude/shared/<slug>/...` 或 `~/.claude/shared/<slug>/CLAUDE.local.md`。所有 worktree 自动生效（它们是软链） |
| 改全局通用准则 | 编辑 `~/.claude/shared/_common/`（soul / memory / playbook）。**所有项目**下次会话生效 |
| 接入新项目 | `cd` 进去，会话里输入 `/local-distill-me`，跟向导走 |
| 换新机器 | `~/.claude/shared/` 不在 git 里，需自己同步；装好 `old-bird` 插件后首次跑 init.sh 会从插件自带 `assets/` 自举出 `_common`/`_template` 兜底 |

---

## 6. 要不要提交什么？

- **软链 `CLAUDE.local.md`**：已被 `.gitignore` 忽略，**不入 git**，无需操心。
- **`.gitignore` 里新增的那一行**：这是 tracked 改动，**需要你自己 commit**（脚本不替你提交）。
- **`~/.claude/shared/` 全部内容**：在仓库之外，永远不进项目 git。

---

## 适配你自己的工具链

`_common/agents/` 的 playbook 里出现的工具名（如 `Explore` / `Plan` / `codex` / `Langfuse` 等）只是**示例编排**。换成你自己装的等价工具即可——改 `~/.claude/shared/_common/agents/*.md` 一次，所有项目生效。
