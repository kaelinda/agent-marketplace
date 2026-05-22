# 配置 (`config.json` + 环境变量)

memory plugin 的所有运行行为由 `Config` 对象决定。它的来源、合并顺序、安全断言都在这里讲清。

> 源码：`lib/config.py`。本文跟着代码走；改了 default schema 请同步这篇。

## 搜索路径

`load_config(path=None)` 按下面的顺序，找到第一个**存在的**就用：

1. 显式传入的 `--config PATH`（CLI / 调用方）
2. 环境变量 `OV_MEMORY_CONFIG` 指向的路径
3. `./config.json`（当前工作目录）
4. `./.ov-memory/config.json`
5. `~/.openviking-memory/config.json`
6. `~/.config/openviking-memory/config.json`

找不到任何一个 → 直接用 `_DEFAULT_CONFIG`，但 identity 还是默认 sentinel，会被 `_enforce_identity_safety` 拦下。

## 合并顺序

```
_DEFAULT_CONFIG（代码内置）
        │
        ├─► deep_merge( file config )      ← 第一个命中的文件
        │
        ├─► 环境变量覆盖：
        │     OPENVIKING_URL → openviking.base_url
        │     OV_TENANT_ID   → identity.tenant_id
        │     OV_USER_ID     → identity.user_id
        │     OV_AGENT_ID    → identity.agent_id
        │
        └─► _enforce_identity_safety
                │
                ├─ identity 没回到 sentinel？ → 继续返回 Config
                └─ 是 sentinel 且没 opt-in？  → raise ConfigError
```

`_deep_merge` 是真递归 deep merge：嵌套 dict 不会被整个 override，会一层层合并。

## 完整配置结构

```jsonc
{
  // ── 后端选择（"openviking" | "openviking-mcp" | "mem0"）
  "backend": "openviking",

  // ── OpenViking HTTP 后端
  "openviking": {
    "base_url": "http://127.0.0.1:8000",
    "api_key_env": "OPENVIKING_API_KEY",
    "timeout_seconds": 10
  },

  // ── mem0 后端
  "mem0": {
    "api_key_env": "MEM0_API_KEY",
    "version": "v1.1"
  },

  // ── MCP 后端
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
  },

  // ── 身份（fail-closed，必须显式设置）
  "identity": {
    "tenant_id": "default",
    "user_id":   "REPLACE_ME_user_id",
    "agent_id":  "REPLACE_ME_agent_id"
  },

  // ── scope 模板（{tenant}/{type}/{entity} 占位符）
  "scope_template": "viking://tenants/{tenant}/{type}s/{entity}/memories/",

  // ── 命名空间覆盖（除非要硬绑特定 scope，这里通常不填）
  "scopes": {
    "doctor": "viking://tenants/default/system/doctor/"
  },

  // ── 召回参数
  "recall": {
    "default_limit": 6,
    "max_limit":     12,
    "default_level": "L0",   // 检索深度档位
    "allow_l2":      false,  // 是否允许更深一档检索
    "min_score":     0.62    // 低于此 score 直接丢弃
  },

  // ── 写入参数
  "store": {
    "auto_store": false,
    "require_confirmation_for_sensitive": true,
    "dedupe_before_store": true
  },

  // ── 会话 commit 参数
  "commit": {
    "enabled": true,
    "max_memories_per_session": 5,
    "store_cases":       true,
    "store_preferences": true,
    "store_projects":    true
  },

  // ── 安全策略
  "safety": {
    "deny_sensitive":          true,   // 含密码/token 直接拒写
    "allow_cross_user_read":   false,  // 跨 user scope 召回
    "allow_cross_user_write":  false,  // 跨 user scope 写
    "redact_secrets":          true,   // 写之前做脱敏
    "allow_default_identity":  false   // 用 default_user / default_agent → 允许？
  },

  // ── 分类器
  "classifier": {
    "builtin_rules": true,
    "extra_rules":  {},   // 用户自定义 type 规则
    "plugin":       null, // 走第三方 classifier 插件路径
    "default_type": "project"
  },

  // ── 策略 profile（命中哪一组 STORE_WORTHY_INDICATORS 等）
  "policy": {
    "profile": "default",
    "profiles": {
      "default": {},
      "code_assistant": { /* 代码场景特化 */ },
      "life_assistant": { /* 生活场景特化 */ }
    }
  },

  // ── 钩子
  "hooks": {
    "plugins": [],
    "builtin": {
      "sensitive_block": true,
      "conflict_detect": true,
      "dedupe":          false
    }
  }
}
```

