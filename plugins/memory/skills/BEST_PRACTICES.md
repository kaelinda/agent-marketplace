# OpenViking Memory Skill Suite — 最佳实践

面向 Agent 开发者和使用者的记忆工作流实践指南。以 Claude Code 为主要集成目标，原则适用于所有 Agent 平台。

---

## 一、Agent 集成

### 1.1 注册到 Claude Code

将 Skill Suite 注册为 Claude Code 的 Skill 目录：

```json
// .claude/settings.json 或项目级 CLAUDE.md
{
  "skills": [
    "/path/to/openviking-memory-skills"
  ]
}
```

或在 `CLAUDE.md` 中引用：

```markdown
@openviking-memory-skills/SKILL.md
```

Claude Code 会自动加载主 `SKILL.md`，Agent 即可获得 recall、capture、commit 等记忆工作流能力。

### 1.2 MCP 工具配置

确保 OpenViking MCP Server 已注册：

```json
// ~/.claude/mcp.json
{
  "mcpServers": {
    "openviking": {
      "command": "openviking-mcp",
      "args": ["--config", "/path/to/config.json"],
      "env": {
        "OPENVIKING_API_KEY": "your-key"
      }
    }
  }
}
```

### 1.3 SKILL.md 触发条件设计

在主 SKILL.md 中，触发条件应精确但不过窄：

```markdown
## When to use

Use this Skill Suite when:
- The user refers to previous conversations, projects, preferences, or environments.
- The user says 记住、保存、别忘了、以后按这个来。
- The user says 忘掉、删除记忆、不要记这个。
- The current task depends on prior context that may be in long-term memory.
- A session reaches a reusable conclusion (design decision, bug fix, preference clarification).
- The user reports that memory is not working or asks to check memory.
```

**不要写成：** "Use this for all conversations" — 这会导致每轮都触发 recall，浪费 token 且干扰回答。

### 1.4 上下文注入格式

recall 输出应以结构化块注入 Agent 上下文，放在用户消息之后、系统指令之前：

```
[Relevant OpenViking Memory]
- Preference: User prefers Chinese explanations with concrete steps and copy-pasteable commands.
- Project: OpenViking Memory Skill Suite — designing doctor, recall, capture, merge, forget, commit sub skills.
- Decision: Doctor is the first required sub skill; auto-store disabled by default.
[/Relevant OpenViking Memory]
```

**长度控制：** 总注入内容不超过 500 字。单条记忆用 summary 级别（1-2 句话），不注入全文。

---

## 二、记忆召回

### 2.1 何时召回

**应该召回的场景：**

| 信号 | 示例 |
|------|------|
| 用户引用历史 | "上次那个项目"、"之前的配置"、"我们讨论过" |
| 任务依赖上下文 | 继续开发、继续排查、继续部署 |
| 用户询问偏好 | "我喜欢什么格式来着" |
| 环境相关问题 | 涉及用户服务器、Nginx、Docker 等 |

**不应召回的场景：**

| 场景 | 原因 |
|------|------|
| 通用知识问答 | "Python 怎么排序列表" — 不需要记忆 |
| 首次见面的用户 | 无历史可召回 |
| 明确不相关的话题 | 用户问天气，不需要召回项目记忆 |

**原则：** 召回是成本（token、延迟、干扰），只在有价值时触发。

### 2.2 召回策略

**类型优先级（从高到低）：**

1. `preference` — 用户偏好，影响回答风格
2. `project` — 当前活跃项目背景
3. `environment` — 用户技术环境
4. `case` — 历史问题排查案例
5. `decision` — 已确认的技术决策
6. `agent_reflection` — Agent 自身经验

**数量控制：**

- 默认 3-6 条
- 最多 12 条
- 宁少勿多 — 注入太多会稀释当前上下文

**分数过滤：**

- `min_score: 0.62` 以下的结果直接丢弃
- 低相关记忆注入等于噪声

### 2.3 避免召回污染

**核心原则：用户当前输入 > 历史记忆。**

如果用户说"现在用 Ubuntu 了"，即使记忆里写的是 CentOS 8，以当前输入为准。历史记忆仅作为参考背景，不应覆盖用户明确的当前指令。

**L2（全文）默认关闭：** summary 级别已足够。全文注入会大幅增加 token 消耗且引入无关细节。

---

## 三、记忆写入

### 3.1 什么值得存

| 类型 | 判断标准 | 示例 |
|------|----------|------|
| 偏好 | 用户长期稳定的习惯 | "喜欢中文、完整代码、可复制命令" |
| 项目 | 长期活跃的工程 | "OpenViking Memory Skill Suite" |
| 环境 | 用户服务器/工具链 | "CentOS 8, Nginx /www/server/nginx" |
| 案例 | 已解决的排查问题 | "Nginx 502 — 检查容器端口映射" |
| 决策 | 用户确认的技术选型 | "auto_store 默认关闭" |
| Agent 经验 | 可复用的排查模式 | "TLS 问题先检查代理环境变量" |

**核心判断：这条信息在 3 个月后还有用吗？** 如果答案是否，不要存。

