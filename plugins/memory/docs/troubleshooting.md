# 排障 (Troubleshooting)

排障第一步**永远**是：

```bash
memory-cli doctor --mode standard   # 或 full
```

`doctor` 已经覆盖了 80% 的"我配置错了"。下面列剩下 20%。

## 怎么读 doctor 输出

`doctor` 返回的不是字符串，是结构化 dict，CLI 帮你格式化了。关键字段：

| 字段 | 含义 |
|---|---|
| `result` | `PASS` / `PASS_WITH_WARNINGS` / `FAIL` |
| `meta`   | mode、endpoint、tenant、user、agent |
| `checks` | 每项检查 `pass / warn / fail / skip` |
| `warnings` | 软问题列表 |
| `errors`   | 硬错误列表（FAIL 看这个） |

直接的修复路径：**`FAIL` → 读 errors[0] → 按下面 §1 / §2 / §3 找对应症状**。

## 1. 启动直接 ConfigError

### 症状
```
ConfigError: Identity is using the default sentinel value(s) for
identity.user_id, identity.agent_id. Set the corresponding env var(s)
(OV_USER_ID, OV_AGENT_ID) ...
```

### 原因
你没设 `identity`，留在了默认的 `default_user` / `default_agent`。memory plugin 是 fail-closed 的，详见 [configuration.md#identity-安全规则](configuration.md#identity-安全规则)。

### 修复
任选其一：

```bash
# 1) 环境变量
export OV_USER_ID="alice"
export OV_AGENT_ID="my-agent"

# 2) 写进 config
#    ~/.openviking-memory/config.json
{ "identity": { "user_id": "alice", "agent_id": "my-agent" } }

# 3) 测试/demo 才能用：opt-in 占位 identity
{ "safety": { "allow_default_identity": true } }
```

## 2. doctor FAIL 在后端 ping

### 症状（HTTP 后端）
```
❌ openviking_ping: connection refused → http://127.0.0.1:8000
```

### 检查清单
1. OpenViking server 真的在跑？`curl http://127.0.0.1:8000/health` 看一下
2. `OPENVIKING_API_KEY` 在当前 shell 设了吗？`echo $OPENVIKING_API_KEY`
3. `openviking.base_url` 写的是对的（有没有写 `https` 时只起 `http`）
4. `openviking.timeout_seconds` 太小（默认 10s，慢链路可能不够）

### 症状（MCP 后端）
```
❌ mcp_invoke: mcporter not found in PATH
```

### 检查清单
1. `which mcporter` 真的有这个二进制？没装就装
2. 或者 `export MCPORTER_BIN=/path/to/mcporter`
3. `mcp.server_name` 跟你 Agent runtime 里挂的 MCP server 名字一致吗

### 症状（mem0 后端）
```
❌ mem0_ping: Unauthorized
```

### 检查清单
1. `MEM0_API_KEY` 没设 / 设错
2. mem0 SDK 版本与 `mem0.version` 不一致

## 3. capture 报错

### 症状 A：被敏感检测拦
```
Error: write blocked — content contains sensitive token
```

#### 原因
内容里命中了密码 / API key / 邮箱 / 身份证号等模式。

#### 修复
- 把敏感数据从内容里删掉再写
- 或者把 `safety.deny_sensitive` 改 `false` 同时让 `safety.redact_secrets=true` 走脱敏路径（仍可能被拒，如果脱敏后依然命中）
- 真要存 secrets 不要走 memory plugin，请用专门的 secret manager

### 症状 B：后端写入失败
```
Error: backend write failed — 503 Service Unavailable
```

#### 原因
后端临时不可用 / 鉴权过期。

#### 修复
1. `memory-cli doctor --mode full` 跑一次确认后端整体是否可用
2. HTTP adapter 当前**无自动重试**——稍后重试，或在 OpenViking server 侧排查

## 4. recall 召不出

### 现象
刚 `capture` 完，立刻 `recall` 拿不到 / 拿到 `(no relevant memories found)`。

### 排查顺序

1. **min_score 卡掉了**：默认 0.62 偏严。临时调低看：
   ```json
   { "recall": { "min_score": 0.5 } }
   ```
2. **type 过滤错位**：`recall --type project` 但写的时候是 `environment`，自然召不出
3. **后端异步索引未完成**：mem0 / OpenViking 实现可能要几秒才能索引到，再 `recall` 试一次
4. **scope 不对**：直接 `memory-cli browse --scope <user_scope>` 看到底有没有这条
5. **真没写进去**：`memory-cli read <id>` 用上次 capture 返回的 ID 看

## 5. dedupe / prune 删多了

### 现象
跑完 `admin dedupe`，发现少了不该少的记忆。

### 原因
- v0.2.0 起 `dedupe` / `prune` 都是**真删**（adapter.delete），不是打 `status="deleted"` 墓碑
- 同 `type+title` 只留 updated_at 最新一条，其它都没了

### 恢复
- 如果跑 `dedupe` / `prune` 前**没 backup**，没法恢复
- 跑前的标准动作：
  ```bash
  memory-cli admin backup --output ~/backups/before-dedupe.json
  memory-cli admin dedupe
  # 觉得不对就：
  memory-cli admin restore --file ~/backups/before-dedupe.json
  ```

## 6. 两个 Agent 互相看不到对方的记忆

### 现象
agent A capture 了一条，agent B recall 不到。

### 原因
**这是 by-design**：每个 agent 默认只看自己的 `agent_scope`，user 也只看自己的 `user_scope`。

### 想共享？
当前 v0.2.0 的 sharing 抽象还在 Phase 3。短期解法：

1. 显式 `--scope` 写到一个共享 URI，例如：
   ```bash
   memory-cli capture --content "..." --scope viking://tenants/default/shared/team-a/
   ```
2. `recall` 时也指定相同 scope（注意：recall 当前 CLI 没暴露 `--scope`，需要靠 browse / read）
3. `safety.allow_cross_user_read=true` 解锁跨 user 读（默认关）

更通用的"team / workspace / shared"一等抽象在 Phase 3 落地后会取代这套手动 scope。

## 7. config.json 改了不生效

### 检查
1. 你改的是哪一份？plugin 按 [搜索路径](configuration.md#搜索路径) 找**第一个**存在的文件就用，后面的都被忽略。`ls ./config.json ./.ov-memory/config.json ~/.openviking-memory/config.json ~/.config/openviking-memory/config.json` 看清谁先匹配。
2. JSON 语法是不是合法？`python -m json.tool ~/.openviking-memory/config.json`
3. 环境变量是不是覆盖了？`OV_USER_ID` / `OV_AGENT_ID` / `OPENVIKING_URL` 优先级高于 config 文件。

## 8. 还没解决？

按这个顺序提供给排查者：

```bash
memory-cli --version              # 如果有的话
memory-cli doctor --mode full     # 完整体检输出
cat ~/.openviking-memory/config.json   # 脱敏后
env | grep -E "^(OV_|OPENVIKING_|MEM0_|MCPORTER_)"   # 相关环境变量
```

加上你**复现失败的最小命令序列**。
