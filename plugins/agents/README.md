# agents

> 外部 AI Agent 调度工具集——让 Claude Code 把任务派发给 Cursor / Codex / 其它 AI CLI 执行，并把结果忠实带回。

> ⚠️ 这里的 "agents" 指的是 **外部 AI 智能体**（Cursor Agent、Codex 等），不是 Claude Code 内部的 subagent（`agents/*.md`）。

## 收录的 skills

| Skill | 用途 | 状态 |
| --- | --- | --- |
| [`cursor-cli`](./skills/cursor-cli) | 调度 Cursor Agent CLI 执行代码审查、子任务派发或代码问答（review / task / ask 三模式） | ✅ stable |

> 计划中：`codex-cli`（OpenAI Codex CLI 调度）、`claude-cli`（嵌套 Claude 调度）……欢迎 PR。

## 安装

```
/plugin marketplace add kaelinda/agent-marketplace
/plugin install agents@manji
```

安装后所有 skills 都会随插件一并启用，按 `description` 触发——例如对 Claude 说"用 cursor 帮我 review 一下"，就会自动激活 `cursor-cli` skill。

## 通用设计

本插件下的 skills 遵循统一的「薄转发包装器」模式：

1. **Claude 是调度器，不是执行者**——只构建命令 / 派发 / 回传，不自己代写代码
2. **结果忠实返回**——不二次总结、不重新解释外部 Agent 的产出
3. **写操作要先确认**——`--force` / 自动批准类参数必须经用户明示同意
4. **输出截断保护**——所有 skill 默认通过附属脚本落盘 + 提炼，避免 Claude Code Bash 工具的 stdout 上限吞掉关键结论
5. **依赖清晰前置**——每个 skill 在 README / SKILL.md 中明确列出外部 CLI 与可选工具（如 `jq`）

## 许可证

MIT — 同仓库根 [LICENSE](../../LICENSE)
