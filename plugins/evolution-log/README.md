# evolution-log — 项目演进记录系统

一份随代码库流转的项目演进日志。每条记录只回答三个问题:**从什么变成什么、为什么、谁牵头**。

代码能告诉你"现在是什么样",git log 能告诉你"改了哪一行",但半年后新人问
"当初为什么从 JWT 换成 OAuth2、谁拍的板、当时否掉了哪些方案",没人答得上来 ——
这份日志就是补这一块。

## 组成

| 组件 | 作用 |
| :--- | :--- |
| `evolution-log` skill | 初始化 / 记录 / 查询 / 草稿确认四条工作流 |
| Stop hook（`evolog-check.py`） | 每轮结束前规则快筛,疑似方案级变更时提醒模型补录 |
| `evolog-index.py` | 从 `records/*.md` 全量重建 `INDEX.md` 与 `.cache/records.json`,幂等 |
| `evolog-init.py` | 项目初始化:配置、存储骨架、`.gitattributes` / `.gitignore` / merge driver、`post-merge` |
| Markdown 存储 | `docs/evolution/records/*.md`,进 Git、随 PR 流转、可 review |

`records/` 是唯一事实来源,索引任何时候都可以丢掉重建。

三个脚本都放在 skill 目录内(`skills/evolution-log/scripts/`),**skill 自包含** ——
把 `skills/evolution-log/` 整个目录拷到任何地方都能用,不依赖插件是否安装、
也不依赖项目根下的任何文件。

## 安装

### Claude Code

```text
/plugin marketplace add kaelinda/agent-marketplace
/plugin install evolution-log@manji
```

装完在目标项目里说一句"**给这个项目初始化演进日志**",skill 会先 `--dry-run`
把要写的文件念一遍,确认后才落盘。也可以手动跑:

```bash
S="<plugin>/skills/evolution-log/scripts"
python3 "$S/evolog-init.py" --dry-run     # 预演,不写任何文件
python3 "$S/evolog-init.py"               # 插件模式
python3 "$S/evolog-init.py" --standalone  # 不装插件也能用
```

### Codex CLI

Codex 不认 `.claude/skills/`,仓库级 skill 的发现目录是 `.agents/skills/`,
也不提供 `CLAUDE_PLUGIN_ROOT`。用 `--codex` 安装:

```bash
python3 "<skill>/scripts/evolog-init.py" --codex
```

它会把整个 skill(SKILL.md + templates + scripts)自包含地装到
`.agents/skills/evolution-log/`,并把 Stop hook 注册进 `.codex/hooks.json`。
hook 命令在运行时用 `git rev-parse --show-toplevel` 现场解析仓库根 ——
从任意子目录启动 Codex 都能定位脚本,也不会把某台机器的绝对路径写死进仓库。

初始化是幂等的,已存在的文件一律不覆盖(除非 `--force`)。

### 三种安装模式

| 模式 | Stop hook 来自 | skill 来自 | 适用 |
| :--- | :--- | :--- | :--- |
| 插件模式（默认） | 插件目录,不进你的仓库 | 插件目录 | 个人使用;团队都装了插件 |
| `--standalone` | 项目 `.claude/hooks/` + `.claude/settings.json` | 插件目录 | 团队成员不都装插件,希望 clone 即生效 |
| `--codex` | 项目 `.claude/hooks/` + `.codex/hooks.json` | 项目 `.agents/skills/` | Codex CLI |

`--standalone` 与插件模式并存也不会重复阻断:插件里的 check 脚本检测到项目自带副本时会主动让位。

> `evolog-index.py` 在三种模式下都会复制一份进项目 `.claude/hooks/` —— git 的
> `post-merge` 钩子在 Claude Code / Codex 之外运行,必须有项目内副本才能在合并后重建索引。

## 依赖

只需要 `python3`（3.6+,纯标准库,不依赖 PyYAML）。`post-merge` 与 merge driver 需要 `git`。
脚本**不发起任何网络请求**,不上传任何内容。

## 日常使用

