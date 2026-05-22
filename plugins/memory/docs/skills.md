# Claude Code Skills 详解

memory plugin 注册了 **5 个 skill**：`memory-recall` / `memory-capture` / `memory-commit` / `memory-doctor` / `memory-admin`，以及 **2 个 slash command**：`/recall` / `/memory-doctor`。

Skill 是**模型按 frontmatter 触发词自动激活**的；command 是**用户敲斜杠主动调用**的。两者底层都走 `memory-cli`。

## 一图看清

```
用户 / Agent 上下文
        │
        ├── 触发词命中 ───────────────────► skill (Claude Code 自动激活)
        │                                      │
        │                                      └─► load_skill_module(...)
        │                                            │
        ├── 用户敲 /recall <q> ─────────► command ─┤
        │                                            ▼
        └── 自动化脚本 ─► memory-cli <cmd> ──► run_xxx(config, ...)
                                                     │
                                                     ▼
                                                  adapter ─► backend
```

## 5 个 skill 速查

| Skill | 用户那一侧的典型说法 | 谁该触发 | 关键参数 |
|---|---|---|---|
| `memory-recall` | "之前我们怎么处理 X 的" / "上次的方案" / "remember when" | Agent 在任务开头主动召回 | query, type, limit |
| `memory-capture` | "记住" / "以后这样" / "save this" | 用户明确要求 / Agent 提取到值得长存的事实 | content, type, scope |
| `memory-commit` | "把刚才的要点存一下" / 长会话 checkpoint | Agent 在会话收尾时 | session-file, --apply |
| `memory-doctor` | "记忆系统好像坏了" / "doctor" / 首次部署 / 切完后端 | 用户主动 / 报错后排查 | --mode |
| `memory-admin` | "看一下记忆库统计" / "去重" / "备份" / "审计" | 运维 / 周期治理 | action + 对应参数 |

> 每个 skill 的 SKILL.md 里 frontmatter 是**给模型看的**——它决定 Claude Code 什么时候自动激活这个 skill。修改 SKILL.md 要谨慎，触发词错位会导致 capture 在不该记的时候记、recall 在该记的时候不召回。

---

## memory-recall

**做什么**：从长期记忆里语义搜索 N 条最相关的，把它们格式化成结构化注入块，丢回上下文里。

**典型触发词**：之前、上次、previously、what did、remember when。

**CLI 等价**：
```bash
memory-cli recall "<query>" [--type project,environment] [--limit 6]
```

**注入格式**（模型看到的样子）：
```
[Relevant OpenViking Memory]
- project: User is designing memory plugin Phase 2 ...
- environment: CentOS 8, Nginx at /www/server/nginx ...
- preference: User prefers Chinese explanations ...
[/Relevant OpenViking Memory]
```

**怎么不踩坑**：
- recall 是**只读**，不要在 capture / commit 之前 recall 一遍当"确认"——是浪费
- 默认 limit=6 / max_limit=12（`recall.max_limit`）；要更多就拉配置
- `recall.min_score`（默认 0.62）会卡掉低相关结果——太严就拉低
- `agent_reflection` 类型会自动在 agent scope 检索（区别于 user scope）

**Claude Code 直接用**：`/recall <query>`（实际上是 command，本质等于跑 skill）

---

## memory-capture

**做什么**：写 1 条新记忆。流程：敏感检测 → 类型分类（可选）→ scope 路由 → adapter.write。

**典型触发词**：记住、以后、remember this、save this for later。

**CLI 等价**：
```bash
memory-cli capture --content "..." [--type TYPE] [--title TITLE] [--scope SCOPE] [--auto-classify]
```

**安全护栏**：
- 内容里出现密码 / API key / token，默认**直接拒**（`safety.deny_sensitive=true`）
- 即使 `deny_sensitive=false`，仍会按 `safety.redact_secrets` 脱敏后再决定要不要写
- 脱敏完还剩敏感数据 → 仍然拒

**类型自动分类**：
- 不传 `--type` 或加 `--auto-classify`，CLI 会调 `classifier.classify_with_confidence()` 推断
- 内置类型：`project / environment / case / preference / decision / profile / agent_reflection`
- 不准就显式 `--type ...`

**scope 路由**：
- 默认按 type 路由到对应 scope（`/projects/`、`/environments/`、`/preferences/` 等）
- 想强制写到自定义命名空间：`--scope viking://tenants/default/users/alice/team/shared/`

**怎么不踩坑**：
- 不要每条对话都 capture。`memory-commit` 是更合适的做法——它从 session 里**挑值得记的**。
- title 默认取内容前 80 字，长内容务必显式给 `--title`，不然 dedupe / browse 不好看
- 写失败**不会**静默丢失，会原样抛出后端错误

---

## memory-commit

**做什么**：从一整段会话里**抽**出值得长期保存的事实，给候选预览，由你/用户决定是否 `--apply`。

