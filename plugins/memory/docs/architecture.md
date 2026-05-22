# 架构 (Architecture)

写给打算给 plugin 加后端 / 加 hook / 改分类器的人。普通使用者不需要。

## 一图概览

```
┌─────────────────────────────────────────────────────────────────────┐
│  Claude Code / 自动化脚本                                            │
│   /recall   /memory-doctor                                          │
│      │           │                                                  │
│      ▼           ▼                                                  │
│  memory-cli  ◄─ skills (frontmatter trigger)                        │
│      │                                                              │
│      ▼                                                              │
│  lib/skill_loader.load_skill_module(...)                            │
│      │                                                              │
│      ├─► memory-recall/run_recall                                   │
│      ├─► memory-capture/run_capture                                 │
│      ├─► memory-commit/run_commit                                   │
│      ├─► memory-doctor/run_doctor                                   │
│      └─► memory-admin/run_admin                                     │
│              │                                                      │
│              ├─► lib/sensitive_detector  (敏感扫描 / 脱敏)          │
│              ├─► lib/classifier          (type 推断)                │
│              ├─► lib/policy              (profile + 触发判定)       │
│              ├─► lib/conflict_detector   (冲突告警)                 │
│              ├─► lib/hooks               (写入前后 hook 调度)       │
│              └─► lib/adapter_factory.get_adapter(config)            │
│                       │                                             │
│                       ▼                                             │
│              ┌────────┴────────┐                                    │
│       HTTPAdapter    MCPAdapter    Mem0Adapter                      │
│              │          │              │                            │
│              ▼          ▼              ▼                            │
│       OpenViking    mcporter      mem0 cloud                        │
│       (REST)       (subprocess)   (SDK)                             │
└─────────────────────────────────────────────────────────────────────┘
```

## 关键 contract：`AdapterResponse`

`lib/adapter_protocol.py` 定义：

```python
@dataclass
class AdapterResponse:
    ok: bool
    data: dict | list | None = None
    error: dict | None = None     # {"code", "message", ...}
    meta: dict | None = None      # {"latency_ms", "raw_id", ...}

    def to_dict(self) -> dict: ...
```

**v0.2.0 起所有 adapter 公共方法的返回都必须是 `AdapterResponse.to_dict()`**。调用方一律检查 `result.get("ok") is False`，不再看 `result.get("error")` 这个 truthy/falsy。

为什么这么严格：在 Phase 2 之前，HTTP 和 MCP adapter 透传裸 dict（`{"error": True, "reason": ...}`），而 Mem0Adapter 用了规范 `{ok, data, ...}`，调用方混在用 → 切后端必然静默错配。是 multi-backend 抽象的根基。

## 写一个新 adapter

1. 实现 `MemoryAdapter` 协议（`lib/adapter_protocol.py`）：

   ```python
   class MyAdapter:
       def __init__(self, config: Config): ...
       def search(self, scope: str, query: str, limit: int) -> dict: ...
       def read(self, memory_id: str) -> dict: ...
       def write(self, scope: str, memory: dict) -> dict: ...
       def update(self, memory_id: str, patch: dict) -> dict: ...
       def delete(self, memory_id: str, mode: str = "soft") -> dict: ...
       def browse(self, scope: str, limit: int) -> dict: ...
       def ping(self) -> dict: ...
   ```

   **每个方法都必须 `return AdapterResponse(...).to_dict()`**。

2. 在 `lib/adapter_factory.py` 加分支：

   ```python
   def get_adapter(config):
       backend = config.get("backend")
       if backend == "my-backend":
           return MyAdapter(config)
       ...
   ```

3. 把新 adapter 接入合同测试。在 `tests/test_adapter_contract.py` 里加一个 fixture，让它跟 `FakeAdapter` 一样跑通整套 contract。

4. 在 `docs/backends.md` 加一节配置说明。

5. **不要绕过** `safety.deny_sensitive` / `safety.allow_cross_user_*`——这些断言在 capture/recall 层完成，不在 adapter 层。adapter 只负责"忠实把这条写到后端 / 读回"。

## scope 系统

scope 是一个 URI 字符串，规则只在 `Config.build_scope()` 里。其它代码**禁止**手拼。

```python
scope = config.build_scope("user", config.user_id)
# 默认模板：viking://tenants/{tenant}/{type}s/{entity}/memories/
```

特殊：`entity_type == "system"` 时模板被改写成 `/system/{entity}/`，去掉 `/memories/` 后缀。这是给 doctor 临时记忆用的隔离区。

## hook 系统

