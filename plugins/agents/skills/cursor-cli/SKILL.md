---
name: cursor-cli
description: >
  调度 Cursor Agent CLI 执行代码审查、子任务派发或代码问答。
  触发场景：
  (1) 用户要求使用 Cursor 进行代码审查 / code review
  (2) 用户需要将子任务派发给 Cursor Agent 执行
  (3) 用户提到"cursor review"、"cursor agent"、"用 cursor 帮我看看"等关键词
  (4) 用户希望通过外部 AI Agent 获得第二意见（second opinion）
  (5) 用户需要在隔离环境（worktree）中执行 AI 任务
  (6) 用户提到"派发任务给 cursor"、"让 cursor 做"、"cursor 帮忙"等表达
---

> **版本检测**：执行前先运行 `bash "<skill_dir>/../../../scripts/version-check.sh" 2>/dev/null`，若输出 `UPGRADE_AVAILABLE` 则按 `plugins/core/skills/version-update/SKILL.md` 的交互流程处理。

# Cursor Agent CLI 调度

通过 `cursor agent` CLI 将任务派发给 Cursor Agent 执行。采用**薄转发包装器（thin forwarding wrapper）**模式：构建命令 → 派发执行 → 原样返回结果。

## 核心原则

1. **你是调度器，不是执行者**：你只负责构建 `cursor agent` 命令并派发，不要自己执行任务内容
2. **结果忠实返回**：Cursor Agent 的结论忠实展示给用户（调度脚本会自动从 JSON 中提炼最终文本），不要修改、总结或重新解释
3. **不做越权操作**：不要在 Cursor 执行期间自己去读代码、分析问题或提前给结论
4. **用户确认优先**：涉及写操作（`--force`）时必须先征得用户同意
5. **优先使用调度脚本**：所有派发默认走 `scripts/cursor-dispatch.sh`，自动处理落盘、提炼和截断，避免 Bash 工具输出上限吞掉结论

## 前置检查

在执行任何操作前，先验证 Cursor CLI 可用：

```bash
command -v cursor >/dev/null 2>&1 && cursor agent --version 2>/dev/null || echo "CURSOR_NOT_FOUND"
```

如果不可用，提示用户：
- 安装 Cursor IDE 后运行 Shell Command: Install 'cursor' command
- 或运行 `cursor agent install-shell-integration`

## 三种调度模式

### 1. Review 模式（代码审查）

**用途**：让 Cursor Agent 以只读模式审查代码，生成审查报告

**命令构建**：

```bash
cursor agent --print --output-format json --mode plan --workspace "<workspace_path>" "<review_prompt>"
```

**关键参数**：
- `--mode plan`：只读模式，Cursor 只分析不修改代码
- `--print`：非交互式输出（headless 模式）
- `--output-format json`：结构化输出，便于解析

**Prompt 构建规则**：
- 明确审查范围：指定文件路径、变更范围或 diff
- 审查维度：代码质量、安全性、性能、可维护性
- 输出要求：按严重程度排序，包含文件路径和行号

**示例用法**：
```
# 审查当前分支的变更
cursor agent --print --output-format json --mode plan \
  --workspace "$(pwd)" \
  "Review the changes in the current branch compared to main. Focus on: 1) security issues 2) performance problems 3) code quality. List findings by severity with file paths and line numbers."

# 审查指定文件
cursor agent --print --output-format json --mode plan \
  --workspace "$(pwd)" \
  "Review src/auth/login.ts for security vulnerabilities and best practices."
```

### 2. Task 模式（子任务派发）

**用途**：将具体的编码任务派发给 Cursor Agent 执行（可读可写）

**命令构建**：

```bash
# 默认模式（需用户确认写操作）
cursor agent --print --output-format json --workspace "<workspace_path>" "<task_prompt>"

# 自动批准模式（用户明确同意后）
cursor agent --print --output-format json --force --workspace "<workspace_path>" "<task_prompt>"
```

