# memory plugin — 现状评估与生产化重构计划

> 本文档由 Ralph Loop iter1 产出，作为后续迭代的"地图"。每个迭代的工作以此为锚点推进。

---

## 0. TL;DR

`plugins/memory/skills/` 已经有 ~6000 行 Python + Markdown 的实现（OpenViking Memory Skill Suite）。架构思路是对的（adapter 协议 + hook 系统 + 策略引擎 + 多后端），但**目前不能直接作为 Claude Code 插件加载**，且**没有跨 Agent 记忆共享机制**——这正是用户的核心诉求。

**3 大问题：**
1. 🔴 **目录结构不符合 Claude Code plugin 规范**（SKILL.md 路径错位、`skills/skills/` 双层嵌套）
2. 🔴 **缺少跨 Agent 共享的一等抽象**（scope 全是隔离粒度，没有 `team / shared / workspace` 概念）
3. 🟡 **生产级硬伤**：无测试、HTTP 无重试、MCP 走 subprocess、错误格式三套适配器各异、文档重复 1700 行

**推荐路径：**保留现有大部分代码（改名 + 结构整改），新增 sharing 层，补测试，瘦身文档。**不重写**，**渐进式迭代**。

---

## 1. 现状盘点

### 1.1 文件清单（49 个文件，~6000 行）

```
plugins/memory/
├── .claude-plugin/plugin.json          (8行)   ← 之前 iter0 占位
├── README.md                           (35行)  ← 之前 iter0 占位
└── skills/                             ← 整个目录是一个"内部包"
    ├── SKILL.md                        (156行)  ⚠️ 路径错位
    ├── README.md                       (235行)
    ├── BEST_PRACTICES.md               (481行)
    ├── SUBSKILL_BEST_PRACTICES.md      (805行) ⚠️ 与 BEST_PRACTICES 重复
    ├── config.example.json             (56行)
    ├── docs/
    │   ├── best-practices.md           (383行) ⚠️ 三份 best-practices
    │   └── sub-skills-guide.md         (361行)
    ├── lib/                            ← 核心库（共 11 个模块，2273 行）
    │   ├── adapter_protocol.py         (147行) ✅ 设计良好
    │   ├── adapter_factory.py          (106行) ✅ 工厂模式 OK
    │   ├── config.py                   (322行) ✅
    │   ├── client.py                   (127行) HTTP 客户端，但无重试/池化
    │   ├── http_adapter.py             (44行)  ⚠️ 不返回 AdapterResponse
    │   ├── mcp_adapter.py              (120行) ⚠️ subprocess 调用
    │   ├── mem0_adapter.py             (456行) ✅ 唯一规范返回格式的
    │   ├── classifier.py               (157行)
    │   ├── conflict_detector.py        (163行)
    │   ├── sensitive_detector.py       (90行)
    │   ├── policy.py                   (118行)
    │   ├── formatter.py                (152行)
    │   └── hooks.py                    (233行) ✅ 事件系统设计 OK
    ├── schema/                         ← 4 个 JSON Schema（未在代码中校验）
    ├── scripts/ov-memory               (375行) Python CLI 入口
    └── skills/                         ⚠️ 双层 skills/skills/
        ├── doctor/SKILL.md + scripts/doctor.py
        ├── recall/...
        ├── capture/...
        ├── commit/...
        ├── forget/...
        ├── merge/...
        ├── project-memory/...
        ├── environment-memory/...
        ├── case-memory/...
        ├── preference-memory/...
        ├── agent-reflection/...
        └── memory-admin/...
```

### 1.2 三个适配器对比

| 维度 | HTTPAdapter | MCPAdapter | Mem0Adapter |
| --- | --- | --- | --- |
| 行数 | 44 | 120 | 456 |
| 调用方式 | `urllib.request` 直连 OpenViking REST | `subprocess` 调 `mcporter` CLI | `mem0` Python SDK |
| 返回格式 | 透传 OVClient 的 raw dict（含 `error: True` 标志） | 透传 mcporter 输出（也是 raw dict） | 规范的 `{ok, data, meta}` ✅ |
| 错误处理 | 透传 HTTP 错误码 | subprocess 失败时只有 stderr 字符串 | try/except 包了所有公共方法 ✅ |
| 重试 | ❌ 无 | ❌ 无 | ❌ 无（依赖 SDK） |
| 连接复用 | ❌ 每次新建 urlopen | ❌ 每次 fork 一个进程 | ❌ |
| 异步 | ❌ 同步 | ❌ 同步 | ❌ 同步 |
| 健康检查 | `OVClient.ping()` 走 `/health` | `_call_tool("memsearch", {"query":"ping"})` | `ping()` 走 trivial search |

