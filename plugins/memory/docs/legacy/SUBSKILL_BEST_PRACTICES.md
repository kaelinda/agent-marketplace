# OpenViking Memory Skill Suite — 子 Skill 实战指南

面向 Agent 使用者的 12 个子 Skill 完整操作手册。聚焦「什么时候用、怎么用、参数怎么调」。

---

## 速查表

| 场景 | 首选 Skill | 备选 |
|------|-----------|------|
| 首次使用 / 配置变更 / 排查问题 | `doctor` | — |
| 用户引用历史 / 继续之前的任务 | `recall` | — |
| 用户说"记住" / 想保存信息 | `capture` | `commit`（批量） |
| 会话结束，沉淀本次要点 | `commit` | `capture`（手动挑） |
| 更新已有记忆 | `merge` | `capture`（先 forget 再新建） |
| 删除错误记忆 | `forget` | `memory-admin prune`（批量） |
| 管理项目上下文 | `project-memory` | `capture --type project` |
| 管理服务器/环境信息 | `environment-memory` | `capture --type environment` |
| 保存排查案例 | `case-memory` | `capture --type case` |
| 管理用户偏好 | `preference-memory` | `capture --type preference` |
| Agent 记录教训 | `agent-reflection` | `capture --type agent_reflection` |
| 备份/去重/清理/审计 | `memory-admin` | — |

---

## 一、基础层（Foundation）

### 1. 🔍 doctor — 系统诊断

**何时用：**
- 首次部署后验证配置
- 配置文件变更后
- 记忆操作返回异常时
- 定期健康检查（建议每周一次）

**三种模式选择：**

| 模式 | 用途 | 耗时 | 适用场景 |
|------|------|------|----------|
| `quick` | 纯配置检查，无网络调用 | <1s | CI/CD 集成、快速验证配置文件 |
| `standard` | 配置 + 连通性 + MCP | ~2s | 日常使用、变更后验证 |
| `full` | 完整读写闭环 | ~5s | 首次部署、怀疑数据损坏时 |

**最佳实践：**
```bash
# 日常检查
ov-memory doctor

# 首次部署必跑
ov-memory doctor --mode full

# CI/CD 里用 quick 模式（不依赖服务在线）
ov-memory doctor --mode quick
```

**输出解读：**
- `PASS` — 全部正常
- `PASS_WITH_WARNINGS` — 可用但有隐患（如 `default_user`）
- `FAIL` — 必须修复后才能使用

---

### 2. 🔍 recall — 记忆召回

**何时用：**
- 用户引用历史（"上次那个项目"、"之前说的配置"）
- 继续未完成的任务
- 需要参考历史决策
- 用户询问偏好（"我喜欢什么格式来着"）

**参数调优：**

| 参数 | 推荐值 | 说明 |
|------|--------|------|
| `--limit` | `3`-`6` | 默认 6，短会话用 3，复杂任务用 6 |
| `--type` | 按需 | 只搜特定类型时指定，减少干扰 |
| `min_score` | `0.62` | 配置文件中设，低于此分数的结果直接丢弃 |

**典型用法：**
```bash
# 广泛召回（默认 6 条）
ov-memory recall "继续开发 OpenViking 项目"

# 精准召回（只搜项目和决策）
ov-memory recall "技术选型" --type project,decision --limit 3

# 环境相关
ov-memory recall "Nginx 配置" --type environment
```

**避免召回污染：**
- 当前用户输入 > 历史记忆
- 用户说"现在用 Ubuntu"，即使记忆里是 CentOS，以当前为准
- 结果太多时宁可丢弃低分结果，也不要注入噪声

---

### 3. ✍️ capture — 记忆写入

**何时用：**
- 用户明确说"记住"、"保存"
- 识别到值得长期保存的配置/决策
- 需要精确控制单条记忆的写入

**写入前检查链（自动执行）：**
```
敏感信息检测 → 去重搜索 → 类型分类 → Scope 路由 → 写入
```

**参数选择：**

| 场景 | 推荐参数 |
|------|----------|
| 用户明确指定类型 | `--type environment --content "..."` |
| 不确定类型 | `--auto-classify --content "..."` |
| 需要自定义 scope | `--scope "custom/path" --content "..."` |
| 指定标题 | `--title "简短标题" --content "..."` |

