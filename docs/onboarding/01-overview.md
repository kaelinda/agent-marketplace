---
title: 项目概览
order: 1
icon: 🧭
summary: 一句话定位、业务背景与技术栈速览
---

## 这是什么项目

**manji（蛮吉）** 是一个开源的 Claude Code 插件市场（plugin marketplace）。它解决的问题很朴素：资深开发者手里攒了很多好用的 AI 工作流（写公众号、跨会话记忆、调度 Cursor/Codex、生成文档、制作技术图解……），但这些"私房工具"散落在各自机器的配置里，别人用不上。manji 把它们按 [Anthropic 官方 Marketplace 标准](https://docs.claude.com/en/docs/claude-code/plugins) 打包成插件，任何人一条命令就能安装复用：

```
/plugin marketplace add kaelinda/agent-marketplace
/plugin install content-generate@manji
```

名字来自国产动画《魁拔》的主角蛮吉 —— 朴实、能打、越战越强。这也是插件的选品标准。

它**不做**的事：不是通用软件包管理器（只服务 Claude Code 生态）、不托管运行时服务（纯静态清单 + 本地脚本）、不收录未经打磨的一次性脚本。

## 核心能力

- **插件分发** — `.claude-plugin/marketplace.json` 注册 11 个插件，Claude Code 原生 `/plugin` 命令即可浏览、安装、更新（对应 `.claude-plugin/`）
- **内容创作全流程** — 技术公众号从写作、审核、封面图到草稿箱发布的 7 个 skill（对应 `plugins/content-generate/`）
- **跨会话长期记忆** — recall/capture/commit/doctor/admin/share 6 个 skill，支持三种后端（对应 `plugins/memory/`）
- **外部 AI Agent 调度** — 把 review/任务派发给 Cursor CLI 等外部工具（对应 `plugins/agents/`）
- **版本检测与自动更新** — 使用任意 skill 时自动检查市场新版本，频率控制 + 推迟递增（对应 `plugins/core/` 与 `scripts/`）
- **新手接手文档生成** — 一键为任意仓库生成 md + HTML 双格式 onboarding 文档（对应 `plugins/project-docs/`）
- **零基础技术图解** — 把 API、架构、数据流和 Agent 解释成少文字、大图的离线 HTML，并生成可校验的 SVG + PNG（对应 `plugins/fireworks-eli5/`）

## 技术栈

| 层 | 技术 | 在仓库里的位置 |
|----|------|--------------|
| 市场清单 | JSON（官方 schema） | `.claude-plugin/marketplace.json` |
| 插件清单 | JSON | `plugins/<name>/.claude-plugin/plugin.json` |
| Skill 定义 | Markdown + YAML frontmatter | `plugins/<name>/skills/<skill>/SKILL.md` |
| 辅助脚本 | Python 3（核心脚本纯 stdlib；渲染器按插件声明） | `plugins/*/skills/*/scripts/` |
| 市场级脚本 | Shell（bash） | `scripts/version-check.sh`、`scripts/manji-upgrade.sh` |
| 测试 | Python unittest（离线运行） | `plugins/*/skills/*/tests/` |

## 项目现状

- 市场版本 **0.11.0**（`VERSION` 与 `marketplace.json` 同步维护）
- 当前基线 43 次提交，最近提交 2026-08-01（文档数据日期：2026-08-25）
- 近期方向：在已有内容、记忆、产品和设计工具之外，新增 `fireworks-eli5`，把 ELI5 解释流程与 Fireworks Tech Graph 的 SVG/PNG 生成合并为可离线分享的 HTML artifact