**关键参数**：
- 无 `--mode` 参数：默认模式，具备完整的读写和 shell 执行能力
- `--force`：自动批准所有工具调用（仅在用户明确同意后使用）
- `--worktree [name]`：在隔离的 git worktree 中执行（推荐用于有风险的操作）

**安全规则**：
- 默认不加 `--force`，让 Cursor 逐步确认操作
- 如果用户说"放心执行"、"全自动"、"yolo"等，才加 `--force`
- 对于危险操作（删文件、改配置），建议使用 `--worktree` 隔离执行

**Prompt 构建规则**：
- 任务描述必须具体、可执行，包含明确的完成标准
- 指定工作目录和涉及的文件范围
- 一次只派发一个任务，不要混合多个不相关任务

**示例用法**：
```
# 派发重构任务（worktree 隔离）
cursor agent --print --output-format json --worktree "refactor-auth" \
  --workspace "$(pwd)" \
  "Refactor src/auth/ to use JWT instead of session-based auth. Update all related tests."

# 派发修复任务
cursor agent --print --output-format json \
  --workspace "$(pwd)" \
  "Fix the TypeScript compilation error in src/utils/parser.ts:42. The error is: Type 'string' is not assignable to type 'number'."
```

### 3. Ask 模式（代码问答）

**用途**：向 Cursor Agent 提问关于代码库的问题（只读）

**命令构建**：

```bash
cursor agent --print --output-format json --mode ask --workspace "<workspace_path>" "<question>"
```

**关键参数**：
- `--mode ask`：问答模式，只读不写
- 适合理解代码逻辑、查找实现细节、了解架构设计

**示例用法**：
```
# 询问代码架构
cursor agent --print --output-format json --mode ask \
  --workspace "$(pwd)" \
  "How does the authentication flow work in this project? Which files are involved?"

# 询问特定实现
cursor agent --print --output-format json --mode ask \
  --workspace "$(pwd)" \
  "What does the function processPayment in src/billing/processor.ts do? What are its edge cases?"
```

## 高级选项

### 模型选择

通过 `--model` 指定 Cursor Agent 使用的模型：

```bash
cursor agent --print --model "sonnet-4" --workspace "$(pwd)" "<prompt>"
```

可用模型通过 `cursor agent --list-models` 查看。用户未指定时不传 `--model`，使用 Cursor 默认配置。

### Worktree 隔离执行

对于有风险的写操作，推荐使用 worktree 隔离：

```bash
# 自动命名的 worktree
cursor agent --print --worktree --workspace "$(pwd)" "<task_prompt>"

# 指定名称的 worktree
cursor agent --print --worktree "fix-bug-123" --workspace "$(pwd)" "<task_prompt>"

# 基于特定分支创建 worktree
cursor agent --print --worktree "feature-x" --worktree-base "develop" --workspace "$(pwd)" "<task_prompt>"
```

### 后台执行

对于耗时较长的任务，使用 Bash 工具的 `run_in_background: true` 参数在后台执行：

```bash
# 后台执行长时间任务
cursor agent --print --output-format json --workspace "$(pwd)" "<long_running_task>"
```

后台执行时：
- 使用 Bash 工具的 `run_in_background: true` 选项
- 任务完成后会自动通知
- 不要轮询或 sleep 等待

### 恢复会话

```bash
# 恢复上次的会话
cursor agent --print --continue --workspace "$(pwd)" "<follow_up_prompt>"

# 恢复指定会话
cursor agent --print --resume "<chat_id>" --workspace "$(pwd)" "<follow_up_prompt>"
```

## 工作流程

### 标准 Review 流程

1. **确认范围**：询问用户要审查的范围（当前分支 diff / 指定文件 / 整个目录）
2. **构建 Prompt**：根据范围构建审查指令，包含具体的审查维度
3. **获取 diff 上下文**（可选）：如果是审查变更，先用 `git diff` 获取变更摘要，嵌入 prompt
4. **派发执行**：使用 review 模式执行 `cursor agent`
5. **展示结果**：原样展示 Cursor 的审查报告
6. **用户决策**：询问用户是否需要针对发现的问题采取行动