**典型用法：**
```bash
# 环境信息
ov-memory capture --type environment --title "ECS 生产服务器" \
  --content "CentOS 8, Nginx /www/server/nginx, Docker Compose"

# 自动分类
ov-memory capture --auto-classify \
  --content "以后 Swift 问题尽量给完整可运行代码"

# 项目决策
ov-memory capture --type decision --title "使用 FastAPI" \
  --content "选择 FastAPI 因为性能好且自带 OpenAPI 文档"
```

**什么不该存：**
- API Key、密码、Token（自动拦截）
- 一次性命令输出
- Agent 自己的推测（用户未确认）
- 过于细碎的操作记录

---

### 4. 📦 commit — 批量提交

**何时用：**
- 会话结束，提取本次对话要点
- 用户说"保存这次对话的要点"
- 配合定时任务周期性提取

**工作流：**
```
导出会话 JSON → commit 预览 → 用户确认 → --apply 写入
```

**典型用法：**
```bash
# 第一步：预览候选（不写入）
ov-memory commit --session-file ./session.json

# 第二步：确认后写入
ov-memory commit --session-file ./session.json --apply
```

**会话文件格式：**
```json
{
  "messages": [
    {"role": "user", "content": "..."},
    {"role": "assistant", "content": "..."}
  ]
}
```

**优先级排序（候选超限时保留）：**
1. `decision` — 影响后续方向
2. `preference` — 长期有效
3. `environment` — 排查必需
4. `case` — 已解决问题
5. `project` — 背景信息

---

### 5. 🗑️ forget — 记忆删除

**何时用：**
- 用户要求删除某条记忆
- 发现错误记忆需要清理
- 定期清理过时数据

**三种模式：**

| 模式 | 效果 | 可恢复 | 适用场景 |
|------|------|--------|----------|
| `soft` | 标记删除 | ✅ | 默认选择，安全 |
| `obsolete` | 标记过时 | ✅ | 信息过期但仍想保留参考 |
| `hard` | 永久删除 | ❌ | 敏感信息泄露，必须彻底清除 |

**三种目标：**
```bash
# 按 ID 精确删除
ov-memory forget --memory-id abc123

# 搜索后删除
ov-memory forget --query "旧项目名" --mode obsolete

# 批量清理某个 scope
ov-memory forget --scope "viking://tenants/t/users/u/memories/cases/" --mode soft
```

**注意事项：**
- `hard` 模式不可逆，确认后再执行
- `soft` 删除可通过 `admin restore` 恢复
- 批量删除受 `policy.max_batch_forget` 限制

---

### 6. 🔗 merge — 记忆合并

**何时用：**
- 用户更新了之前记录的信息
- 发现已有记忆需要补充新内容
- 配置变更（如服务器路径更新）

**合并策略：**
- 追加式，不替换原始内容
- 用 `[Updated]` 标记新旧分隔
- 自动更新时间戳和摘要

**典型用法：**
```bash
# 更新环境信息
ov-memory merge --memory-id abc123 --new "路径改为/opt/nginx/"

# 补充项目信息
ov-memory merge --memory-id def456 --new "新增 Redis 缓存层"
```

**输出效果：**
```
原始内容...

[Updated] 路径改为/opt/nginx/
```

---

## 二、类型层（Type-specific）

这 5 个子 Skill 是 `capture` 的类型特化版本，提供更语义化的接口。

### 7. 📂 project-memory — 项目记忆

**存储内容：** 技术栈选型、架构决策（ADR）、项目配置、构建部署流程

**命令速查：**
```bash
ov-memory project list                              # 列出所有项目
ov-memory project create my-api --content "FastAPI + PostgreSQL"
ov-memory project recall --query "技术栈"            # 搜索项目记忆
ov-memory project update my-api --content "新增 Redis"
```

**适用场景：** 多项目切换、长期项目上下文维护

---

### 8. 🖥️ environment-memory — 环境记忆

**存储内容：** 操作系统、Nginx/Apache 配置路径、部署目录、包管理器、系统服务