| 场景 | 你说 |
| :--- | :--- |
| 记录 | "记录一下,认证方案从 JWT 改成 OAuth2 了" |
| 查询 | "为什么当初从 JWT 迁到 OAuth2?" / "导出需求是谁牵头改的?" / "认证这块的演进史" |
| 确认草稿 | "确认一下 2026-08-01-oauth2-migration 那条记录" |
| 手工重建索引 | `python3 .claude/hooks/evolog-index.py` |

自动兜底:完成重构 / 迁移类任务后,Stop hook 会在本轮结束前提醒模型补录一条 `draft` 记录。

## 配置（`.claude/evolution-log.json`）

```jsonc
{
  "schema_version": 1,               // 配置与 records.json 的结构版本
  "storage_dir": "docs/evolution",   // 存储位置,也可用环境变量 EVOLOG_DIR 覆盖
  "sensitive_paths": ["src/core/"],  // 快筛的架构敏感路径,按项目定制(字符串数组)
  "extra_keywords": [],              // 在内置关键词之外追加快筛词(字符串数组)
  "llm_gate": true,                  // true: 阻断时先让模型自评是否真为方案级变更
                                     // false: 阻断时直接请求补录(误报率更高)
  "auto_hook": true                  // false: 关掉自动兜底,只保留手动记录与查询
}
```

类型写错不会静默生效:数组项写成字符串、布尔项写成 `"false"` 之类,都会回落默认值
并把原因写进 `.claude/cache/evolog/error.log`（`keywords` 若按字符串迭代会退化成
逐字符匹配,几乎每轮误报阻断,所以这一项必须拦住）。

存储位置解析优先级:`EVOLOG_DIR` > `storage_dir` > `docs/evolution`。

## 安全边界

索引脚本会被 git `post-merge` 自动调用,也就是说**合入的仓库内容不可信**。相应约束:

- **拒绝跟随符号链接** —— 输出路径及其每一级父目录都逐级 `lstat` 检查;仓库里合入一个
  指向 `~/.ssh/authorized_keys` 的 `INDEX.md` symlink 不会导致该文件被覆盖,脚本直接退出 1
- **仓库外存储需独立开关** —— 仅由仓库内 `.claude/evolution-log.json` 指定的仓库外路径
  一律拒绝;确需仓库外集中知识库,要用 `EVOLOG_DIR` 环境变量,或显式加
  `--allow-external-storage` / `EVOLOG_ALLOW_EXTERNAL_STORAGE=1`。这两者都不受仓库内容控制
- **原子写入** —— 同目录临时文件 → `fsync` → `os.replace`,中途失败不会留下截断的
  `INDEX.md` 或 `records.json`

选仓库外路径会失去 PR 流转与 CI 校验能力,仅推荐用于多项目集中知识库或密级隔离场景。

## Hook 行为边界

Stop hook 是这个插件唯一会"打断"你的地方,所以它的约束写死在脚本里:

- **opt-in**:项目没有 `.claude/evolution-log.json` 且没有 `EVOLOG_DIR` 时直接放行 ——
  插件装在全局也不会打扰未启用本系统的项目
- **fail-open**:任何内部异常一律放行,错误写入 `.claude/cache/evolog/error.log`
- **单会话至多阻断一次**,并用 `stop_hook_active` 防无限循环
- **定长窗口**:只读 transcript 末尾 200KB,耗时与会话长度无关
- **零外发**:脚本只做规则快筛,命中后把"请先自评是否真为方案级变更"的指令
  回注给**会话内的模型**完成二级判断 —— 不调用任何模型 API,也就没有脱敏与 API Key 问题

## 并发与 Git 协作

- **索引重建**用 `mkdir` 原子锁。拿不到锁的一方不会一走了之,而是留下 `rebuild.pending`
  标记;持锁方收尾时发现标记会再跑一次,避免"后到的记录一直不进索引"
