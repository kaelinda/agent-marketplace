# cursor-cli

> 调度 Cursor Agent CLI 执行代码审查、子任务派发或代码问答的薄转发包装器。

## 能干什么

- **Review 模式（只读）**：让 Cursor Agent 审查当前分支变更或指定文件，给出按严重程度排序的问题列表
- **Task 模式（读写）**：派发具体编码任务给 Cursor 执行，可选 `--worktree` 隔离 / `--force` 自动批准
- **Ask 模式（只读）**：向 Cursor 提问关于代码库的问题，适合理解架构和实现

定位是「让 Claude Code 把任务派发给 Cursor」——你是调度器，不是执行者。

## 触发场景

- "用 cursor 帮我 review 一下"
- "把这个重构任务派发给 cursor"
- "我想要 cursor 的 second opinion"
- "让 cursor 在 worktree 里跑这个改动"

## 依赖

- [Cursor IDE](https://cursor.sh/)，并已安装 `cursor` shell 命令（VS Code 命令面板 → `Shell Command: Install 'cursor' command`）
- 已登录：`cursor agent login`
- 推荐安装 `jq`（用于从 JSON 输出中提炼最终文本，否则会回退到原始 JSON）

环境检查：

```bash
bash plugins/cursor-cli/skills/cursor-cli/scripts/cursor-dispatch.sh check
```

## 直接调脚本（不通过 Claude）

```bash
# 审查当前分支
./scripts/cursor-dispatch.sh review --workspace "$(pwd)" \
  "Review changes in current branch vs main. Focus on security and correctness."

# 派发编码任务（worktree 隔离）
./scripts/cursor-dispatch.sh task --workspace "$(pwd)" --worktree "fix-bug-123" \
  "Fix the off-by-one error in src/utils/parser.ts:42"

# 代码问答
./scripts/cursor-dispatch.sh ask --workspace "$(pwd)" \
  "How does authentication work in this project?"
```

## 输出协议

为绕过 Claude Code Bash 工具的 stdout 体积上限，脚本：

1. 把原始 JSON 写入 `$CURSOR_OUT_DIR`（默认 `/tmp`）
2. 用 `jq` 提炼最终文本到同名 `.txt`
3. stdout 仅回显提炼文本；超过 20KB（`CURSOR_STDOUT_LIMIT`）时只打印 head + tail
4. 末尾固定打印 `text file` / `raw file` / `exit code` 脚注，方便用 Read 工具分页读取完整结果

## 许可证

MIT — 同仓库根 LICENSE