**命令速查：**
```bash
ov-memory env list
ov-memory env capture --name prod-server --os "Ubuntu 22.04" --nginx-path "/etc/nginx"
ov-memory env update --name prod-server --content "新增 Redis 配置"
```

**适用场景：** 多服务器管理、排查环境相关问题

---

### 9. 📋 case-memory — 案例记忆

**存储内容：** 问题描述、排查过程、解决方案、标签

**命令速查：**
```bash
ov-memory case list
ov-memory case create --title "OOM 排查" \
  --problem "容器 OOM killed" \
  --solution "增加 memory limit 到 2Gi"
ov-memory case recall --query "OOM"
```

**适用场景：** 问题解决后沉淀、遇到类似问题时搜索

**这是最有价值的记忆类型之一：** 下次遇到类似问题可直接调取历史方案，跳过重复排查。

---

### 10. ⚙️ preference-memory — 偏好记忆

**存储内容：** 编码风格、语言偏好、输出格式、工具偏好

**命令速查：**
```bash
ov-memory pref list
ov-memory pref set --key "language" --value "中文"
ov-memory pref get --key "language"
ov-memory pref delete --key "editor"
```

**适用场景：** 个性化 Agent 回答风格

**召回优先级最高：** preference 类型在召回时排第一位，直接影响回答行为。

---

### 11. 🤖 agent-reflection — Agent 自省

**存储内容：** 错误教训、成功经验、工作模式改进、工具使用技巧

**命令速查：**
```bash
ov-memory reflection list
ov-memory reflection add --title "部署失误" \
  --content "忘记检查端口占用导致失败，下次先 lsof 检查"
ov-memory reflection recall --query "部署"
```

**特殊性：** 存储在 agent scope（非 user scope），是 Agent 自身的经验库。

**写好反思的原则：**
- 简洁具体，不写空泛描述
- 包含「错误 → 原因 → 修正」三要素
- 可复用的模式比单次事件更有价值

---

## 三、治理层（Governance）

### 12. 🛠️ memory-admin — 管理后台

**何时用：**
- 定期维护（建议每月一次）
- 备份/恢复
- 疑似记忆污染时
- 安全审计

**命令速查：**

| 命令 | 用途 | 推荐频率 |
|------|------|----------|
| `stats` | 查看记忆分布 | 随时 |
| `backup` | 导出 JSON 备份 | 重大变更前 |
| `restore` | 从备份恢复 | 数据丢失时 |
| `dedupe` | 去重（保留最新） | 每月 |
| `prune` | 清理已删除/过时 | 每月 |
| `audit` | 敏感数据扫描 | 每季度 |

**典型用法：**
```bash
# 查看统计
ov-memory admin stats

# 备份
ov-memory admin backup --output ~/backup-$(date +%Y%m%d).json

# 去重
ov-memory admin dedupe

# 清理过时记忆（默认 deleted + obsolete）
ov-memory admin prune

# 安全审计
ov-memory admin audit
```

---

## 四、组合工作流

### 工作流 1：新项目启动

```bash
# 1. 确认系统正常
ov-memory doctor

# 2. 创建项目记忆
ov-memory project create my-new-project --content "Next.js + Supabase"

# 3. 记录技术决策
ov-memory capture --type decision --title "数据库选型" \
  --content "选择 Supabase 因为..."

# 4. 记录环境信息
ov-memory env capture --name vercel-deploy --content "Vercel 部署, 自动 CI/CD"
```

### 工作流 2：问题排查后沉淀

```bash
# 1. 解决问题后，创建案例
ov-memory case create --title "Nginx 502" \
  --problem "域名访问 502 但 IP 直连正常" \
  --solution "检查 Docker 端口映射 → 本地 curl → 查 Nginx 日志"

# 2. 如果涉及环境信息变更，更新
ov-memory env update --name prod-server --content "新增 upstream 配置"

# 3. Agent 记录教训
ov-memory reflection add --title "502 排查顺序" \
  --content "先检查端口映射，再查 Nginx 配置，最后看容器日志"
```

### 工作流 3：会话结束批量沉淀

```bash
# 1. 导出会话（Agent 自动完成）
# 2. 预览候选
ov-memory commit --session-file session.json

# 3. 确认后写入
ov-memory commit --session-file session.json --apply
```

