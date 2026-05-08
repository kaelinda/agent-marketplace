# 子 Skill 使用指南

本文档覆盖 OpenViking Memory Skills 全部 12 个子 skill 的用法。

> **后端切换**：所有子 skill 无需任何修改，只需更改 `config.json` 中的 `backend` 字段即可在 openviking / mem0 之间切换。

---

## 1. 🔍 recall — 记忆召回

从记忆库中语义搜索相关记忆。

```bash
# 基本搜索
ov-memory recall --query "Docker部署"

# 按类型过滤
ov-memory recall --query "nginx" --type knowledge

# 限制返回数量
ov-memory recall --query "部署" --limit 10

# 指定 scope
ov-memory recall --query "配置" --scope "project:myapp"
```

| 参数 | 说明 |
|------|------|
| `--query` | 搜索关键词（必填） |
| `--type` | 过滤记忆类型（knowledge / experience / preference 等） |
| `--limit` | 最大返回条数（默认 5） |
| `--scope` | 指定搜索范围 |

**返回**：按相关度排序的记忆列表，每条含 content、score、metadata。

---

## 2. ✍️ capture — 记忆写入

写入新记忆，自动检测去重（避免重复存储）。

```bash
# 普通写入
ov-memory capture --content "Redis 密码是 xxx"

# 指定类型
ov-memory capture --content "Nginx 超时设置为 60s" --type knowledge

# 附带标签
ov-memory capture --content "生产环境用 PostgreSQL 15" --tags "db,prod"

# 指定 scope
ov-memory capture --content "项目用 Next.js 14" --scope "project:myapp"
```

| 参数 | 说明 |
|------|------|
| `--content` | 记忆内容（必填） |
| `--type` | 记忆类型（默认 knowledge） |
| `--tags` | 标签，逗号分隔 |
| `--scope` | 存储范围 |

**特性**：写入前自动搜索相似记忆，若有高度相似内容则跳过并提示。

---

## 3. 🗑️ forget — 记忆删除

按条件搜索并删除过期/错误的记忆。支持安全模式。

```bash
# 搜索后交互删除（默认 safe 模式）
ov-memory forget --query "旧的部署地址"

# 智能模式（需确认）
ov-memory forget --query "旧配置" --mode smart

# 安全模式（必须确认）
ov-memory forget --query "旧配置" --mode safe

# 按 ID 直接删除
ov-memory forget --id "mem_abc123"
```

| 参数 | 说明 |
|------|------|
| `--query` | 搜索关键词 |
| `--id` | 直接指定记忆 ID |
| `--mode` | 删除模式：`safe`（默认，需确认）/ `smart`（智能匹配） |

---

## 4. 🔗 merge — 记忆合并

合并重复/冲突记忆，保留最新、最准确的信息。

```bash
# 搜索并检测可合并项
ov-memory merge --query "部署配置"

# 指定合并两条
ov-memory merge --id1 "mem_aaa" --id2 "mem_bbb"

# 自动合并模式
ov-memory merge --query "配置" --auto
```

| 参数 | 说明 |
|------|------|
| `--query` | 搜索关键词，用于发现可合并项 |
| `--id1` / `--id2` | 直接指定待合并的两条记忆 |
| `--auto` | 自动合并（跳过确认） |

**合并策略**：保留最新时间戳、合并互补字段、统一标签。

---

## 5. 📦 commit — 批量提交

将暂存区的一批记忆一次性提交到记忆库。

```bash
# 提交所有暂存记忆
ov-memory commit

# 指定批次大小
ov-memory commit --batch-size 50

# 预览模式（不实际写入）
ov-memory commit --dry-run
```

| 参数 | 说明 |
|------|------|
| `--batch-size` | 每批次大小（默认 20） |
| `--dry-run` | 仅预览，不实际提交 |

**场景**：大量记忆积累后，批量提交以提高效率。

---

## 6. 🩺 doctor — 健康检查

诊断记忆系统连接、配置、数据完整性。

```bash
# 完整健康检查
ov-memory doctor

# 检查并自动修复
ov-memory doctor --fix
```

**检查项**：
- 后端连接（openviking / mem0）
- API Key 配置
- 写入/搜索/删除功能验证
- 数据完整性

> 已适配 mem0 — 自动检测后端类型，显示对应的端点/API 信息。

---

## 7. 🛠️ memory-admin — 记忆管理

CRUD 管理所有记忆（浏览、编辑、清理）。

```bash
# 浏览所有记忆
ov-memory admin list

# 按类型过滤
ov-memory admin list --type knowledge

# 编辑记忆
ov-memory admin edit --id "mem_abc" --content "新内容"

# 删除记忆
ov-memory admin delete --id "mem_abc"

# 清理旧记忆（超过 30 天）
ov-memory admin cleanup --older-than 30d
```

