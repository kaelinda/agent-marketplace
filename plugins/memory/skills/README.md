# OpenViking Memory Skill Suite

面向 AI Agent 的长期记忆工作流套件。在 MCP 工具层之上，定义 Agent 什么时候记忆、如何召回、如何沉淀、如何更新、如何遗忘，以及如何诊断和治理记忆系统。

## 它是什么

```
Agent / 用户
    ↓
OpenViking Memory Skill Suite   ← 本项目：记忆工作流 + 安全策略
    ↓
MCP Tools / HTTP API            ← 调用层
    ↓
OpenViking Server               ← 记忆存储与检索后端
```

**不是**替代 OpenViking，**不是**重新实现向量数据库。它是 Agent 和 OpenViking 之间的「记忆操作系统」。

## 核心能力

| 子 Skill | 一句话 |
|----------|--------|
| `doctor` | 检查配置、连接性、权限、读写闭环 |
| `recall` | 根据当前任务召回相关长期记忆 |
| `capture` | 将值得长期保存的信息写入 OpenViking |
| `merge` | 更新合并已有记忆，避免冲突和重复 |
| `forget` | 删除、废弃或屏蔽指定记忆 |
| `commit` | 从一段会话中沉淀长期记忆候选 |
| `project-memory` | 管理长期项目上下文 |
| `environment-memory` | 管理用户技术环境 |
| `case-memory` | 管理问题排查案例 |
| `preference-memory` | 管理用户偏好 |
| `agent-reflection` | 管理 Agent 自身经验 |
| `memory-admin` | 备份、迁移、去重、统计、清理 |

## 目录结构

```
openviking-memory-skills/
├── SKILL.md                    # 主 Skill 定义（Agent 入口）
├── README.md                   # 本文件
├── config.example.json         # 配置示例
├── scripts/
│   └── ov-memory               # CLI 统一入口
├── skills/
│   ├── doctor/                 # 系统诊断
│   ├── recall/                 # 记忆召回
│   ├── capture/                # 记忆写入
│   ├── merge/                  # 记忆合并
│   ├── forget/                 # 记忆删除
│   ├── commit/                 # 会话沉淀
│   ├── project-memory/         # 项目记忆
│   ├── environment-memory/     # 环境记忆
│   ├── case-memory/            # 案例记忆
│   ├── preference-memory/      # 偏好记忆
│   ├── agent-reflection/       # Agent 经验
│   └── memory-admin/           # 管理工具
├── lib/
│   ├── config.py               # 配置加载
│   ├── client.py               # HTTP 客户端
│   ├── mcp_adapter.py          # MCP 适配器
│   ├── http_adapter.py         # HTTP 适配器
│   ├── policy.py               # 策略引擎
│   ├── classifier.py           # 类型自动分类
│   ├── sensitive_detector.py   # 敏感信息检测
│   ├── conflict_detector.py    # 冲突检测
│   └── formatter.py            # 输出格式化
└── schema/
    ├── memory.schema.json
    ├── skill-config.schema.json
    ├── doctor-result.schema.json
    └── commit-candidate.schema.json
```

## 快速开始

### 1. 配置

```bash
cp config.example.json config.json
# 编辑 config.json，填入你的 OpenViking 地址和身份信息
```

或通过环境变量：

```bash
export OPENVIKING_API_KEY="your-key"
export OPENVIKING_URL="http://your-server:8000"
export OV_USER_ID="your_user_id"
```

### 2. 诊断

```bash
ov-memory doctor --mode standard
```

输出示例：

```
OpenViking Memory Doctor
Mode: standard
Endpoint: http://127.0.0.1:8000
Tenant: default
User: zhouzuosong
Agent: hermes

✅ Config loaded
✅ API key loaded from OPENVIKING_API_KEY
✅ OpenViking service reachable: 38ms
✅ MCP server detected: openviking
✅ Required tools found: memsearch, memread, memwrite, memforget, memcommit
✅ User memory scope readable
✅ User memory scope writable
✅ Doctor write → search → read → delete loop passed

Result: PASS
```

### 3. 写入记忆