### 工作流 4：定期维护

```bash
# 1. 健康检查
ov-memory doctor

# 2. 查看统计
ov-memory admin stats

# 3. 去重
ov-memory admin dedupe

# 4. 清理过时数据
ov-memory admin prune

# 5. 安全审计
ov-memory admin audit

# 6. 备份
ov-memory admin backup
```

---

### 工作流 5：多 Agent 协作

当同一用户的多个 Agent（如 Hermes、Claude Code、Codex）共享一个 OpenViking 后端时：

**核心原则：** 每个 Agent 有独立的 `agent_id`，Agent 反思记忆互相隔离，但项目/环境/案例记忆共享。

#### 5a. Agent 启动时加载上下文

```bash
# Agent 启动 → 自动 recall 当前任务相关记忆
ov-memory recall "继续开发 API 模块" --limit 6

# 输出注入 Agent 上下文
[Relevant OpenViking Memory]
- Project: my-api — FastAPI + PostgreSQL, 当前进度 60%
- Decision: 使用 JWT 认证，access_token 过期 15 分钟
- Environment: Docker Compose 部署，端口 8000
- Case: 上次 PostgreSQL 连接池耗尽 — 增加 max_connections 到 200
- Preference: 代码风格 Black，测试用 pytest
```

#### 5b. Agent 独立反思，互不干扰

```bash
# Agent A（Hermes）记录自己的教训
ov-memory reflection add --title "commit 粒度" \
  --content "commit 生成候选时，短会话（<5分钟）应跳过"

# Agent B（Claude Code）记录自己的教训
# 自动存入 Claude Code 的 agent scope，不会污染 Hermes 的反思库
```

**反思记忆的 namespace 设计：**
```
viking://tenants/{tenant}/agents/hermes/memories/reflections/
viking://tenants/{tenant}/agents/claude-code/memories/reflections/
viking://tenants/{tenant}/agents/codex/memories/reflections/
```

每个 Agent 只读写自己的 `agent_id` 下的反思，互不干扰。

#### 5c. Agent 间通过共享记忆协作

场景：Hermes 做了技术选型，Claude Code 接手写代码。

```bash
# Hermes 记录决策
ov-memory capture --type decision --title "API 框架选型" \
  --content "选择 FastAPI 因为自带 OpenAPI 文档、async 支持好"

# Claude Code 启动时 recall → 自动获得这条决策
ov-memory recall "API 开发" --type decision
# → 输出: Decision: 选择 FastAPI 因为自带 OpenAPI 文档...
```

**不需要 Agent A 主动通知 Agent B。** 共享记忆库就是消息总线。

#### 5d. 冲突处理

当 Agent B 的新信息与 Agent A 的旧记忆冲突时：

```bash
# Agent B 发现框架已换成 Gin
ov-memory recall "API 框架" --type decision
# → 返回: Decision: 选择 FastAPI...

# Agent B 不应直接覆盖，而是 merge 并标记冲突
ov-memory merge --memory-id abc123 --new "2026-05-05 切换到 Go Gin，原因：性能需求"

# 或者创建新决策，让 recall 的 conflict_detector 自动检测
ov-memory capture --type decision --title "API 框架切换" \
  --content "从 FastAPI 切换到 Go Gin，原因：P99 延迟要求 < 5ms"
```

**原则：新决策建新条目，旧决策标记 obsolete，保留决策演变历史。**

#### 5e. 配置建议

```json
{
  "identity": {
    "tenant_id": "my-team",
    "user_id": "zhouzuosong",
    "agent_id": "hermes"
  },
  "safety": {
    "allow_cross_user_read": false,
    "allow_cross_user_write": false
  },
  "recall": {
    "max_limit": 6,
    "min_score": 0.62
  }
}
```

每个 Agent 用不同的 `agent_id`，共享同一个 `tenant_id` + `user_id`。

---

### 工作流 6：团队共享记忆

当多个用户（团队成员）需要共享某些知识时：

**核心原则：** 默认隔离，显式共享。通过 tenant 级别的共享 scope 实现。

#### 6a. 共享知识库设计

