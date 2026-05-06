# OpenViking Memory Skill Suite — 最佳实践

面向 Agent 开发者和使用者的记忆工作流实践指南。

> 本文档适用于 openviking 和 mem0 双后端，所有最佳实践不依赖具体后端实现。

---

## 一、首次接入

### 1.1 跑通 doctor 再做任何事

```bash
# 首次安装、配置变更、记忆异常时，先跑 doctor
ov-memory doctor
ov-memory doctor --fix  # 自动修复可修复的问题
```

**为什么：** 80% 的"记忆不工作"是配置问题（API Key 未设、scope 写错、后端不可达）。doctor 会检查连接、读写闭环、配置完整性，比你自己排查快 10 倍。

### 1.2 后端选择

| 场景 | 推荐后端 | 理由 |
|------|----------|------|
| 开发/测试 | openviking (HTTP) | 本地可控，调试方便 |
| 生产/多租户 | mem0 | 云端托管，自带向量索引和用户隔离 |
| 需要自定义向量库 | openviking (MCP) | 通过 MCP 协议可对接任意存储 |

切换方式：只改 `config.json` 的 `backend` 字段，所有子 skill 无需修改。

```json
// mem0
{ "backend": "mem0", "mem0_config": { "api_key_env": "MEM0_API_KEY" } }

// openviking
{ "backend": "openviking", "base_url": "http://localhost:8080" }
```

---

## 二、记忆写入

### 2.1 什么值得存

**核心判断：这条信息在 3 个月后还有用吗？**

| 类型 | 判断标准 | 示例 |
|------|----------|------|
| preference | 用户长期稳定的习惯 | "喜欢中文、完整代码、可复制命令" |
| project | 长期活跃的工程 | "OpenViking Memory Skill Suite" |
| environment | 用户服务器/工具链 | "Ubuntu 22.04, Nginx 路径 /etc/nginx" |
| case | 已解决的排查问题 | "Nginx 502 — 检查容器端口映射" |
| decision | 用户确认的技术选型 | "auto_store 默认关闭" |
| agent_reflection | 可复用的排查模式 | "TLS 问题先检查代理环境变量" |

### 2.2 什么不该存

- **敏感信息：** API Key、密码、Token、JWT、SSH 私钥、数据库连接串、身份证号
- **临时内容：** 一次性命令、临时日志、调试输出、当前会话中间状态
- **未确认猜测：** Agent 自己推测的结论，用户没有确认
- **过于细碎：** "用户运行了 `ls -la`" — 这不是长期记忆

### 2.3 写入前检查链（顺序不可调换）

```
capture / commit 写入
    ↓
1. 敏感信息检测（sensitive_detector）
   ├─ 检测到 block 级 → 拒绝或脱敏
   └─ 安全 → 继续
    ↓
2. 去重搜索（dedupe hook）
   ├─ 高度相似 → merge 而非新建
   └─ 无重复 → 继续
    ↓
3. 类型自动分类（classifier）
   └─ 确定 memory type（preference / project / environment / case / decision / agent_reflection）
    ↓
4. Scope 路由
   └─ 根据 type 写入对应 namespace
```

### 2.4 auto_store 为什么默认关

自动存储会导致：
1. **记忆污染** — 大量无价值内容涌入，稀释真正有用的记忆
2. **召回干扰** — 搜索时被垃圾记忆抢占排名
3. **敏感泄露** — Agent 可能在不经意间存储敏感信息

**推荐策略：**
- 用户明确说"记住" → 直接 capture 写入
- 会话结束 → commit 生成候选，用户确认后写入
- Agent 觉得值得存 → 不直接写入，建议用户确认

---

## 三、记忆召回

### 3.1 何时召回

**应该召回：**

| 信号 | 示例 |
|------|------|
| 用户引用历史 | "上次那个项目"、"之前的配置"、"我们讨论过" |
| 任务依赖上下文 | 继续开发、继续排查、继续部署 |
| 用户询问偏好 | "我喜欢什么格式来着" |
| 环境相关问题 | 涉及用户服务器、Nginx、Docker 等 |

**不应召回：**