- **`INDEX.md` 冲突**由 `merge=ours` 消解。注意 `merge=ours` 只是"用哪个 driver"的声明,
  driver 本身存在本地 git config 里、不随仓库分发 —— `evolog-init` 会执行
  `git config merge.ours.driver true`,**每个 clone 都要跑一次 init**(或手工执行这条命令),
  否则声明形同虚设
- **已有的 `post-merge`** 不会被覆盖:检测到已存在时只提示你手工补哪一行

## 记录格式

```yaml
---
id: 2026-08-01-jwt-to-oauth2
date: 2026-08-01            # 必填,必须是 YYYY-MM-DD,格式错误的记录不入索引
type: solution_change       # solution_change | requirement_change | migration | decision
title: 认证方案从 JWT 迁移到 OAuth2
from: 自签 JWT + 本地用户表
to: OAuth2 授权码模式 + 统一身份中心
owner: 张三
status: confirmed           # draft | confirmed | superseded
source: manual              # manual | auto_hook
supersedes: []
related: []
---
```

正文固定五节:背景 / 变更原因 / **被否掉的备选方案** / 影响范围 / 决策过程。
第三节是重点 —— 它是最容易丢失、未来最有价值的信息。

`type` / `status` 拼错、`tags` 之类写成标量、`id` 重复,重建时都会打印告警但不丢记录;
只有 `date` 非法才会拒绝入索引(排序依赖它)。记录文件本身才是事实来源,索引不该因为
一个拼错的字段整体失败。

## 团队约定（建议随项目 wiki 发布）

- **记录门槛** —— 满足任一即应记录:改变了对外行为或接口;推翻了此前的技术选型;
  影响多个模块/团队;回滚成本高。普通编码与修 bug 不记。
- **draft 确认** —— `auto_hook` 产生的草稿（INDEX 中 📝 标记）由 owner 在一个工作日内
  确认或删除;未确认草稿不得作为决策依据引用。
- **PR 检查项** —— 涉及方案级变更的 PR 必须附带对应 evolution 记录(可加 CI 校验:
  diff 触及 `sensitive_paths` 时检查本次提交是否包含 `records/` 新增)。
- **安全约定** —— `.claude/`、`.codex/`、`.agents/` 目录的任何变更需指定 maintainer 审批
  (建议配置 CODEOWNERS);hook 信任确认前先读脚本内容。

## 目录结构

```
plugins/evolution-log/
├── .claude-plugin/plugin.json
├── hooks/hooks.json                        # Stop hook 注册(指向 skill 内脚本)
├── skills/evolution-log/                   # 自包含:整个目录可独立分发
│   ├── SKILL.md
│   ├── templates/record.md
│   └── scripts/
│       ├── evolog-check.py                 # Stop hook 判定器(opt-in + fail-open)
│       ├── evolog-index.py                 # 索引重建(幂等、原子写、拒绝 symlink)
│       └── evolog-init.py                  # 项目初始化(幂等,支持 --dry-run)
├── tests/test_evolog.py                    # 71 项自测
└── CHANGELOG.md
```

初始化后在目标项目里长这样:

```
.claude/
├── evolution-log.json                  # 配置
├── hooks/evolog-index.py               # 索引重建(git post-merge 需要)
└── cache/evolog/                       # 会话标记与错误日志(已进 .gitignore)
.agents/skills/evolution-log/           # 仅 --codex:自包含 skill 副本
docs/evolution/
├── INDEX.md                            # 生成物,merge=ours
├── records/*.md                        # 唯一事实来源
└── .cache/records.json                 # 生成物,已进 .gitignore
```

## 自测

```bash
python3 plugins/evolution-log/tests/test_evolog.py
```

71 项,纯标准库、无网络。覆盖:opt-in 门禁与 fail-open、单会话一次、配置类型错误回落、
frontmatter 校验与 id 重复、索引幂等、**symlink 覆盖防护**、**仓库外存储策略**、
并发重建不陈旧、Codex 子目录启动、merge driver 端到端消除 `INDEX.md` 冲突、
已有 hook/settings 不被覆盖、打包结构自包含。
