# Code Review Agent

> 索引：本项目的 `project-rules/subagents.md`

**触发词**："review 一下 / 帮我看下改动 / 提交前看下"

**目标**：多 Agent 并行 review + 意见对比 + 采纳建议。

**默认范围**：当前未提交改动（呼应 [../code-review.md](../code-review.md)）。不主动做功能分支 vs master 全量 diff，除非用户明说。

## 编排

1. **拿 diff**：`git diff` + `git diff --staged` + `git status`
2. **并行召唤 reviewer**（一条消息多 tool calls）：
   - 内部 review：`review` skill（Pre-landing PR review）
   - codex review：`codex` skill 的 review 模式（独立的 codex CLI 二审）
   - 深度调查：`codex:rescue` agent（适合疑似 bug / 复杂修复场景）
3. **意见对比**：把三方反馈做矩阵对比：
   - 一致问题 → 优先级 P0，必须改
   - 仅 1 方提到 → 评估是否误报
   - 互相冲突 → 列出冲突点 + 我的判断 + 让用户拍板
4. **采纳建议**：给出每条意见的「采纳 / 不采纳 / 待讨论」+ 理由

## 输出格式

```text
## 改动概览
- 文件数: N，主要变化: [...]

## Review 矩阵
| 问题 | review | codex | codex:rescue | 采纳建议 |
| --- | --- | --- | --- | --- |
| ... | ✅ | ✅ | ⚠️ | 改 |

## 必改项（一致命中）
- [ ] ...

## 待讨论（有冲突）
- ...

## 不采纳（附理由）
- ...
```

## 红线

- 不要为了"看起来全面"召唤所有 reviewer——小改动用 `review` 一家就够；中等改动加 `codex`；只有复杂修复/疑难 bug 才上 `codex:rescue`
- review 完不要主动 commit，给完建议等用户拍板
