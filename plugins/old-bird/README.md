# Old Bird Plugin

老鸟工具集 —— 给资深开发者用的**本地配置与工作流治理**工具。

核心理念：把自己打磨过的私房实践，**纯本地、安全（不联网、不上传、不入库）地蒸馏**成可复用机制，
干净地复用到每个项目。不承担业务功能。

## Skills

### local-distill-me

把一套「`CLAUDE.local.md` 轻量索引 + `~/.claude/shared/` 共享规则」的私有指令体系，
**纯本地、不入库**地蒸馏并**引导式**移植到任意项目，并为多个 git worktree 配置统一、不会漂移的私有规则。
全程只读写本机文件、不联网，私有规则始终留在你自己机器上。

三层 + 软链架构：

| 层 | 位置 | git | 作用 |
|---|---|---|---|
| 公共 | 仓库根 `CLAUDE.md` | tracked | 团队共享说明（本 skill 不动它） |
| 私有索引 | 各 worktree 根 `CLAUDE.local.md` | **gitignored** | 软链 → 共享目录唯一权威索引 |
| 共享规则 | `~/.claude/shared/` | 仓库之外 | 规则正文（通用层 `_common/` + 项目层 `<slug>/`） |

规则正文放在 home 下，每个 worktree 的 `CLAUDE.local.md` 都软链到同一份权威索引
→ 改一处全 worktree 生效，物理上不会漂移。

**触发方式：**

- `/local-distill-me`：在目标项目目录触发，向导自动探测当前项目。
- `/local-distill-me <slug>`：带参时 `<slug>` 作为共享规则目录名的提示。
- 自然语言："把 CLAUDE.local.md 那套搬到这个项目""给这个项目配 shared 规则"
  "多个 worktree 怎么共享 Claude 规则"等。

向导分 6 步（探测 → 确认 slug → 预览 → 跑脚手架 → 引导填规则 → 可选装 worktree 钩子 → 收尾校验），
能点选就用 `AskUserQuestion`，全程非破坏、幂等可重跑。

详见 [`skills/local-distill-me/SKILL.md`](skills/local-distill-me/SKILL.md) 与
[`skills/local-distill-me/QUICKSTART.md`](skills/local-distill-me/QUICKSTART.md)。
