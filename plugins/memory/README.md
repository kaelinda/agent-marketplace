# memory plugin

> 跨会话长期记忆工具集——把对话里的关键事实沉淀下来，让下一次会话能找回它。
>
> Phase 2（v0.2.0）已落地：5 个 Claude Code skill / 2 个 slash command / 3 个适配器（OpenViking / MCP / mem0）/ FakeAdapter 合同测试 / fail-closed identity 校验。
>
> 完整的用户使用文档与跨 Agent 共享场景说明在 Phase 6 / Phase 3 里继续打磨；本 README 只覆盖能让你跑起来的最小集合。

## 这是什么

```
Agent / 用户
   ↓
memory plugin            ← 决定何时记 / 何时召回 / 怎么治理
   ↓
adapter (HTTP / MCP / mem0)
   ↓
后端服务（OpenViking / mem0 cloud / 任意 MCP server）
```

## 6 个 Claude Code skill

| Skill | 触发场景（简版） | CLI 等价 |
|---|---|---|
| `memory-recall`  | 用户说"之前关于 X 的记录" / 任务启动前拉项目上下文 | `memory-cli recall <q>` |
| `memory-capture` | 用户说"记住" / "以后这样" / Agent 识别到值得长期保存 | `memory-cli capture --content "..."` |
| `memory-commit`  | 会话结束 / 周期 checkpoint / 主动沉淀经验 | `memory-cli commit --session-file s.json [--apply]` |
| `memory-doctor`  | 报错排查 / 切换后端 / 验证配置 | `memory-cli doctor [--mode quick\|standard\|full]` |
| `memory-share`   | 把记忆分享给 agent / team / user，撤销共享，看共享给我的（Phase 3） | `memory-cli share <id> --to <kind>:<id>` |
| `memory-admin`   | stats / backup / restore / dedupe / prune / audit | `memory-cli admin <action>` |

详细 frontmatter 与触发词见各 `skills/<name>/SKILL.md`。跨 Agent 共享的完整心智模型 + 双 Agent 端到端例子见 [`docs/cross-agent-sharing.md`](./docs/cross-agent-sharing.md)。

## 3 个 slash command

- `/recall <query>` — 调 `memory-recall`，把召回结果作为结构化记忆块注入当前对话上下文
- `/memory-doctor [mode]` — 调 `memory-doctor`，跑一次诊断检查并展示结果
- `/memory-share share|unshare|subscribed [...]` — 调 `memory-share`，授权 / 撤销 / 看共享给我的

## 安装与最小配置

> 完整的"backend chooser"和分后端启动指引会在 Phase 6 README 重写时补齐。这里只给最小可跑的路径。

### 1. 安装

```
/plugin marketplace add kaelinda/agent-marketplace
/plugin install memory@manji
```

### 2. identity（必须）

`memory plugin` 默认 fail-closed：不显式提供 `OV_USER_ID` 和 `OV_AGENT_ID`，或不在 config 里把 `safety.allow_default_identity` 设为 `true`，`load_config()` 会直接 `raise ConfigError`。这是为了避免多 Agent 同机部署时漏配身份导致共写一个 `default_agent` 命名空间。

最简单的方式：

```bash
export OV_USER_ID="alice"
export OV_AGENT_ID="my-agent-name"
```

### 3. backend（任选其一）

复制 `config.example.json` 到 `~/.openviking-memory/config.json` 或 `./config.json`，按需修改。

| backend | 何时选 | 关键配置 |
|---|---|---|
| `openviking` (HTTP) | 自起 OpenViking server / 已有 OpenViking 部署 | `openviking.base_url` + `OPENVIKING_API_KEY` |
| `openviking-mcp` (MCP) | 已经在 Agent runtime 里挂了 OpenViking MCP server | `mcp.server_name` + `mcp.tool_names` |
| `mem0` (云) | 想要开箱即用的语义检索后端 | `mem0.api_key_env=MEM0_API_KEY` + `MEM0_API_KEY` |

## 第一次跑通

```bash
# 验证配置
memory-cli doctor --mode quick

# 写一条
memory-cli capture --content "项目使用 FastAPI + PostgreSQL，部署在 ECS"

# 找回
memory-cli recall "项目技术栈"
```

## 数据落点

- 配置：`./config.json` → `./.ov-memory/config.json` → `~/.openviking-memory/config.json` → `~/.config/openviking-memory/config.json`（按这个顺序匹配第一个存在的文件）
- 也可以 `OV_MEMORY_CONFIG=/path/to/config.json` 显式指定
- 数据本身存在所选 backend 上，不在本地

## 重要环境变量

| 变量 | 作用 |
|---|---|
| `OV_USER_ID` | identity.user_id 覆盖（必须） |
| `OV_AGENT_ID` | identity.agent_id 覆盖（必须） |
| `OV_TENANT_ID` | identity.tenant_id 覆盖（可选） |
| `OV_TEAM_IDS` | 逗号分隔的 team_id 列表，决定订阅哪些 team scope（Phase 3） |
| `OPENVIKING_API_KEY` | OpenViking HTTP / MCP 后端 API key |
| `OPENVIKING_URL` | OpenViking HTTP base URL（覆盖 config） |
| `MEM0_API_KEY` | mem0 云后端 API key |
| `OV_MEMORY_CONFIG` | 显式 config.json 路径 |
| `MCPORTER_BIN` | MCP 适配器调用的 mcporter 可执行文件路径 |

## 更详细的话

- **现状评估与重构路线图**：`EVAL.md`
- **Phase 2 变更总览**：`CHANGELOG.md`
- **跨 Agent 共享 / 三份 best-practices 合一**：Phase 3 / Phase 6 落地

## License

MIT