```
viking://tenants/team-alpha/users/alice/memories/       ← Alice 私有
viking://tenants/team-alpha/users/bob/memories/         ← Bob 私有
viking://tenants/team-alpha/resources/                  ← 团队共享（手动指定 scope）
viking://tenants/team-alpha/system/doctor/              ← 系统诊断
```

#### 6b. 写入团队共享记忆

```bash
# 记录团队共享的排查案例
ov-memory capture --type case --title "生产环境 Redis 连接超时" \
  --content "根因：Redis sentinel 切换时客户端未配置 retry" \
  --scope "viking://tenants/team-alpha/resources/cases/"

# 记录团队共享的编码规范
ov-memory capture --type preference --title "API 错误码规范" \
  --content "错误码格式: E{模块}{序号}，如 E_AUTH_001" \
  --scope "viking://tenants/team-alpha/resources/standards/"
```

#### 6c. 查询团队共享记忆

```bash
# 查询团队共享的排查案例
ov-memory recall "Redis 超时" --scope "viking://tenants/team-alpha/resources/cases/"

# 查询团队编码规范
ov-memory recall "错误码" --scope "viking://tenants/team-alpha/resources/standards/"
```

#### 6d. 权限控制

```json
{
  "safety": {
    "allow_cross_user_read": false,
    "allow_cross_user_write": false
  },
  "scopes": {
    "team_shared": "viking://tenants/team-alpha/resources/",
    "user_memories": "viking://tenants/team-alpha/users/{user_id}/memories/"
  }
}
```

**默认不开放跨用户读写。** 团队共享通过显式指定 `--scope` 实现，而非放宽隔离策略。

#### 6e. 团队运维协作场景

```bash
# 运维 A 排查并记录
ov-memory case create --title "K8s Pod CrashLoop" \
  --problem "Pod 反复重启" \
  --solution "检查 liveness probe 超时设置，从 1s 调到 5s" \
  --scope "viking://tenants/team-alpha/resources/cases/"

# 运维 B 遇到类似问题 → 搜索团队案例库
ov-memory recall "Pod 重启" --scope "viking://tenants/team-alpha/resources/cases/"
# → 输出: Case: K8s Pod CrashLoop — 检查 liveness probe 超时设置
```

---

### 工作流 7：记忆迁移与后端切换

从 OpenViking 迁移到 mem0（或反之）：

```bash
# 1. 备份当前记忆
ov-memory admin backup --output ~/ov-backup-$(date +%Y%m%d).json

# 2. 修改 config.json
# { "backend": "mem0" }

# 3. 验证新后端
ov-memory doctor --mode full

# 4. 恢复数据（逐条写入新后端）
ov-memory admin restore --file ~/ov-backup-20260505.json

# 5. 验证迁移完整性
ov-memory admin stats
ov-memory recall "测试查询"  # 确认召回正常
```

**注意事项：**
- mem0 的 `add()` 会做语义提取，原始内容不会原样存储
- 建议在 metadata 中保留原始字段
- 迁移后运行 `admin audit` 确认敏感信息未泄露

---

### 工作流 8：Agent 自我进化

Agent 通过反思记忆持续改进自身行为：

```bash
# 1. Agent 犯错后记录教训
ov-memory reflection add --title "误删生产数据" \
  --content "执行 forget --mode hard 前没有先备份。教训：hard delete 前必须 backup"

# 2. 下次遇到类似操作时 recall
ov-memory recall "删除数据" --type agent_reflection
# → 输出: Reflection: 误删生产数据 — hard delete 前必须 backup

# 3. 定期复盘反思库
ov-memory reflection list

# 4. 清理过时的教训（已修复的问题）
ov-memory forget --query "旧 bug 的教训" --mode obsolete
```

**反思记忆的价值闭环：**
```
犯错 → 记录教训 → 下次 recall → 避免重复犯错 → 反思记忆越来越多 → Agent 越来越靠谱
```

---

### 工作流 9：多项目上下文切换

同时维护多个项目时的高效切换：

```bash
# 切换到项目 A
ov-memory recall "项目 A 的技术栈" --type project --limit 3
ov-memory recall "项目 A 的待办" --type decision --limit 3

# 切换到项目 B
ov-memory project recall --query "项目 B"

# 项目 A 产生了新决策 → 存入项目 A 的 scope
ov-memory capture --type decision --title "项目 A 数据库迁移" \
  --content "从 MySQL 迁移到 PostgreSQL" \
  --scope "viking://tenants/t/users/u/memories/projects/project-a/"
```