## 环境变量

| 变量 | 覆盖的字段 / 用途 | 谁会读 |
|---|---|---|
| `OV_MEMORY_CONFIG`     | 显式指定 config.json 路径 | `load_config()` |
| `OV_TENANT_ID`         | `identity.tenant_id` | `load_config()` |
| `OV_USER_ID`           | `identity.user_id`   | `load_config()` |
| `OV_AGENT_ID`          | `identity.agent_id`  | `load_config()` |
| `OPENVIKING_URL`       | `openviking.base_url` | `load_config()` |
| `OPENVIKING_API_KEY`   | 由 `openviking.api_key_env` 名字指向 | HTTPAdapter |
| `MEM0_API_KEY`         | 由 `mem0.api_key_env` 名字指向 | Mem0Adapter |
| `MCPORTER_BIN`         | mcporter 可执行文件路径 | MCPAdapter |

> 注意：MCP 子进程的环境是**白名单**——只有以 `MCP_` 开头的环境变量会被透传给 `mcporter`。`OPENVIKING_API_KEY` / `MEM0_API_KEY` 不会泄漏。

## Identity 安全规则

**默认 fail-closed**。`load_config()` 完成后会跑 `_enforce_identity_safety(cfg)`：

```python
if cfg.user_id == "default_user" or cfg.agent_id == "default_agent":
    if not cfg.get("safety.allow_default_identity"):
        raise ConfigError(...)
```

**为什么**：多 agent 同机部署时，两个 agent 都漏配 `OV_AGENT_ID` 会共用 `default_agent` 命名空间——既不是隔离也不是有意共享，就是数据污染。Phase 2 把它改成启动失败，捕获在写入前。

**什么时候 opt-in `allow_default_identity=true`**：
- 单元测试 / 一次性脚本
- 跑 demo 想最快看到效果

**不要**在生产 / 持续运行的 agent 上开。

## Scope 是怎么算出来的

`Config.build_scope(entity_type, entity_id)`：

1. 若 `scopes.<override_key>` 显式给了 URI（例如 `scopes.doctor`），直接用它
2. 否则用 `scope_template` 套 `{tenant}/{type}/{entity}` 渲染

预设三个 scope：

```python
config.user_scope    # = build_scope("user", user_id)
config.agent_scope   # = build_scope("agent", agent_id)
config.doctor_scope  # = build_scope("system", "doctor")
```

**system** 类型的 entity 走特殊渲染：`/system/<entity>/`，不带 `/memories/` 后缀。

### 模板举例

```
模板：viking://tenants/{tenant}/{type}s/{entity}/memories/

identity.tenant_id = "default"
identity.user_id   = "alice"
identity.agent_id  = "code-agent"

user_scope   → viking://tenants/default/users/alice/memories/
agent_scope  → viking://tenants/default/agents/code-agent/memories/
doctor_scope → viking://tenants/default/system/doctor/
```

### 换后端时改模板

mem0 / Zep / 其它向量后端有自己的 namespace 格式。改 `scope_template` 即可——不要去硬编码 `lib/` 里的 scope 字符串。

## 配置文件的"最佳大小"

绝大多数用户只要这么几行：

```json
{
  "backend": "mem0",
  "identity": { "tenant_id": "default", "user_id": "alice", "agent_id": "my-agent" },
  "safety":   { "deny_sensitive": true }
}
```

其它字段都有 sane defaults。需要再加，不需要别堆。

## 改完配置之后

```bash
memory-cli doctor --mode quick
```

100ms 内告诉你配置加得对不对、identity 合不合法、对应后端的 API key 有没有。

更广的排查 → [troubleshooting.md](troubleshooting.md)。