### 3.2 什么不该存

- **敏感信息：** API Key、密码、Token、JWT、SSH 私钥、数据库密码、身份证号、银行卡号
- **临时内容：** 一次性命令、临时日志、调试输出、当前会话的中间状态
- **未确认猜测：** Agent 自己推测的结论，用户没有确认
- **过于细碎：** "用户运行了 `ls -la`" — 这不是长期记忆

### 3.3 auto_store 为什么默认关

自动存储会导致：
1. **记忆污染** — 大量无价值内容涌入，稀释真正有用的记忆
2. **召回干扰** — 搜索时被垃圾记忆抢占排名
3. **敏感泄露** — Agent 可能在不经意间存储敏感信息

**推荐策略：**
- 用户明确说"记住" → 直接写入
- 会话结束 → commit 生成候选，用户确认后写入
- Agent 觉得值得存 → 不直接写入，建议用户确认

### 3.4 写入前检查链

每次写入必须经过以下检查，顺序不可调换：

```
1. 敏感信息检测（sensitive_detector）
   ├─ 检测到 → 拒绝或脱敏
   └─ 安全 → 继续

2. 去重搜索（dedupe）
   ├─ 高度相似 → merge 而非新建
   └─ 无重复 → 继续

3. 类型自动分类（classifier）
   └─ 确定 memory type

4. Scope 选择
   └─ 根据 type 路由到正确 namespace
```

---

## 四、会话沉淀

### 4.1 commit 策略

**核心原则：先候选，后确认，不自动 apply。**

commit 流程：

```
会话结束
    ↓
commit 读取会话内容
    ↓
提取可沉淀信息（决策、偏好、环境、案例）
    ↓
过滤掉临时内容和敏感信息
    ↓
生成候选记忆列表
    ↓
用户确认（或配置为自动确认）
    ↓
写入 OpenViking
```

### 4.2 沉淀优先级

当候选数量超过 `max_memories_per_session`（默认 5）时，按以下优先级保留：

1. **决策（decision）** — 影响后续开发方向，最值得保留
2. **偏好（preference）** — 影响回答风格，长期有效
3. **环境（environment）** — 用户技术栈，排查问题必需
4. **案例（case）** — 已解决的问题，避免重复排查
5. **项目（project）** — 项目背景，但更新频率高，旧的容易过期

### 4.3 长会话 vs 短会话

| 会话类型 | 是否 commit | 原因 |
|----------|------------|------|
| 5 分钟问答 | ❌ | 无长期价值内容 |
| 30 分钟调试 | ✅ commit case | 可能沉淀出排查案例 |
| 2 小时设计方案 | ✅ commit decision + project | 产生重要决策 |
| 持续开发会话 | ✅ commit 5 条候选 | 积累大量可复用信息 |

---

## 五、安全治理

### 5.1 敏感信息三道防线

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

### 5.2 多用户隔离

**Namespace 规范：**

```
viking://tenants/{tenant_id}/users/{user_id}/memories/
```

- `tenant_id` — 租户隔离，不同客户之间严格隔离
- `user_id` — 用户隔离，同一租户下不同用户默认不可互读

**配置检查：**

```json
{
  "safety": {
    "allow_cross_user_read": false,
    "allow_cross_user_write": false
  }
}
```

**doctor 检查项：** 如果 `user_id` 是 `default_user`，doctor 会给出警告 — 生产环境必须使用真实用户 ID。

### 5.3 脱敏 vs 拒绝

| 策略 | 适用场景 | 示例 |
|------|----------|------|
| **拒绝** | 整条记忆都是敏感信息 | 用户粘贴了一段包含 API Key 的配置 |
| **脱敏** | 记忆主体有价值，部分敏感 | "服务器 IP 是 1.2.3.4，密码是 xxx" → 脱敏密码部分 |

默认策略：`deny_sensitive: true`（拒绝）。改为脱敏需显式配置 `redact_secrets: true`。

---

## 六、记忆生命周期

### 6.1 全流程

```
创建（capture / commit）
    ↓
激活（status: active）← 默认状态，可被召回
    ↓
更新（merge）← 用户修改、新信息补充
    ↓
过期（status: obsolete）← 标记过期，不再召回，保留历史
    ↓
归档（status: archived）← 长期不活跃，压缩存储
    ↓
删除（status: deleted / hard delete）← 用户明确要求删除
```

### 6.2 merge 策略

当新信息与已有记忆冲突或相似时：

| 情况 | 处理方式 |
|------|----------|
| 完全重复 | 跳过，不写入 |
| 高度相似 | merge — 保留稳定事实，加入新事实，删除过时事实 |
| 内容冲突 | 标记冲突，提示用户确认哪个为准 |
| 不确定信息 | 标记 `confidence: 0.5`，不作为强依据 |

**merge 保留规则：**
- 保留：用户明确确认的事实
- 加入：新出现的事实
- 删除：被用户明确否定的事实
- 标记：互相矛盾的信息（等待用户确认）

### 6.3 定期治理

