---
description: 召回与当前任务相关的长期记忆并注入到对话上下文
argument-hint: [query]
---

请使用 memory plugin 的 `memory-recall` skill，根据用户输入的检索词召回相关记忆，并把结果作为结构化记忆块注入当前对话上下文，避免改写或裁剪。

执行流程：

1. 解析参数 `$1` 作为检索 query；为空时用最近一条用户消息或当前任务摘要替代。
2. 调用：
   ```bash
   bash "<skill_dir>/../../scripts/memory-cli" recall "$1"
   ```
   `<skill_dir>` 由 Claude Code 替换；这条命令会运行 `plugins/memory/scripts/memory-cli` 并打印 `[Relevant OpenViking Memory] ... [/Relevant OpenViking Memory]` 块。
3. 把命令输出原样追加到当前上下文，不做内容删改；若输出 `(no relevant memories found)` 就说明这次召回为空。
4. 后续回答时把召回到的事实/偏好/项目上下文当作权威信息使用。

注意：
- 这个命令不修改任何持久化记忆，只读。
- 如果 `memory-cli doctor --mode quick` 不通过（identity 配置缺失等），先告知用户配置问题再触发本召回。