→ **三个适配器返回格式不统一是最大的契约破坏**。`adapter_protocol.py` 定义了 `AdapterResponse`，但只有 mem0 真正用了。

### 1.3 12 个 sub-skill 的本质

它们**不是** Claude Code 意义上的 Skill（不会被 Claude 自动激活）；它们是 ov-memory CLI 内部的子命令模块，每个目录里有一份 SKILL.md（描述用法）+ 一份 Python 脚本（实现）。Python 脚本通过 `import_skill()` 在 ov-memory 主入口里动态加载。

---

## 2. 核心问题分类

### 🔴 Critical：Claude Code 插件合规性

| # | 问题 | 影响 |
| --- | --- | --- |
| C1 | `plugins/memory/skills/SKILL.md` 路径错位 — 应在 `plugins/memory/skills/<skill-name>/SKILL.md` | Claude Code 不会识别为 skill |
| C2 | 12 个 sub-skill 在 `plugins/memory/skills/skills/<name>/SKILL.md`（多了一层 `skills/`） | 同上，全部识别失败 |
| C3 | 顶层 SKILL.md frontmatter `name: openviking-memory-skills` 与目录名 `memory` / 与 plugin 名 `memory` 不一致 | 加载冲突 |
| C4 | README 第 233 行 `License: Private` 与 plugin.json 的 `MIT` 矛盾 | 开源市场不能放 |
| C5 | 不暴露任何 slash command；所有交互都靠 Python CLI（`scripts/ov-memory`） | 用户用不了 `/recall ...` 这种 |

### 🔴 Critical：Cross-Agent 共享缺失

用户的核心诉求："**适配不同的记忆管理工具，可以跨 Agent 实现记忆共享**"。

现状代码：
- `scope_template = "viking://tenants/{tenant}/{type}s/{entity}/memories/"` — `{type}` 只取 `user|agent|system`，没有 `team|shared|workspace`
- `safety` 配置默认 `allow_cross_user_read: false`、`allow_cross_user_write: false`
- 没有 ACL / 权限模型
- 没有 "把 memory X 共享给 agent Y" 的 API
- README 提到的 `viking://tenants/{t}/resources/` scope 在代码里**完全没引用**

→ 这块是**全新功能**，需要从抽象层（scope template）一直加到 skill 层（`/memory-share`）。

### 🟡 Important：生产级硬伤

| # | 问题 | 修复成本 |
| --- | --- | --- |
| P1 | 三个 adapter 返回格式不统一（HTTPAdapter 透传 raw dict） | 中 |
| P2 | `OVClient` 用 urllib 没有重试、没有 keep-alive、没有连接池 | 中 |
| P3 | `MCPAdapter` 走 `subprocess` 调 mcporter，每次 fork 新进程 | 高（需要 native MCP client） |
| P4 | 完全没有测试（单元 / 集成都没有） | 中 |
| P5 | JSON Schema 文件存在但代码里**没有任何 validate 调用** | 低 |
| P6 | `scripts/ov-memory` 用 `importlib.util` 动态加载 sub-skill 脚本，路径硬编码 | 低 |
| P7 | `mem0_adapter.close()` 调用 `mem0.close()`，但 mem0 SDK 不一定有这个方法（已有 try/except） | 低 |
| P8 | `Identity` 默认值是 `default_user`/`default_agent`，生产环境会用错 user 写错 scope | 低（加校验） |
| P9 | 三份 best-practices 文档（共 1700 行）内容大量重复 | 低 |
| P10 | 错误日志用 `print(... file=sys.stderr)`，没有结构化日志 | 中 |

