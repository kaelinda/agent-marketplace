# memory plugin — 文档索引

> 这里收录的是"装好之后怎么用 / 怎么排查 / 怎么扩展"的全部用户文档。最小启动路径在仓库根的 [`../README.md`](../README.md)。

## 你应该先读哪一篇

| 你的处境 | 入口 |
|---|---|
| 第一次装，想跑通一条记忆 | [getting-started.md](getting-started.md) |
| 在 OpenViking / MCP / mem0 之间选不动 | [backends.md](backends.md) |
| 想知道 5 个 skill 各自什么时候会触发 | [skills.md](skills.md) |
| 要直接用 `memory-cli` 写脚本 / 自动化 | [cli.md](cli.md) |
| 看不懂 `config.json` / 想调安全策略 | [configuration.md](configuration.md) |
| `doctor` 报红 / capture 写不进去 | [troubleshooting.md](troubleshooting.md) |
| 想给 plugin 加新后端 / 加 hook | [architecture.md](architecture.md) |
| 数据存在哪、能不能跨设备、隐私边界 | [faq.md](faq.md) |

## 概念速查

- **memory plugin**：跨会话的长期记忆中间层。负责"什么时候记 / 什么时候召回 / 怎么治理"，本身**不存数据**。
- **backend**：真正存数据的后端服务。当前支持 `openviking`（HTTP）/ `openviking-mcp`（MCP server）/ `mem0`（云）。
- **adapter**：plugin 和 backend 之间的协议层。每个 backend 一个 adapter，统一返回 `AdapterResponse{ok, data, error, meta}`。
- **scope**：记忆的命名空间 URI。从 `scope_template` + `identity` 渲染出来，决定一条记忆归属于谁。
- **identity**：`tenant_id` + `user_id` + `agent_id` 三元组。fail-closed —— 不显式设置就拒绝启动。
- **skill / command**：Claude Code 侧的两种入口。skill 由模型按 frontmatter 触发词自动激活；command 由用户敲 `/recall …` 触发。

## 历史文档

`docs/legacy/` 是 Phase 1 的早期资料，里头 CLI 参数（例如 `recall --query` / `doctor --fix`）已经和当前实现不一致，仅供回溯。**不要照那里抄命令**。

---

文档版本：随 plugin v0.2.0 同步发布。下次破坏性变更会在 `CHANGELOG.md` 的 Migration 段写明对应文档需要怎么改。