**技巧：** 用 `--scope` 精确控制记忆归属，避免不同项目的记忆互相干扰。

---

### 工作流 10：自动化运维知识库

将日常运维操作沉淀为结构化知识库：

```bash
# 第一阶段：日常积累
# 每次排查完自动沉淀
ov-memory case create --title "DNS 解析失败" \
  --problem "容器内 DNS 解析超时" \
  --solution "检查 CoreDNS Pod 状态 → 查 /etc/resolv.conf → 增加 ndots:5"

ov-memory env capture --name k8s-cluster \
  --content "K8s 1.28, Calico CNI, CoreDNS, 3 master + 5 worker"

# 第二阶段：定期整理
# 每月运行
ov-memory admin dedupe    # 合并重复案例
ov-memory admin audit     # 检查敏感信息
ov-memory admin stats     # 查看知识库规模

# 第三阶段：新人 onboarding
# 新成员加入时，导出团队知识库
ov-memory admin backup --scope "viking://tenants/team-alpha/resources/" \
  --output ~/team-knowledge-$(date +%Y%m%d).json

# 新成员的 Agent recall 团队案例
ov-memory recall "常见问题" --scope "viking://tenants/team-alpha/resources/cases/"
```

---

## 五、参数速查

### recall 参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `query` | str | 必填 | 搜索查询文本 |
| `--type` | str | 全部 | 逗号分隔的类型过滤 |
| `--limit` | int | 6 | 最大返回数（上限 12） |

### capture 参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--content` | str | 必填 | 记忆内容 |
| `--type` | str | 自动推断 | project/environment/case/preference/decision/agent_reflection |
| `--title` | str | 前 80 字符 | 记忆标题 |
| `--scope` | str | 按类型路由 | 自定义命名空间路径 |
| `--auto-classify` | flag | false | 强制自动分类（覆盖 --type） |

### forget 参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--memory-id` | str | — | 指定 ID（三选一） |
| `--query` | str | — | 搜索匹配（三选一） |
| `--scope` | str | — | 批量删除（三选一） |
| `--mode` | str | soft | soft/obsolete/hard |

### admin 参数

| 命令 | 关键参数 | 说明 |
|------|----------|------|
| `stats` | `--scope` | 指定命名空间 |
| `backup` | `--output`, `--scope` | 输出路径、范围 |
| `restore` | `--file` | 备份文件路径 |
| `dedupe` | `--scope` | 按 type+title 去重 |
| `prune` | `--status` | 清理指定状态（默认 deleted+obsolete） |
| `audit` | `--scope` | 敏感数据扫描 |

---

## 六、反模式速查

| ❌ 错误做法 | ✅ 正确做法 |
|------------|-----------|
| 自动存储所有对话 | `auto_store: false`，明确触发或 commit 确认 |
| 不检查直接写入 | 敏感检测 → 去重 → 分类 → 写入 |
| 一次召回 20+ 条 | 默认 3-6 条，最多 12 条 |
| 召回覆盖当前指令 | 当前输入 > 历史记忆 |
| 跳过 doctor 直接用 | 首次/变更/异常时先跑 doctor |
| 用 default_user 上生产 | 真实 tenant_id + user_id |
| commit 直接 apply | 先预览，确认后写入 |
| 所有记忆存同一类型 | 分类存储，类型决定召回优先级 |
| 从不清理存量记忆 | 定期 dedupe + prune |
| 跨用户读取 | `allow_cross_user_read: false` |

---

## 七、记忆类型优先级

召回时按此顺序排序（高 → 低）：

1. **preference** — 用户偏好，影响回答风格
2. **project** — 当前活跃项目背景
3. **environment** — 用户技术环境
4. **case** — 历史问题排查案例
5. **decision** — 已确认的技术决策
6. **agent_reflection** — Agent 自身经验

**数量控制：** 默认 3-6 条，宁少勿多。

---

*文档版本：2026-05-05 v2 | 基于 OpenViking Memory Skill Suite v2 | 新增工作流 5-10*