| 场景 | 原因 |
|------|------|
| 通用知识问答 | "Python 怎么排序列表" — 不需要记忆 |
| 首次见面的用户 | 无历史可召回 |
| 明确不相关的话题 | 用户问天气，不需要召回项目记忆 |

**原则：** 召回有成本（token、延迟、干扰），只在有价值时触发。

### 3.2 召回策略

**类型优先级（从高到低）：**

1. `preference` — 用户偏好，影响回答风格
2. `project` — 当前活跃项目背景
3. `environment` — 用户技术环境
4. `case` — 历史问题排查案例
5. `decision` — 已确认的技术决策
6. `agent_reflection` — Agent 自身经验

**数量控制：**
- 默认 3-6 条，最多 12 条
- 宁少勿多 — 注入太多会稀释当前上下文
- `min_score: 0.62` 以下的结果直接丢弃

### 3.3 避免召回污染

**核心原则：用户当前输入 > 历史记忆。**

如果用户说"现在用 Ubuntu 了"，即使记忆里写的是 CentOS 8，以当前输入为准。历史记忆仅作为参考背景，不应覆盖用户明确的当前指令。

**上下文注入格式（总长不超过 500 字）：**

```
[Relevant Memory]
- Preference: User prefers Chinese explanations with copy-pasteable commands.
- Project: OpenViking Memory Skill Suite — designing sub-skill workflows.
- Decision: Doctor is the first required sub skill; auto-store disabled by default.
[/Relevant Memory]
```

---

## 四、会话沉淀（commit）

### 4.1 commit 策略

**核心原则：先候选，后确认，不自动 apply。**

```
会话结束
    ↓
commit 读取会话内容
    ↓
提取可沉淀信息（决策、偏好、环境、案例）
    ↓
过滤掉临时内容和敏感信息
    ↓
生成候选记忆列表（≤5 条）
    ↓
用户确认（或配置为自动确认）
    ↓
写入记忆库
```

### 4.2 沉淀优先级

候选数量超过上限时，按以下优先级保留：

1. **decision** — 影响后续开发方向，最值得保留
2. **preference** — 影响回答风格，长期有效
3. **environment** — 用户技术栈，排查问题必需
4. **case** — 已解决的问题，避免重复排查
5. **project** — 项目背景，但更新频率高，旧的容易过期

### 4.3 长会话 vs 短会话

| 会话类型 | 是否 commit | 原因 |
|----------|------------|------|
| 5 分钟问答 | ❌ | 无长期价值内容 |
| 30 分钟调试 | ✅ commit case | 可能沉淀出排查案例 |
| 2 小时设计方案 | ✅ commit decision + project | 产生重要决策 |
| 持续开发会话 | ✅ commit 5 条候选 | 积累大量可复用信息 |

---

## 五、记忆维护

### 5.1 记忆生命周期

```
创建（capture / commit）
    ↓
激活（active）← 默认状态，可被召回
    ↓
更新（merge）← 用户修改、新信息补充
    ↓
过期（obsolete）← 标记过期，不再召回
    ↓
归档（archived）← 长期不活跃
    ↓
删除（delete）← 用户明确要求
```

### 5.2 merge 策略

| 情况 | 处理方式 |
|------|----------|
| 完全重复 | 跳过，不写入 |
| 高度相似 | merge — 保留稳定事实，加入新事实 |
| 内容冲突 | 标记冲突，提示用户确认 |
| 不确定信息 | 标记 confidence: 0.5，不作为强依据 |

### 5.3 定期治理

```bash
# 去重 — 发现并合并重复记忆
ov-memory admin dedupe

# 清理 — 删除超过 180 天的过期案例
ov-memory admin cleanup --older-than 180d

# 审计 — 扫描存量敏感信息
ov-memory admin audit

# 统计 — 查看记忆分布
ov-memory admin stats
```

建议每月运行一次，保持记忆库质量。

---

## 六、安全治理

### 6.1 敏感信息三道防线

```
第一道：write 前检测
    ↓ 每次 capture / commit 写入前扫描
    ↓ 匹配 secret pattern → 拒绝或 redact

第二道：commit 前扫描
    ↓ 会话沉淀时二次扫描
    ↓ 防止用户在对话中无意泄露的密钥被存储

第三道：定期 audit
    ↓ memory-admin audit 命令
    ↓ 扫描存量记忆中可能遗漏的敏感信息
```