### 🟢 Nice-to-have

- `Mem0Adapter.browse` 本地切片模拟 offset，大数据集会慢（代码里已有 TODO 注释）
- `adapter_factory.get_adapter` 用 `inspect.signature` 推断 kwargs，换签名就崩
- 没有 metrics / 计时统计（只有 `meta.elapsed_ms`）

---

## 3. 重构计划（分迭代）

### Phase 1 — 评估（iter1，本迭代）✅
- 读完所有核心代码
- 写本评估文档

### Phase 2 — 结构整改（iter2）
**目标：让插件能被 Claude Code 正确加载。**

新结构：
```
plugins/memory/
├── .claude-plugin/plugin.json          (升 0.2.0)
├── README.md                           (重写，简洁版)
├── CHANGELOG.md                        (新)
├── EVAL.md                             (本文件)
├── skills/                             (Claude Code 一等公民 skill 列表)
│   ├── memory-recall/SKILL.md          (← 从 skills/skills/recall/ 提升)
│   ├── memory-capture/SKILL.md         (← 从 skills/skills/capture/ 提升)
│   ├── memory-commit/SKILL.md          (← 从 skills/skills/commit/ 提升)
│   ├── memory-doctor/SKILL.md          (← 从 skills/skills/doctor/ 提升)
│   └── memory-admin/SKILL.md           (← 从 skills/skills/memory-admin/ 提升)
├── commands/                           (新：暴露 slash commands)
│   ├── recall.md
│   └── memory-doctor.md
├── lib/                                (从 skills/lib/ 上提到 plugin 根)
├── schema/                             (从 skills/schema/ 上提到 plugin 根)
├── scripts/
│   └── memory-cli                      (重命名 ov-memory，去 OpenViking 品牌)
├── tests/                              (新)
└── docs/
    └── BEST_PRACTICES.md               (合并三份重复文档)
```

**保留**但**不再作为 Claude Code skill**：project-memory、environment-memory、case-memory、preference-memory、agent-reflection、forget、merge、browse、read。这些都是 CLI 子命令而非"该自动激活的能力"。Claude Code skill 数量收敛到 5 个核心。

**变更要点：**
- 把 `skills/lib/` `skills/scripts/` `skills/schema/` 上提到 plugin 根
- 把 `skills/skills/<name>/` 下的 SKILL.md + scripts 提升到 `skills/<name>/`，**合并主 SKILL.md 中的描述**到对应 skill
- 删除根 SKILL.md（Claude Code skill 是文件夹粒度，不是包粒度）
- 修 path 引用（ov-memory 里的 `SKILLS_DIR`、`sys.path.insert` 等）
- 删旧的双层 skills/，去掉 OpenViking 内部品牌
- 改 `License` 到 MIT
- 重写 README 用 Claude Code 用户视角

### Phase 3 — Cross-Agent 共享层（iter3）
**目标：实现"多个 Agent 读写同一份记忆"的核心场景。**

**抽象扩展：**
- 新 entity_type：`team` / `workspace`
- 新 scope template 占位符：`{shared_id}`
- 新 scope 形态：`viking://tenants/{t}/teams/{team_id}/memories/`
- 新 ACL 字段（在 memory.metadata 里）：`shared_with: [agent_id, ...]`、`visibility: private|team|public`

**新 lib/sharing.py：**
```python
class SharingManager:
    def share(self, memory_id, target_type, target_id, permission="read") -> AdapterResponse
    def unshare(self, memory_id, target_id) -> AdapterResponse
    def list_shares(self, memory_id) -> AdapterResponse
    def list_subscribed(self, agent_id) -> AdapterResponse  # 我能读到哪些 shared memory
    def can_access(self, memory, agent_id, op="read") -> bool  # ACL 判定
```

**新 skill：`memory-share`**
- 描述："当用户说'把这条记忆分享给 X agent'时激活"
- 命令：`memory-cli share <memory-id> --to <agent-id|team:<id>> [--read|--write]`

**Adapter 层适配：**
- mem0 用 metadata.shared_with（mem0 支持 metadata filter）
- HTTP/MCP 走 OpenViking 服务端的 ACL 字段
- 默认 search 时同时查 own scope + 已订阅的 shared scope（可由配置关闭）