```bash
# 明确写入
ov-memory capture \
  --type environment \
  --title "ECS 生产服务器" \
  --content "CentOS 8, Nginx 路径 /www/server/nginx, Docker Compose 部署"

# 自动分类
ov-memory capture \
  --auto-classify \
  --content "以后回答 Swift 问题时尽量给完整可运行的代码"
```

### 4. 召回记忆

```bash
ov-memory recall "继续完善 OpenViking Memory Skill"
```

输出（可直接注入 Agent 上下文）：

```
[Relevant OpenViking Memory]
- Project: User is designing an OpenViking Memory Skill Suite with doctor, recall, capture, merge, forget and commit capabilities.
- Decision: Doctor should check config, MCP tools, service connectivity, namespace, and read/write loop.
- Preference: User prefers Chinese explanations with concrete implementation plans.
[/Relevant OpenViking Memory]
```

### 5. 会话沉淀

```bash
ov-memory commit --session-file ./session.json --apply
```

自动提取本次会话中值得长期保存的项目背景、技术决策、环境信息、问题案例，生成候选记忆供确认后写入。

## 记忆类型

| 类型 | 说明 | 示例 |
|------|------|------|
| `profile` | 用户长期背景 | 用户是 iOS 开发者 |
| `preference` | 输出偏好 | 喜欢中文、完整代码、可复制命令 |
| `project` | 长期项目 | MagicBroom、OpenViking Memory Skill |
| `environment` | 技术环境 | CentOS 8、Nginx 路径、Docker Compose |
| `case` | 问题排查案例 | Nginx 502、TLS 握手失败 |
| `decision` | 已确认决策 | 第一版包含 doctor 模块 |
| `agent_reflection` | Agent 经验 | 遇到 TLS 问题先检查代理环境变量 |

## 安全策略

**默认行为：**

- `auto_store: false` — 不自动存储，需要明确触发
- `deny_sensitive: true` — 拒绝 API Key、密码、Token 等入库
- `redact_secrets: true` — 检测到敏感信息自动脱敏
- `allow_cross_user_read: false` — 不读取其他用户记忆
- `allow_cross_user_write: false` — 不写入其他用户记忆

**敏感信息处理：**

```
原文：  OPENAI_API_KEY=sk-xxxxxxxx
入库：  OPENAI_API_KEY=[REDACTED]
```

## 记忆治理

| 问题 | 处理方式 |
|------|----------|
| 重复记忆 | 写入前搜索相似记忆，相似则 merge |
| 过期记忆 | 状态标记 `obsolete`，不再召回 |
| 冲突记忆 | `conflict-detector` 检测后提示用户确认 |
| 敏感信息 | `sanitizer` 拒绝或脱敏 |
| 记忆污染 | `commit` 默认生成候选而非直接写入 |

## Namespace 设计

```
viking://tenants/{tenant_id}/users/{user_id}/memories/profile/
viking://tenants/{tenant_id}/users/{user_id}/memories/preferences/
viking://tenants/{tenant_id}/users/{user_id}/memories/projects/
viking://tenants/{tenant_id}/users/{user_id}/memories/environments/
viking://tenants/{tenant_id}/users/{user_id}/memories/cases/
viking://tenants/{tenant_id}/users/{user_id}/memories/decisions/
viking://tenants/{tenant_id}/agents/{agent_id}/memories/reflections/
viking://tenants/{tenant_id}/resources/
viking://tenants/{tenant_id}/system/doctor/
```

隔离原则：
- 不同 tenant 严格隔离
- 不同 user 默认不可互读
- system/doctor 只存临时测试数据

## 开发状态

- [x] lib/ 核心库（config、client、adapter、policy、classifier、detector、formatter）
- [x] schema/ JSON Schema
- [x] config.example.json
- [x] scripts/ov-memory CLI（14 个子命令）
- [x] 12 个子 Skill SKILL.md + scripts
- [x] 主 SKILL.md
- [x] BEST_PRACTICES.md

## 技术栈

- Python 3.10+（仅使用标准库，零第三方依赖）
- 支持 MCP 和 HTTP 双通道调用 OpenViking
- 可作为 Hermes Agent Skill、独立 CLI 工具、或库被其他项目导入

## License

Private — 仅限内部使用。