**典型场景**：
- 长会话结束前 checkpoint
- 用户说"把这次讨论的要点存下来"
- Agent 在重要决策 / 排障收尾后主动沉淀

**CLI 等价**：
```bash
memory-cli commit --session-file session.json          # 仅预览
memory-cli commit --session-file session.json --apply  # 真的写入
```

**会话文件格式**：
```json
{
  "messages": [
    {"role": "user",      "content": "..."},
    {"role": "assistant", "content": "..."}
  ]
}
```

**提取流程**：
1. 跳过 < 30 字符的短消息
2. 用 `STORE_WORTHY_INDICATORS`（profile 可配）筛
3. 敏感检测 + 类型分类 + 去重
4. 预览候选 / 批量写入

**配置影响**：
- `commit.max_memories_per_session`（默认 5）：单次最多抽几条
- `commit.store_cases / store_preferences / store_projects`：各类型是否参与
- `policy.profile` 切到 `code_assistant` / `life_assistant` 会换 STORE_WORTHY 关键词集

**怎么不踩坑**：
- 不加 `--apply` 永远是预览。**别忘了加。**
- 已经有相似记忆的不会重复存，但相似阈值跟 `recall.min_score` 共用——觉得没去到位就先 `admin dedupe`
- 候选里有敏感数据会被丢掉，不会写入

---

## memory-doctor

**做什么**：给当前 memory 系统体检。三档：

| `--mode` | 查什么 | 大致耗时 |
|---|---|---|
| `quick`    | 配置加载 + API key 是否设 + identity 是不是默认 sentinel | < 100ms |
| `standard` | quick 全部 + 后端 ping + MCP 工具配置 + scope 可读 | 1–3 s |
| `full`     | standard 全部 + write→search→read→delete 端到端闭环 | 5–15 s |

**CLI 等价**：
```bash
memory-cli doctor --mode quick
memory-cli doctor --mode standard
memory-cli doctor --mode full
```

**Claude Code**：`/memory-doctor [mode]`

**返回**：结构化 dict，关键字段 `result`（PASS / PASS_WITH_WARNINGS / FAIL）/ `checks` / `warnings` / `errors`。CLI 把它格式化成有色文本。

**怎么读**：
- `FAIL` 看 errors 第一条——根因 80% 在那
- `PASS_WITH_WARNINGS` 看 warnings：通常是"环境变量没设但你也没用到那个后端"
- `full` 模式会创建并删一条 doctor scope 下的测试记忆，**不会污染**你的常规 scope

详细的红/黄/绿场景对照 → [troubleshooting.md](troubleshooting.md)

---

## memory-admin

**做什么**：运维级操作。

| 子命令 | 用途 | 可逆？ |
|---|---|---|
| `stats`    | 总数 / 类型分布 / 状态分布 | 只读 |
| `backup`   | 当前 scope 全量导出 JSON | 只读 |
| `restore`  | 从备份恢复 | 只追加 |
| `dedupe`   | 同 type+title 保留最新；其余 **硬删** | ❌ 不可逆 |
| `prune`    | 清理 `deleted` / `obsolete` / 自定义 `--status` | ❌ 不可逆 |
| `audit`    | 扫描已存记忆里的敏感数据 | 只读 |

**CLI 等价**：
```bash
memory-cli admin stats [--scope SCOPE]
memory-cli admin backup [--output backup.json] [--scope SCOPE]
memory-cli admin restore --file backup.json
memory-cli admin dedupe [--scope SCOPE]
memory-cli admin prune [--status STATUS] [--older-than 180d]
memory-cli admin audit [--scope SCOPE]
```

**注意**：
- `dedupe` 和 `prune` 是真删（v0.1 那种 `status="deleted"` 墓碑机制已经废）。**跑前先 `backup`**。
- `restore` 不会改原备份文件
- `audit` 报"含敏感"的不代表写入时漏检——可能是写入后**业务侧**填进去的，需要人工评估

---

## 5 个 skill 的组合套路

### 套路 1：标准会话流
```
[会话开始]
    └─► memory-recall（拉项目 / 偏好 / 故障案例上下文）
        ↓
    Agent 干活 ……
        ↓
[会话尾]
    └─► memory-commit --session-file --apply
        （从会话里抽 N 条候选写入）
```

### 套路 2：用户显式记
```
"以后请用中文解释" ──► memory-capture --content "..." --type preference
```

### 套路 3：定期维护
```
每周一次：
    memory-cli admin stats
    memory-cli admin backup --output ~/backups/$(date +%F).json
    memory-cli admin dedupe
    memory-cli admin audit
```

### 套路 4：换后端 / 上线前
```
memory-cli doctor --mode quick        # 本地配置先过
memory-cli doctor --mode standard     # ping 后端
memory-cli doctor --mode full         # 端到端闭环
```

---

更深一层（什么时候**不**该触发哪个 skill / 模型怎么选择）→ 看每个 skill 自己的 `SKILL.md` frontmatter 描述。这里写的是"用户应该怎么用"，不是"模型应该怎么决策"。
