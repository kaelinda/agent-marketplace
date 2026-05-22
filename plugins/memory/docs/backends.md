# 后端选型 (backends)

memory plugin 本身不存数据。**所有数据落在你选的后端**。换后端只改 `config.json` 的 `backend` 字段，调用方代码不动。

## 快速对比

| 维度 | `openviking`（HTTP） | `openviking-mcp`（MCP） | `mem0`（云） |
|---|---|---|---|
| 部署 | 你自己起 OpenViking server | Agent runtime 里已经挂了 OpenViking MCP server | 注册 mem0 拿 API key |
| 调用方式 | `urllib.request` 直连 REST | `subprocess` 调 `mcporter` | `mem0` Python SDK |
| 数据归属 | 你自己 | 你自己 | mem0 云端 |
| 向量检索 | 取决于你 OpenViking 的实现 | 同左 | mem0 自带 |
| 跨设备 | server 在哪你就跨多远 | 取决于 MCP 部署 | 天然跨设备 |
| 离线可用 | ✅ 局域网内 | ✅ 同 runtime | ❌ |
| 适配器规范 | ✅ 已统一 | ✅ 已统一 | ✅ 原生规范 |
| 性能瓶颈 | HTTP RT | subprocess fork | 公网 RT |
| 推荐场景 | 自托管 / 研发 / 隐私敏感 | Claude Code Agent 已经在用 MCP 生态 | 开箱即用 / 个人 / demo |

> 当前所有适配器都已统一返回 `AdapterResponse{ok, data, error, meta}`（v0.2.0 起；以前 HTTP / MCP 返回裸 dict，调用方写过 `result.get("error")` 的需要换成 `result.get("ok") is False`）。

## openviking（HTTP）

### 配置

```json
{
  "backend": "openviking",
  "openviking": {
    "base_url": "http://127.0.0.1:8000",
    "api_key_env": "OPENVIKING_API_KEY",
    "timeout_seconds": 10
  }
}
```

### 必需环境变量

```bash
export OPENVIKING_API_KEY="ov-..."
# 可选：覆盖 config 里的 base_url
export OPENVIKING_URL="https://memory.internal.example/api"
```

### 验证

```bash
memory-cli doctor --mode standard
# 应该看到 ✅ openviking ping
```

### 优点

- 数据 100% 在你手里
- HTTP 易调试（curl / 浏览器 devtools）
- 局域网延迟低

### 注意

- 当前 HTTP adapter **无重试 / 无连接池**；高频写入场景需要你在 OpenViking server 侧扛压
- timeout 默认 10s，慢链路要在 `openviking.timeout_seconds` 调

## openviking-mcp（MCP server）

### 何时选

你已经在 Claude Code / 其它 Agent runtime 里挂了 OpenViking MCP server（`mcporter` 跑得通），不想再起一个 HTTP server。

### 配置

```json
{
  "backend": "openviking-mcp",
  "mcp": {
    "enabled": true,
    "server_name": "openviking",
    "tool_names": {
      "search": "memsearch",
      "read":   "memread",
      "write":  "memwrite",
      "update": "memupdate",
      "delete": "memforget",
      "commit": "memcommit",
      "browse": "membrowse"
    }
  }
}
```

`tool_names` 是 MCP server 里**真实**的 tool 名。OpenViking 上游改名了就得跟。

### 可选环境变量

```bash
export MCPORTER_BIN="/usr/local/bin/mcporter"  # 默认会按 PATH 查找
```

### 安全细节

mcp adapter 的 subprocess 调用走的是**白名单环境**（`MCP_*` 前缀的 var 才会传给子进程）。意味着 `OPENVIKING_API_KEY` / `MEM0_API_KEY` **不会**被泄露到 mcporter 子进程里。这是 v0.2.0 的硬约束，不要在外面改。

### 注意

- 每次调用 fork 一个子进程，QPS 上限取决于你机器；不要在 loop 里高频调用
- subprocess 失败时错误信息可能只剩 stderr 字符串，调试性比 HTTP 弱

## mem0（云）

### 配置

```json
{
  "backend": "mem0",
  "mem0": {
    "api_key_env": "MEM0_API_KEY",
    "version": "v1.1"
  }
}
```

### 必需环境变量

```bash
export MEM0_API_KEY="m0-..."
```

### 优点

- 5 分钟接入，自带语义检索
- 跨设备无需自己做同步
- 服务端管去重 / 索引

### 代价

- 数据在 mem0 那边，隐私边界你自己评估
- 公网 RT，离线不可用
- 计费看 mem0 自己的策略

### 注意

- `mem0.version` 跟 mem0 SDK 走，确认你装的版本和 config 一致
- mem0 的 user / agent 边界用 `identity.user_id` + `identity.agent_id` 映射；不要乱改 `scope_template`，否则 mem0 这边的 namespace 会乱

## 切后端检查清单

1. 改 `config.json` 的 `backend` 字段
2. 给新后端的 API key（环境变量）
3. `memory-cli doctor --mode standard` 必须 PASS
4. `memory-cli doctor --mode full` 跑一次，确认 write→search→read→delete 闭环
5. **不要尝试搬旧记忆过去**：每个 backend 的 scope / ID schema 不一样，搬过去也认不出。需要的话用 `memory-cli admin backup` 在旧后端导出 JSON，在新后端用 `restore` 重新落地——但相似度索引会重建。

## 自己接新后端？

走 `lib/adapter_protocol.py` 的 `MemoryAdapter` 协议 + `AdapterResponse` 返回类型，看 [architecture.md](architecture.md) 的 "新增 adapter" 段。`tests/test_adapter_contract.py` 是任何 adapter 都必须过的合同测试，参考 `tests/fakes/fake_adapter.py` 的实现样例。