| 参数 | 说明 |
|------|------|
| `--type` | 按类型过滤 |
| `--id` | 记忆 ID |
| `--content` | 新内容（edit 时使用） |
| `--older-than` | 时间阈值（cleanup 时使用，如 `30d`、`7d`） |

---

## 8. 📁 project-memory — 项目记忆

管理项目相关的记忆（技术栈、架构决策、部署配置）。

```bash
# 列出已记录项目
ov-memory project list

# 记录项目信息
ov-memory project capture --name "myapp" --tech-stack "React,Node,PostgreSQL"

# 更新项目信息
ov-memory project update --name "myapp" --content "迁移到 Next.js 14"

# 按方面查询
ov-memory project recall --query "myapp" --aspect "架构"
```

| 参数 | 说明 |
|------|------|
| `--name` | 项目名称（必填） |
| `--tech-stack` | 技术栈（capture 时使用） |
| `--content` | 补充内容 |
| `--aspect` | 查询方面（架构 / 部署 / 测试 等） |

**命名空间**：`{user_scope}/projects/`

---

## 9. 🌍 environment-memory — 环境记忆

记录服务器/部署环境的配置信息（OS、Nginx、路径等）。

```bash
# 列出所有环境
ov-memory env list

# 捕获环境信息
ov-memory env capture --name "prod-server" --os "Ubuntu 22.04" --nginx-path "/etc/nginx"

# 更新环境信息
ov-memory env update --name "prod-server" --content "新增 Redis 缓存配置"
```

| 参数 | 说明 |
|------|------|
| `--name` | 环境名称标识（必填） |
| `--os` | 操作系统（如 Ubuntu 22.04） |
| `--nginx-path` | Nginx 配置路径 |
| `--content` | 补充说明（update 时必填） |

**命名空间**：`{user_scope}/environments/`

---

## 10. ⚙️ preference-memory — 偏好记忆

管理用户偏好设置（编辑器、语言、输出格式等），键值对形式。

```bash
# 列出所有偏好
ov-memory pref list

# 设置偏好
ov-memory pref set --key "editor" --value "vim"

# 查询偏好
ov-memory pref get --key "editor"

# 删除偏好
ov-memory pref delete --key "editor"
```

| 参数 | 说明 |
|------|------|
| `--key` | 偏好键名（必填，支持嵌套如 `coding.style`） |
| `--value` | 偏好值（set 时必填） |

**存储格式**：
```json
{"key": "coding.style", "value": "functional", "scope": "user"}
```

**命名空间**：`{user_scope}/preferences/`

---

## 11. 📚 case-memory — 案例记忆

记录问题排查过程和解决方案，形成可搜索的知识库。

```bash
# 列出所有案例
ov-memory case list

# 创建案例
ov-memory case create --title "OOM排查" --problem "容器 OOM killed" --solution "增加 memory limit 到 2Gi"

# 搜索相关案例
ov-memory case recall --query "OOM"
```

| 参数 | 说明 |
|------|------|
| `--title` | 案例标题（create 时必填） |
| `--problem` | 问题描述（create 时必填） |
| `--solution` | 解决方案（create 时必填） |
| `--query` | 搜索关键词（recall 时使用） |

**命名空间**：`{user_scope}/cases/`

---

## 12. 🤖 agent-reflection — Agent 自省

记录 Agent 的工作反思、错误教训和改进经验。

```bash
# 列出所有反思
ov-memory reflection list

# 新增反思
ov-memory reflection add --title "部署失误" --content "忘记检查端口占用导致部署失败，下次先 lsof 检查"

# 搜索反思
ov-memory reflection recall --query "部署"
```

| 参数 | 说明 |
|------|------|
| `--title` | 反思标题（add 时必填） |
| `--content` | 反思内容（add 时必填） |
| `--query` | 搜索关键词（recall 时使用） |

**命名空间**：`{agent_scope}/reflections/`

⚠️ **注意**：此 skill 存储在 **agent scope** 而非 user scope，召回时优先检查 agent scope。反思记忆应简洁具体，避免空泛描述。

---

## 附录：后端切换配置

### 使用 mem0

```json
{
  "backend": "mem0",
  "mem0_config": {
    "api_key_env": "MEM0_API_KEY",
    "version": "v1.1"
  }
}
```

```bash
export MEM0_API_KEY=your_key_here
```

### 使用 OpenViking（默认）

```json
{
  "backend": "openviking",
  "base_url": "http://localhost:8080"
}
```

切换后端后所有子 skill **无需任何修改**，适配层自动处理响应格式差异。
