---
name: openviking-memory-skills
description: OpenViking Memory Skill Suite — Agent 长期记忆管理完整工作流。包含记忆存储、召回、分类、遗忘、诊断等 12 个子 Skill。
category: devops
---

# OpenViking Memory Skill Suite

Agent 长期记忆工作流管理套件。基于 OpenViking 后端，为 Agent 提供结构化的记忆存储、检索、分类、安全策略和生命周期管理。

## 架构

```
Agent → Memory Skill Suite → Adapter Factory → MCP/HTTP Adapter → OpenViking Server
```

## 12 个子 Skill

### 基础层（Foundation）
| Skill | 说明 | CLI 命令 |
|-------|------|----------|
| `doctor` | 系统诊断检查 | `ov-memory doctor` |
| `recall` | 记忆召回检索 | `ov-memory recall <query>` |
| `capture` | 记忆存储 | `ov-memory capture --content "..."` |
| `commit` | 会话记忆提取 | `ov-memory commit --session-file FILE` |
| `forget` | 记忆遗忘 | `ov-memory forget --memory-id ID` |
| `merge` | 记忆合并更新 | `ov-memory merge --memory-id ID --new "..."` |

### 类型层（Type-specific）
| Skill | 说明 | CLI 命令 |
|-------|------|----------|
| `project-memory` | 项目记忆 | `ov-memory project (list|create|recall|update)` |
| `environment-memory` | 环境记忆 | `ov-memory env (list|capture|update)` |
| `case-memory` | 案例记忆 | `ov-memory case (list|create|recall)` |
| `preference-memory` | 偏好记忆 | `ov-memory pref (list|set|get|delete)` |
| `agent-reflection` | Agent 自省 | `ov-memory reflection (list|add|recall)` |

### 治理层（Governance）
| Skill | 说明 | CLI 命令 |
|-------|------|----------|
| `memory-admin` | 管理后台 | `ov-memory admin (stats|backup|restore|dedupe|prune|audit)` |

### 工具命令（非独立 Skill）
| 命令 | 说明 |
|------|------|
| `ov-memory browse` | 浏览指定 scope 下的记忆列表 |
| `ov-memory read <id>` | 读取单条记忆详情 |

## 快速开始

```bash
# 1. 配置
cp config.example.json config.json
# 编辑 config.json 填入 OpenViking 服务信息

# 2. 诊断
python scripts/ov-memory doctor

# 3. 存储记忆
python scripts/ov-memory capture --content "项目使用 FastAPI + PostgreSQL" --type project

# 4. 召回记忆
python scripts/ov-memory recall "项目技术栈"
```

## 配置

配置文件搜索顺序：
1. `--config` 命令行参数
2. `./config.json`（当前目录）
3. `~/.openviking-memory/config.json`

详见 `config.example.json` 和 `lib/config.py`。

## 目录结构

```
openviking-memory-skills/
├── SKILL.md              # 本文件 — 主入口
├── README.md             # 项目文档
├── BEST_PRACTICES.md     # 最佳实践指南
├── config.example.json   # 配置模板
├── lib/                  # 核心库（10 个模块）
│   ├── config.py         # 配置加载器
│   ├── client.py         # OpenViking HTTP 客户端
│   ├── adapter_protocol.py  # 适配器协议接口
│   ├── adapter_factory.py   # 适配器工厂（可替换后端）
│   ├── http_adapter.py   # HTTP 适配器
│   ├── mcp_adapter.py    # MCP 适配器
│   ├── policy.py         # 策略引擎
│   ├── classifier.py     # 记忆类型分类器
│   ├── sensitive_detector.py # 敏感数据检测
│   ├── conflict_detector.py  # 冲突检测
│   └── formatter.py      # 输出格式化
├── schema/               # JSON Schema 定义
├── scripts/
│   └── ov-memory         # CLI 入口
└── skills/               # 12 个子 Skill
    ├── doctor/
    ├── recall/
    ├── capture/
    ├── commit/
    ├── forget/
    ├── merge/
    ├── project-memory/
    ├── environment-memory/
    ├── case-memory/
    ├── preference-memory/
    ├── agent-reflection/
    └── memory-admin/
```

## 安全策略

- 敏感数据检测：自动识别密码、API密钥、Token、个人信息
- 三级敏感度：`safe` / `warn` / `block`
- `block` 级数据默认拒绝存储，可配置脱敏后存储
- 所有遗忘操作支持 soft/obsolete/hard 三级模式

## 后端可替换

通过 `adapter_factory.py` 实现后端可替换：
1. 实现 `MemoryAdapter` 协议（`lib/adapter_protocol.py`）
2. 注册新适配器：`register_backend("backend_name", "lib.xxx_adapter:XxxAdapter")`
3. 配置中设置 `"backend": "backend_name"`

当前支持：HTTP（直接调用 OpenViking API）、MCP（通过 MCP 协议）

## Scope 动态构建

Scope/namespace 不再硬编码，通过 `scope_template` 配置：
```json
{ "scope_template": "viking://tenants/{tenant}/{type}s/{entity}/memories/" }
```
换后端时只需改 `scope_template`。可通过 `scopes.user_memories` 等显式覆盖。

## 分类器可扩展

分类规则通过 `classifier` 配置段外部化：
- `builtin_rules`: 是否启用内置中英文规则（默认 true）
- `extra_rules`: 自定义规则 `{"type": ["regex1", ...]}`
- `plugin`: 外部分类器 `"module.path:function"`
- `default_type`: 无匹配时默认类型

## 策略可配置

策略通过 `policy` 配置段切换场景：
- `profile`: 当前策略名（default / code_assistant / life_assistant）
- 各 profile 定义 `store_worthy`、`skip_indicators`、`recall_triggers`、`min_content_length`

## 事件钩子系统

通过 `hooks` 配置注入自定义逻辑（`lib/hooks.py`）：
- 事件：`before_store` / `after_store` / `before_recall` / `after_recall` / `on_conflict` 等
- 内置钩子：敏感数据拦截、冲突检测、去重
- 自定义钩子：`hooks.plugins` 列表注册 `"module.path:function"`
