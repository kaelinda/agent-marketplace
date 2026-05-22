# FAQ

收集真实在 issue / Slack / 对话里被反复问到的问题。短回答 + 链接到具体文档。

## 数据放在哪？我的数据安全吗？

memory plugin 本身**不存数据**，只是一个中间层。数据的归属取决于你选的 backend：

| Backend | 数据落点 |
|---|---|
| `openviking` (HTTP) | 你自己起的 OpenViking server |
| `openviking-mcp`    | OpenViking MCP server 背后挂的存储 |
| `mem0`              | mem0 云 |

详见 [backends.md](backends.md)。

## 切换 backend 我的旧记忆会自动迁移吗？

**不会**。每个 backend 的 scope 格式 / memory ID 编码 / 索引方式都不一样。

迁移流程：
```bash
# 旧后端
memory-cli admin backup --output ~/migration.json

# 改 config 切到新后端
# ...

# 新后端
memory-cli admin restore --file ~/migration.json
```

注意：相似度索引会在新后端**重建**，召回行为可能跟旧后端不完全一致。

## 我能让两个 Agent 共享同一份记忆吗？

**部分可以**，但不太优雅。当前 v0.2.0 还没有 sharing 一等抽象（在 Phase 3 路线图）。短期方案：

1. 显式 `--scope` 写到一个共享 URI：
   ```bash
   memory-cli capture --content "..." --scope viking://tenants/default/shared/team-a/
   ```
2. 召回时也用 `browse --scope <shared>` 或允许跨 user 召回（`safety.allow_cross_user_read=true`）
3. 多 agent 用**同一个** `OV_USER_ID` + 不同 `OV_AGENT_ID`，user scope 自然共享

更通用的 `team` / `workspace` / `shared` 抽象等 Phase 3。

## `OV_USER_ID` 和 `OV_AGENT_ID` 是什么？

- `OV_USER_ID`：使用 agent 的**人**的稳定标识（比如 GitHub username / 内部工号）
- `OV_AGENT_ID`：agent 实例自己的稳定名（`code-assistant` / `research-agent`）

二者结合形成 user scope 和 agent scope。详见 [configuration.md#scope-是怎么算出来的](configuration.md#scope-是怎么算出来的)。

## 为什么不让我用默认值就跑起来？

历史教训：多 agent 同机部署时，两个 agent 都漏配 `OV_AGENT_ID`，结果都共享 `default_agent` 命名空间——既不隔离也不有意共享，纯污染。fail-closed 把这个错误在启动时就报掉。

测试 / demo 想绕过：`safety.allow_default_identity=true`。详见 [configuration.md#identity-安全规则](configuration.md#identity-安全规则)。

## 写入的内容会被发到哪里做向量化？

取决于 backend：

- OpenViking：发到你 OpenViking server，向量化策略由 server 端决定
- mem0：发到 mem0 cloud，由 mem0 嵌入
- MCP：发到 MCP server 配置的后端

memory plugin 本身**不调用任何 LLM / embedding API**。它只在本地做：
- 敏感检测（正则）
- 分类（基于规则的 keyword 匹配，可换插件）
- 去重 / 冲突检测（基于 type+title 字符串）

## 我想自己加一个 backend，从哪儿开始？

`docs/architecture.md` 的"写一个新 adapter"章节。核心是实现 `MemoryAdapter` 协议 + 过 `tests/test_adapter_contract.py`。

## 敏感检测漏报了/误报了，怎么调？

- 看实现：`lib/sensitive_detector.py`
- 误报：把 `safety.deny_sensitive` 关掉同时把 `safety.redact_secrets=true` 走脱敏路径
- 漏报：目前 detector 没暴露 plugin 接口，提 issue / PR 加规则；临时方案是在写入前预处理 content

## 我能在 capture 时不让它自动分类吗？

可以，显式 `--type <type>` 即可。`classify_with_confidence` 只在不传 `--type` 或带 `--auto-classify` 时调。

## CLI 不存在的子命令怎么加？

两条路：

1. **当 CLI 子命令加**（不暴露给模型）：在 `scripts/subcommands/<name>.py` 新增模块 + 在 `memory-cli` 的 `build_parser()` 里加 subparser
2. **当 Claude Code skill 加**（模型可自动触发）：在 `skills/<kebab-name>/SKILL.md` 写 frontmatter（关键是 `description` 里的触发词），`scripts/<verb>.py` 实现 `run_xxx(config, ...)`

模型该不该自动触发，是 skill 与 CLI 子命令的核心区别。治理类操作走 CLI 更安全。

## 记忆能加密吗？

memory plugin 本身**不做端到端加密**。如果你需要：

- OpenViking server 端做静态加密（你的运维问题）
- 客户端加密 → 你要在 capture 之前 / recall 之后自己做加解密；目前没有 hook 暴露到这层（未来可能加 `on_serialize`/`on_deserialize` hook）

## `recall` 返回的 memory 里有过时信息怎么办？

- 单条：`memory-cli forget --memory-id <id> --mode hard`
- 批量：`memory-cli admin prune --older-than 180d`
- 把它修正：`memory-cli merge --memory-id <id> --new "..."`

## 升级 plugin 会破坏我的存量记忆吗？

不会——存量记忆在后端，跟 plugin 版本解耦。但 CLI 接口可能在 minor 版本变（参考 `CHANGELOG.md` 的 Migration 段）。`ov-memory` → `memory-cli` 是最近一次 rename，已经留了 shim 直到 v0.3。

## 我有问题这里没回答

1. 看 `EVAL.md` — 可能已经在 roadmap 里
2. 看 `CHANGELOG.md` — 可能是新版本行为变了
3. 提 issue：https://github.com/kaelinda/agent-marketplace/issues