### 标准 Task 派发流程

1. **理解任务**：确认用户的任务需求和完成标准
2. **评估风险**：判断是否需要 `--worktree` 隔离或 `--force` 自动批准
3. **构建 Prompt**：将任务描述转换为清晰、可执行的指令
4. **征得同意**：展示即将执行的命令，征得用户确认
5. **派发执行**：使用 task 模式执行
6. **展示结果**：原样展示 Cursor 的执行结果
7. **后续处理**：如果在 worktree 中执行，告知用户 worktree 路径和合并方式

## 辅助脚本（推荐入口）

调度脚本位于 `scripts/cursor-dispatch.sh`，**默认以此为入口**，它解决了直接调 `cursor agent` 时的输出截断问题：

```bash
bash "<skill_dir>/scripts/cursor-dispatch.sh" <mode> [options] "<prompt>"
```

支持的 mode：`review`、`task`、`ask`、`check`（环境检查）

### 输出协议（重要：解决截断问题）

调度脚本对 `cursor agent` 的输出做三层处理，避免被 Claude Code Bash 工具的 stdout 上限吞掉关键结论：

1. **原始输出落盘**：完整 JSON（含工具调用轨迹）写入 `$CURSOR_OUT_DIR`（默认 `/tmp`），文件名形如 `cursor-<mode>-<ts>-<pid>.out`
2. **提炼最终文本**：自动用 `jq` 从 JSON 中抽取 `.result`（或 `.content`/`.message`/`.text`/`.output` 等字段）写入同名 `.txt`，体积通常只有原始 JSON 的 1/5–1/10
3. **智能回显**：
   - 提炼文本 ≤ 阈值（默认 20000 字节，通过 `CURSOR_STDOUT_LIMIT` 覆盖）→ 完整打印
   - 超过阈值 → 仅打印 head + tail + `[TRUNCATED]` 提示，并附带原始文件路径
   - 结尾固定输出元信息脚注：`text file` / `raw file` / `exit code`

### 遇到截断时如何取回完整内容

如果 stdout 里看到 `[TRUNCATED]` 提示或用户要求完整轨迹：

- 解析脚注里的 `text file` 路径（提炼后的文本）或 `raw file` 路径（原始 JSON）
- 使用 **Read 工具 + offset/limit** 分页读取该文件，不要再用 `cat` / `head` 走 Bash
- 读取时按用户关心的维度（如"只看安全相关结论"）做分段提取，而不是一次拉全文

### 额外选项

- `--raw` / `--no-extract`：跳过提炼，stdout 直接回显原始输出（仍会按阈值截断 + 落盘）
- `--out-dir <path>`：自定义落盘目录
- `--out-file <path>`：直接指定原始输出文件路径
- 环境变量 `CURSOR_STDOUT_LIMIT`：覆盖 stdout 回显字节阈值
- 环境变量 `CURSOR_OUT_DIR`：覆盖默认落盘目录

## 注意事项

- Cursor Agent 的 `--print` 模式输出到 stdout，错误输出到 stderr（脚本会分别落盘）
- `--output-format json` 返回结构化 JSON，脚本默认自动提炼结论，用户看不到一堆 tool_call 噪音
- 如果 Cursor Agent 执行失败，报告错误并停止，不要尝试变通方案
- 不要在 Cursor Agent 执行的同时自己也去修改代码，避免冲突
- 长时间任务建议使用后台执行 + worktree 隔离的组合；后台执行结束后，务必通过脚注里的文件路径取回完整结果
- Prompt 中使用英文可以获得更好的效果（Cursor 模型对英文支持更好）
- 脚本依赖 `jq` 进行提炼；若未安装，会回退为原始输出（并打印 WARN）