`lib/hooks.py` 暴露事件总线：

- `on_before_write(memory_dict) -> memory_dict | None`：返回 None 阻止写入
- `on_after_write(result) -> None`
- `on_before_recall(query, scope) -> (query, scope) | None`
- `on_after_recall(memories) -> memories`

内置 hook：
- `sensitive_block`（默认开）：写入前敏感检测
- `conflict_detect`（默认开）：写入前同 scope 同 title 冲突告警
- `dedupe`（默认关）：写入前查相似度阈值，命中就 merge 而不是 write

**加自定义 hook 插件**：

```json
{
  "hooks": {
    "plugins": ["plugins/my_org_compliance_hook.py"]
  }
}
```

文件需要暴露一个 `register(bus)` 函数：

```python
def register(bus):
    bus.on("before_write", my_compliance_check)
```

## classifier

`lib/classifier.py` 的 `classify_with_confidence(content) -> (type, confidence)`。两种扩展：

1. **加规则**（不改代码）：
   ```json
   {
     "classifier": {
       "extra_rules": {
         "compliance": ["GDPR", "PIPL", "合规", "审计"]
       }
     }
   }
   ```
2. **接外部分类器插件**：
   ```json
   { "classifier": { "plugin": "my_classifier:classify" } }
   ```
   该 callable 接 `content: str` 返回 `(type: str, confidence: float)`。

## 测试

- `tests/test_adapter_contract.py`：任何 adapter 都必须过的合同测试
- `tests/fakes/fake_adapter.py`：纯内存的 `MemoryAdapter`，调用方测试时挂它就行
- `pytest.ini`：跑测试入口

```bash
cd plugins/memory
python -m pytest -q
```

## 目录结构总览

```
plugins/memory/
├── .claude-plugin/plugin.json     # Claude Code plugin manifest
├── README.md                      # 最小启动文档
├── CHANGELOG.md                   # 版本变更
├── EVAL.md                        # 演化路线图（内部）
├── config.example.json            # 配置示例
├── pytest.ini
├── commands/                      # slash commands
│   ├── recall.md
│   └── memory-doctor.md
├── skills/                        # Claude Code skills（5 个）
│   ├── memory-recall/{SKILL.md, scripts/}
│   ├── memory-capture/{SKILL.md, scripts/}
│   ├── memory-commit/{SKILL.md, scripts/}
│   ├── memory-doctor/{SKILL.md, scripts/}
│   └── memory-admin/{SKILL.md, scripts/}
├── lib/                           # 核心库（adapter / config / classifier / hooks ...）
├── schema/                        # JSON Schema (memory / commit / recall / config)
├── scripts/
│   ├── memory-cli                 # 主 CLI
│   ├── ov-memory                  # v0.2 shim alias (将在 v0.3 移除)
│   └── subcommands/               # CLI 子命令模块（forget / merge / preference / ...）
├── tests/
│   ├── conftest.py
│   ├── fakes/fake_adapter.py
│   └── test_adapter_contract.py
└── docs/                          # 你正在看的目录
    ├── README.md
    ├── getting-started.md
    ├── backends.md
    ├── skills.md
    ├── cli.md
    ├── configuration.md
    ├── troubleshooting.md
    ├── architecture.md  ← 本文
    ├── faq.md
    └── legacy/                    # Phase 1 历史文档，仅供回溯
```

## 设计取舍备忘

| 决策 | 选了 | 没选 | 为什么 |
|---|---|---|---|
| 多后端抽象 | adapter protocol + 工厂 | 后端直接是 driver class | 后端 SDK 接口差距大，统一 contract 比统一 base class 更稳 |
| 错误形状 | `{ok, data, error, meta}` | HTTP-style status code | 跨后端语义统一；调用方代码不分支 |
| identity 默认 | fail-closed | fail-open 用 sentinel | 多 agent 同机部署常见，错配静默成本大 |
| dedupe / prune | 真删 | 墓碑 `status="deleted"` | 墓碑会污染 browse/search 而且没人清扫 |
| MCP 调用 | subprocess(`mcporter`) + 环境白名单 | 内嵌 MCP client | mcporter 已经存在，复用；白名单防 API key 泄露 |
| scope | template + identity 渲染 | 静态 scopes 字典 | 切租户/换后端时不用改代码 |
| skill 数量 | 5 个 Claude Code skill + N 个 CLI 子命令 | 把 12 个全做成 skill | 模型不需要那么多入口；治理类操作走 CLI 更清晰 |

更广的 roadmap → `EVAL.md`。
