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
| `evolog-init.py` | 项目初始化:配置、存储骨架、`.gitattributes` / `.gitignore`、`post-merge` |
| Markdown 存储 | `docs/evolution/records/*.md`,进 Git、随 PR 流转、可 review |

`records/` 是唯一事实来源,索引任何时候都可以丢掉重建。

## 安装

```text
/plugin marketplace add kaelinda/agent-marketplace
/plugin install evolution-log@manji
```

装完在目标项目里说一句"**给这个项目初始化演进日志**",skill 会先 `--dry-run`
把要写的文件念一遍,确认后才落盘。也可以手动跑:

```bash
python3 "<plugin>/scripts/evolog-init.py" --dry-run          # 预演
python3 "<plugin>/scripts/evolog-init.py"                    # 插件模式
python3 "<plugin>/scripts/evolog-init.py" --standalone --codex   # 不装插件 / Codex
```

初始化是幂等的,已存在的文件一律不覆盖(除非 `--force`)。

### 两种安装模式

| 模式 | Stop hook 来自 | 适用 |
| :--- | :--- | :--- |
| 插件模式（默认） | 插件目录,不进你的仓库 | 个人使用;团队都装了插件 |
| `--standalone` | 复制进项目 `.claude/hooks/` 并注册 `.claude/settings.json` | 团队成员不都装插件,希望 clone 即生效;Codex 用户加 `--codex` |

两种模式并存也不会重复阻断:插件里的 check 脚本检测到项目自带副本时会主动让位。

> `evolog-index.py` 在两种模式下都会复制一份进项目 —— git 的 `post-merge` 钩子在
> Claude Code 之外运行,必须有项目内副本才能在合并后重建索引。

## 依赖

只需要 `python3`（3.6+,纯标准库,不依赖 PyYAML）。`post-merge` 钩子需要 `git`。
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
  "storage_dir": "docs/evolution",   // 存储位置,也可用环境变量 EVOLOG_DIR 覆盖
                                     // 支持仓库内相对路径或仓库外绝对路径(~ 可用)
  "sensitive_paths": ["src/core/"],  // 快筛的架构敏感路径,按项目定制
  "extra_keywords": [],              // 在内置关键词之外追加快筛词
  "llm_gate": true,                  // true: 阻断时先让模型自评是否真为方案级变更
                                     // false: 阻断时直接请求补录(误报率更高)
  "auto_hook": true                  // false: 关掉自动兜底,只保留手动记录与查询
}
```

存储位置解析优先级:`EVOLOG_DIR` > `storage_dir` > `docs/evolution`。
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

## 记录格式

```yaml
---
id: 2026-08-01-jwt-to-oauth2
date: 2026-08-01
type: solution_change        # solution_change | requirement_change | migration | decision
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

## 团队约定（建议随项目 wiki 发布）

- **记录门槛** —— 满足任一即应记录:改变了对外行为或接口;推翻了此前的技术选型;
  影响多个模块/团队;回滚成本高。普通编码与修 bug 不记。
- **draft 确认** —— `auto_hook` 产生的草稿（INDEX 中 📝 标记）由 owner 在一个工作日内
  确认或删除;未确认草稿不得作为决策依据引用。
- **PR 检查项** —— 涉及方案级变更的 PR 必须附带对应 evolution 记录(可加 CI 校验:
  diff 触及 `sensitive_paths` 时检查本次提交是否包含 `records/` 新增)。
- **安全约定** —— `.claude/`、`.codex/` 目录的任何变更需指定 maintainer 审批
  (建议配置 CODEOWNERS);hook 信任确认前先读脚本内容。

## 目录结构

```
plugins/evolution-log/
├── .claude-plugin/plugin.json
├── hooks/hooks.json                    # Stop hook 注册(${CLAUDE_PLUGIN_ROOT})
├── scripts/
│   ├── evolog-check.py                 # Stop hook 判定器(opt-in + fail-open)
│   ├── evolog-index.py                 # 索引重建(幂等,mkdir 原子锁)
│   └── evolog-init.py                  # 项目初始化(幂等,支持 --dry-run)
├── skills/evolution-log/
│   ├── SKILL.md
│   └── templates/record.md
└── tests/test_evolog.py                # 34 项自测,python3 -m pytest 或直接运行
```

初始化后在目标项目里长这样:

```
.claude/
├── evolution-log.json                  # 配置
├── hooks/evolog-index.py               # 索引重建(git post-merge 需要)
└── cache/evolog/                       # 会话标记与错误日志(建议 gitignore)
docs/evolution/
├── INDEX.md                            # 生成物,merge=ours
├── records/*.md                        # 唯一事实来源
└── .cache/records.json                 # 生成物,建议 gitignore
```

## 自测

```bash
python3 plugins/evolution-log/tests/test_evolog.py
```
