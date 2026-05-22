# 入门：从 0 到第一条记忆

走完这一篇，你会有：identity 配好、后端连通、`doctor` 全绿、写过 1 条、召回回 1 条。预计 10 分钟。

## 0. 前置

- Python 3.10+
- `memory-cli` 在 `PATH` 里能找到（plugin 安装后会被 Claude Code 注册；CLI 自动化用的话直接调 `plugins/memory/scripts/memory-cli`）
- 一个后端：选一个，本文以 **mem0 云** 为例（最省事），其它两个在 [backends.md](backends.md) 里展开。

## 1. 装

```text
/plugin marketplace add kaelinda/agent-marketplace
/plugin install memory@manji
```

> 验证：`memory-cli --help` 应该打印子命令列表。

## 2. 配 identity（**必做**，否则启动就 raise）

memory plugin 是 fail-closed 的。`identity.user_id` / `identity.agent_id` 留在默认的 `default_user` / `default_agent`，`load_config()` 会直接 `ConfigError`。

最快的做法：

```bash
export OV_USER_ID="alice"             # 换成你的真实 user id
export OV_AGENT_ID="my-coding-agent"  # 换成这个 agent 的稳定名
# 可选
export OV_TENANT_ID="default"         # 多租户场景才需要改
```

或者写进 `~/.openviking-memory/config.json`：

```json
{ "identity": { "tenant_id": "default", "user_id": "alice", "agent_id": "my-coding-agent" } }
```

> **为什么这么严**：多 agent 同机部署时，两个 agent 都漏配 `OV_AGENT_ID`，结果都落进 `default_agent` 命名空间——既不是隔离也不是有意共享，纯数据污染。Phase 2 起改成启动失败。详见 `lib/config.py` 注释与 EVAL.md §2.4。

## 3. 选后端 + 给 API key

复制 `config.example.json` 到 `~/.openviking-memory/config.json`（plugin 会按 [配置搜索路径](configuration.md#搜索路径) 找它），然后：

### mem0 云后端

```json
{
  "backend": "mem0",
  "mem0": { "api_key_env": "MEM0_API_KEY", "version": "v1.1" }
}
```

```bash
export MEM0_API_KEY="m0-..."
```

### OpenViking HTTP（自部署）

```json
{
  "backend": "openviking",
  "openviking": { "base_url": "http://127.0.0.1:8000", "api_key_env": "OPENVIKING_API_KEY" }
}
```

```bash
export OPENVIKING_API_KEY="ov-..."
```

### OpenViking MCP（Agent runtime 已挂了 OpenViking MCP server）

```json
{
  "backend": "openviking-mcp",
  "mcp": { "enabled": true, "server_name": "openviking" }
}
```

> 三种后端怎么选 / 优劣分别是什么 → [backends.md](backends.md)。

## 4. 体检

```bash
memory-cli doctor --mode quick      # 100ms，本地配置体检
memory-cli doctor --mode standard   # 1–3s，加上后端 ping
memory-cli doctor --mode full       # 5–15s，端到端 write→read→delete
```

期望：`PASS`。如果是 `PASS_WITH_WARNINGS`，warnings 列出来的是软问题（例如 `api_key_env` 指向的环境变量没设但还没真用到）。如果是 `FAIL`，看 errors 第一条——大多数情况是 identity 没配或者后端没起。

> Claude Code 里也可以直接 `/memory-doctor [quick|standard|full]`。

## 5. 写一条，再找回来

```bash
memory-cli capture --content "项目使用 FastAPI + PostgreSQL，部署在 ECS" --auto-classify
# 输出：Auto-classified as: environment (confidence: 0.83)
#       Memory stored: [m_...] (environment) 项目使用 FastAPI + ...

memory-cli recall "项目技术栈"
# 输出：
# [Relevant OpenViking Memory]
# - environment: 项目使用 FastAPI + PostgreSQL，部署在 ECS
# [/Relevant OpenViking Memory]
```

如果 `recall` 给你 `(no relevant memories found)`：
- `recall.min_score`（默认 0.62）可能把你刚写的那条卡掉了——把 query 写得更接近原文，或者临时降到 0.5 复测。
- 后端是 mem0 / OpenViking 异步索引的情况下，刚写完几秒内 `recall` 可能还没看到。
- 终极手段：`memory-cli browse` 看 scope 里到底有没有这条。

## 6. 下一步

- **让 Claude Code 自动用**：[skills.md](skills.md) 解释 5 个 skill 各自的触发条件 / 何时不要触发。
- **CLI 全集**：[cli.md](cli.md)。
- **接入团队 / 多 agent**：[configuration.md](configuration.md) 的 scope 章节 + [faq.md](faq.md) 的"我能让两个 agent 共享一份记忆吗"。
- **写出错了 / 找不回**：[troubleshooting.md](troubleshooting.md)。