### 6.2 脱敏 vs 拒绝

| 策略 | 适用场景 | 示例 |
|------|----------|------|
| **拒绝** | 整条记忆都是敏感信息 | 用户粘贴了包含 API Key 的配置 |
| **脱敏** | 记忆主体有价值，部分敏感 | "密码是 xxx" → 脱敏密码部分 |

默认策略：`deny_sensitive: true`（拒绝）。改为脱敏需显式配置 `redact_secrets: true`。

### 6.3 多用户隔离

```
viking://tenants/{tenant_id}/users/{user_id}/memories/
```

- `tenant_id` — 租户隔离，不同客户之间严格隔离
- `user_id` — 用户隔离，同一租户下不同用户默认不可互读

生产环境必须使用真实用户 ID，`default_user` 只用于开发测试。

---

## 七、Agent 集成

### 7.1 SKILL.md 触发条件设计

触发条件应精确但不过窄：

```markdown
Use this Skill Suite when:
- The user refers to previous conversations, projects, preferences, or environments.
- The user says 记住、保存、别忘了、以后按这个来。
- The user says 忘掉、删除记忆、不要记这个。
- A session reaches a reusable conclusion (decision, bug fix, preference).
- The user reports that memory is not working or asks to check memory.
```

**不要写成：** "Use this for all conversations" — 每轮都触发 recall 会浪费 token 且干扰回答。

### 7.2 召回注入格式

recall 输出应以结构化块注入 Agent 上下文，放在用户消息之后：

```
[Relevant Memory]
- Preference: User prefers Chinese, complete code, copy-pasteable commands.
- Project: OpenViking Memory Skill Suite — sub-skill workflow design.
[/Relevant Memory]
```

**长度控制：** 总注入不超过 500 字。单条记忆用 summary 级别（1-2 句话），不注入全文。

---

## 八、反模式速查

| ❌ 反模式 | ✅ 正确做法 |
|-----------|------------|
| 自动存储所有对话 | `auto_store: false`，用户确认后写入 |
| 不检查直接写入 | 每次写入经过 sensitive → dedupe → classify 三步 |
| 一次召回 20+ 条记忆 | 默认 3-6 条，最多 12 条 |
| 召回后覆盖当前指令 | 当前输入优先，记忆只是参考 |
| 跳过 doctor 直接使用 | 首次/变更/异常时先跑 doctor |
| 用 default_user 上生产 | 生产环境用真实 tenant_id + user_id |
| commit 直接 apply 不确认 | 默认生成候选，用户确认后写入 |
| 不区分记忆类型 | 使用 classifier 自动分类或手动指定 --type |
| 存量记忆从不清理 | 定期 admin dedupe + admin cleanup |
| 跨用户读取他人记忆 | `allow_cross_user_read: false`，默认禁止 |

---

## 九、典型场景

### 场景 1：继续长期项目

```
用户："继续完善 OpenViking Memory Skill"

1. recall 检索 project / decision / preference
2. 注入 3-6 条相关上下文
3. Agent 基于上下文继续上次方案
4. 本轮产生新决策 → commit 生成候选
5. 用户确认后写入
```

### 场景 2：记住配置

```
用户："记住，我的 Nginx 路径是 /www/server/nginx"

1. capture 判断为 environment 类型
2. sensitive_detector 检测 — 无敏感信息
3. dedupe 搜索 — 是否已有 Nginx 路径记忆？
   ├─ 有 → merge 更新
   └─ 无 → 新建
4. 写入 environments scope
5. 返回保存成功
```

### 场景 3：记忆不生效

```
用户："为什么之前的记忆查不到？"

1. doctor — 检查配置和服务
2. 检查索引延迟 — 是否刚写入还没索引完成
3. 检查 scope — 是否配错了 tenant / user
4. 检查 recall 参数 — min_score 是否太高
5. 输出修复建议
```

### 场景 4：问题排查后沉淀

```
解决了："容器 OOM killed"

1. commit 读取本次会话
2. 提取：problem / environment / root_cause / solution
3. 生成 case memory 候选
4. 用户确认后写入 case-memory
5. 下次遇到类似问题，Agent 直接调取历史方案
```