建议周期性运行：

```bash
# 去重 — 发现并合并重复记忆
ov-memory admin dedupe --scope user_memories

# 清理 — 删除超过 180 天的过期案例
ov-memory admin prune --older-than 180d --type case --status obsolete

# 统计 — 查看记忆分布
ov-memory admin stats

# 审计 — 扫描存量敏感信息
ov-memory admin audit
```

---

## 七、典型场景

### 场景 1：继续长期项目

**用户：** "继续完善 OpenViking Memory Skill"

**流程：**

```
1. recall 子 Skill 检索 project / decision / preference
2. 注入相关上下文（项目背景、上次决策、用户偏好）
3. Agent 基于上下文继续上次方案
4. 本轮产生新决策时 → commit 生成候选记忆
5. 用户确认后写入
```

**关键点：** 不要注入全部历史。只注入与当前任务直接相关的 3-6 条。

### 场景 2：记住配置

**用户：** "记住，我的 Nginx 路径是 /www/server/nginx"

**流程：**

```
1. capture 判断为 environment 类型
2. sensitive_detector 检测 — 无敏感信息
3. dedupe 搜索 — 是否已有 Nginx 路径记忆？
   ├─ 有 → merge 更新
   └─ 无 → 新建
4. 写入 environments scope
5. 返回保存成功
```

**关键点：** 即使用户说"记住"，也要经过完整检查链。环境信息也可能包含敏感数据（如内网 IP）。

### 场景 3：记忆不生效

**用户：** "为什么之前的记忆查不到？"

**流程：**

```
1. doctor quick — 检查配置和服务是否可达
2. doctor standard — 检查读写闭环
3. 检查索引延迟 — 是否刚写入还没索引完成
4. 检查 scope — 是否配错了 tenant / user / agent
5. 检查 recall 参数 — min_score 是否太高、limit 是否太小
6. 输出修复建议
```

**关键点：** 先诊断系统，再怀疑内容。80% 的"记忆不生效"是配置问题。

### 场景 4：问题排查后沉淀

**用户解决了：** "sub2api IP 能访问，但域名 502"

**流程：**

```
1. commit 读取本次会话
2. 提取关键信息：
   - problem: IP 能访问但域名 502
   - environment: Docker Compose + Nginx 反向代理
   - root_cause: 容器端口映射或 Nginx upstream 问题
   - solution: 检查容器状态 → 本地 curl → 查 Nginx 日志 → 验证 proxy_pass
3. 生成 case memory 候选
4. 用户确认后写入 case-memory
```

**关键点：** 排查案例是最有价值的记忆类型之一。下次遇到类似问题，Agent 可以直接调取历史方案，跳过重复排查。

---

## 八、反模式

### ❌ 1. 自动存储所有对话

**问题：** 记忆被大量无价值内容污染，召回时全是噪声。

**修正：** `auto_store: false`，只在用户明确要求或 commit 确认后写入。

### ❌ 2. 不检查直接写入

**问题：** API Key、密码被存入长期记忆，存在泄露风险。

**修正：** 每次写入前经过 sensitive_detector → classifier → dedupe 三步检查。

### ❌ 3. 一次召回太多记忆

**问题：** 注入 20 条记忆，token 爆炸，Agent 被历史信息淹没。

**修正：** 默认 3-6 条，最多 12 条。宁少勿多。

### ❌ 4. 召回后覆盖当前指令

**问题：** 用户说"现在用 Ubuntu"，但 Agent 根据记忆坚持说"你的服务器是 CentOS"。

**修正：** 当前用户输入优先级高于历史记忆。记忆是参考，不是权威。

### ❌ 5. 跳过 doctor 直接使用

**问题：** 配置错误、scope 写错、MCP 未注册，所有记忆操作静默失败。

**修正：** 首次安装、配置变更、记忆异常时，先跑 doctor。

### ❌ 6. 用 default_user 上生产

**问题：** 多用户共享同一个 namespace，记忆互相串扰。

**修正：** 生产环境必须使用真实的 `tenant_id` + `user_id`。doctor 会对此给出警告。

### ❌ 7. commit 直接 apply 不确认

**问题：** Agent 错误判断临时内容为长期记忆，写入后污染记忆库。

**修正：** commit 默认生成候选列表，用户确认后再写入。

### ❌ 8. 不区分记忆类型

**问题：** 所有记忆都存为同一类型，召回时无法按需过滤。

**修正：** 使用 classifier 自动分类，或手动指定 `--type`。类型决定召回优先级和 namespace 路由。

### ❌ 9. 存量记忆从不清理

**问题：** 过期记忆持续干扰召回，旧项目信息与当前方向冲突。

**修正：** 定期运行 `admin dedupe` 和 `admin prune`。记忆需要维护，不是写完就不管了。

### ❌ 10. 跨用户读取他人记忆

**问题：** 隐私泄露，用户 A 的偏好、环境、项目信息被用户 B 的 Agent 看到。

**修正：** `allow_cross_user_read: false`，默认禁止。除非是明确的团队共享场景，否则严格隔离。
