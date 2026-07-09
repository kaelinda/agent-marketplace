---
title: 目录导览
order: 3
icon: 🗂️
summary: 带注释的目录树 + 改哪儿速查表
---

## 目录树

```text
agent-marketplace/
├── .claude-plugin/
│   └── marketplace.json     # 市场清单：owner / metadata.version / plugins[] 注册表
├── plugins/                 # 全部插件（每个目录 = 一个可独立安装的插件）
│   ├── core/                # 版本检测与自动更新
│   ├── agents/              # 外部 AI Agent 调度（cursor-cli）
│   ├── memory/              # 跨会话记忆（5 skill + schema + docs）
│   ├── content-generate/    # 公众号内容全流程（7 skill）
│   ├── playground/          # 趣味实验（mbti-test）
│   ├── old-bird/            # 私房工作流蒸馏（local-distill-me）
│   └── project-docs/        # 新手接手文档生成（本文档的生产者）
├── agents/
│   └── content-publisher/   # 顶层 agent 人设（Soul.md，纯执行型发布 agent）
├── scripts/
│   ├── version-check.sh     # 市场版本检查（缓存 ~/.manji/）
│   └── manji-upgrade.sh     # 市场更新执行
├── docs/
│   └── onboarding/          # 本套新手文档（project-docs skill 生成）
├── data/                    # 预留数据目录（当前为空）
├── CLAUDE.md                # 本仓库的 Claude 指令（skill 路由规则）
├── CONTRIBUTING.md          # 贡献指南：插件布局 / manifest 规范 / PR checklist
├── README.md                # 市场门面：快速上手 + 插件目录表
└── VERSION                  # 市场版本号（与 marketplace.json 同步）
```

插件内部的标准布局（以 project-docs 为例）：

```text
plugins/project-docs/
├── .claude-plugin/plugin.json   # 插件清单（name/version/description/keywords）
├── README.md                    # 插件级说明
└── skills/project-docs/
    ├── SKILL.md                 # skill 定义：frontmatter 触发词 + 执行手册
    ├── scripts/build_html.py    # 辅助脚本（纯 stdlib）
    ├── references/              # 给 Claude 按需读取的参考资料
    └── tests/                   # 离线单测
```

## 改 X 去哪儿

| 我想… | 去这里 | 提示 |
|-------|--------|------|
| 新增一个插件 | `plugins/<新名字>/` | 照抄 `plugins/playground/` 的骨架；别忘了下面两行 |
| 注册插件到市场 | `.claude-plugin/marketplace.json` | `plugins[]` 加一条 + `metadata.version` 升版 |
| 让新插件出现在门面 | `README.md` 插件目录表 | 状态列标 🆕 |
| 给现有插件加 skill | `plugins/<name>/skills/<skill>/SKILL.md` | frontmatter `name`+`description` 必填 |
| 改 skill 触发条件 | 对应 `SKILL.md` 的 frontmatter `description` | 触发词写具体场景 + 中英文示例 |
| 改版本检测逻辑 | `scripts/version-check.sh` + `plugins/core/` | 缓存与配置在 `~/.manji/` |
| 更新公众号发布流程 | `plugins/content-generate/skills/wechat-publisher/` | 顶层 `agents/content-publisher/Soul.md` 也可能要同步 |
| 升级市场版本号 | `VERSION` + `marketplace.json` 的 `metadata.version` | 两处必须一致 |
| 看贡献规范 / PR checklist | `CONTRIBUTING.md` | 提 PR 前过一遍 |

## 别碰 / 谨慎碰

- `plugins/old-bird/skills/local-distill-me/assets/` — 成套的模板资产，内部结构被 skill 脚本按路径引用，重命名/挪动会静默破坏移植流程。
- `plugins/memory/schema/` — JSON Schema 被 memory skill 运行时校验引用，改字段要连带改 skill 与测试。
- `data/` — 当前为空的预留目录，别顺手删（git 里以占位存在）。
- 各 skill 的 `references/` — 是给 Claude 运行时按需读取的"知识库"，内容与 SKILL.md 的指引强耦合，改动要两边对照。