### Phase 4 — 生产硬化（iter4）
- HTTPAdapter 加重试（指数退避，3 次）
- HTTP 客户端改用 `http.client.HTTPConnection` 复用连接（仍然零依赖）
- 所有 adapter 强制返回 `AdapterResponse`（HTTPAdapter / MCPAdapter 包一层）
- MCPAdapter 错误格式与其他统一
- Schema validation 在 capture/write 路径上启用（jsonschema 可选依赖，缺失则跳过）
- 加结构化日志（标准库 `logging`）

### Phase 5 — 测试（iter5）
- `tests/test_adapter_protocol.py`：所有 adapter 共用合同测试（用 fake adapter）
- `tests/test_scope.py`：scope template 解析、跨 entity_type
- `tests/test_sharing.py`：ACL 判定、共享/取消共享流程
- `tests/test_classifier.py`、`test_sensitive.py`、`test_policy.py`
- `tests/test_hooks.py`：事件触发顺序、blocked 短路
- 目标：核心 lib 覆盖率 ≥80%

### Phase 6 — 文档瘦身（iter6）
- 三份 best-practices 合一份 → `docs/BEST_PRACTICES.md`
- 重写 plugin README（用户视角："如何在 Claude Code 里用 memory 插件"）
- 写 `docs/ARCHITECTURE.md`（开发者视角）
- 写 `docs/CROSS_AGENT_SHARING.md`（专门讲共享场景）

### Phase 7 — 收尾（iter7）
- 在 marketplace.json 注册 memory plugin（升 0.2.0 后正式发布）
- 根 README 插件目录补一行
- 跑一次端到端：在另一仓库 install 插件、capture 一条、recall 一条
- 输出 `<promise>DONE</promise>`

---

## 4. 风险与缓解

| 风险 | 缓解 |
| --- | --- |
| 重构导致 import 路径全断 | Phase 2 一口气改，所有 `sys.path.insert` 用相对计算后的根 |
| Cross-agent 共享的 ACL 模型设计偏 | 先做最简模型（owner + shared_with list），不做 RBAC |
| Mem0 / OpenViking 后端能力不一致 | 共享层先在 metadata 里做客户端 ACL，服务端能力作为 enhancement |
| 没有测试基础设施 | Phase 5 用 pytest + fake adapter，不引入额外依赖 |
| 文档量太大（每个 phase 都要改） | 不在每个 phase 改 README，等 Phase 6 一次性重写 |

---

## 5. 取舍声明

- **不做** RBAC / 多角色 / 审计日志（超出"个人 + 小团队 Agent"场景）
- **不做** 向量检索本地实现（依赖后端能力）
- **不做** 同步异步双 API（保持同步，简单）
- **不引入** 第三方依赖（lib/ 保持 stdlib only；mem0 SDK 是 lazy import）
- **暂不做** Web UI / TUI 浏览器（CLI 已够）

---

## 6. 完成定义（Definition of Done）

iter7 输出 `<promise>DONE</promise>` 当且仅当全部满足：

- [ ] `plugins/memory/skills/<skill>/SKILL.md` 至少 5 个，目录扁平合规
- [ ] `marketplace.json` 已注册 memory plugin，version ≥ 0.2.0
- [ ] `lib/` 在 plugin 根，所有 import 路径正确
- [ ] 至少一个 adapter（mem0 或 fake）能跑通 capture → recall 闭环
- [ ] cross-agent 共享：能 share 一条 memory，另一个 agent_id 配置下 recall 能拿到
- [ ] `tests/` 至少 ≥10 个测试，pytest 全绿
- [ ] 三份 best-practices 合并成一份
- [ ] README 重写过，含安装、cross-agent 用法、配置示例
- [ ] LICENSE 与 plugin.json 一致

---

## 7. 当前迭代输出

- 本评估文档（`plugins/memory/EVAL.md`）
- 任务列表里 task #15「按计划重构与实现」分解成 Phase 2-7 子任务
- commit & push 后进入 iter2

下一迭代（iter2）从 Phase 2 开始：**结构整改**。
