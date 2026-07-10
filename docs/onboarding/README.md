---
title: 导读
order: 0
icon: 📖
summary: 5 分钟速览 + 按角色的阅读路线图
---

## 这套文档怎么读

> 一句话：**manji（蛮吉）是一个开源的 Claude Code 插件市场** —— 收录 agent / skill / command / hook / MCP 等可复用扩展，按 Anthropic 官方 Marketplace 标准组织。第一天先读 01 和 05，能把插件装起来再看 02/04。

| 你是谁 | 建议路线 |
|--------|---------|
| 第一天接手仓库的新人 | 01 概览 → 05 快速上手 → 03 目录导览 |
| 想贡献一个新插件 | 04 核心流程（贡献流程）→ 03 速查表 → CONTRIBUTING.md |
| 想改某个现有 skill | 03 目录导览 → 对应插件 README → 06 术语表 |
| 做整体设计/评审 | 02 架构总览 → 04 核心流程 |

## 5 分钟速览

- 这是一个**纯配置 + 脚本**的仓库：没有构建产物、没有服务端，核心是 JSON 清单和一堆 Markdown/Python/Shell。
- 一切从 `.claude-plugin/marketplace.json` 开始 —— 它注册了全部 7 个插件，Claude Code 靠它发现插件。
- 每个插件是 `plugins/<name>/` 下的独立目录，核心资产是 **skill**（`skills/<skill>/SKILL.md` + 可选 `scripts/`、`references/`、`tests/`）。
- 目前 7 个插件、18 个 skill：core（版本检测）、agents（外部 AI 调度）、memory（跨会话记忆）、content-generate（公众号内容全流程）、playground（趣味实验）、old-bird（私房工作流）、project-docs（新手接手文档）。
- 日常两类改动：**新增/升级插件**（动 `plugins/` + `marketplace.json` + `README.md`）和**修 skill 本体**（只动对应 skill 目录）。
- 脚本零第三方依赖是硬约定：Python 只用 stdlib，Shell 用 bash/zsh 兼容写法。
- 有问题先看根 `README.md` 和 `CONTRIBUTING.md`，再看对应插件自己的 README。
