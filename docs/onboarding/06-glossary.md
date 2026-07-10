---
title: 术语表
order: 6
icon: 📚
summary: 业务与领域词汇 ↔ 代码命名对照
---

## 业务术语

| 术语 | 含义 | 代码中的对应 |
|------|------|-------------|
| Marketplace（市场） | 一份可被 Claude Code 添加的插件注册表仓库 | `.claude-plugin/marketplace.json` |
| Plugin（插件） | 按主题聚合的一组扩展能力，安装/卸载的最小单位 | `plugins/<name>/` + `plugin.json` |
| Skill | 教 Claude 完成一类任务的"执行手册"，对话中自动触发 | `plugins/*/skills/<skill>/SKILL.md` |
| Frontmatter | SKILL.md 顶部的 YAML 元数据，`description` 决定触发 | 每个 `SKILL.md` 头部 `---` 块 |
| Slash command | 用户显式敲 `/xxx` 调用的命令，可与 skill 同名共存 | `plugins/*/commands/*.md` |
| Agent / Subagent | 有独立人设与职责边界的执行体 | `agents/content-publisher/Soul.md` |
| Soul.md | 顶层 agent 的人设文件：我是谁/我做什么/我不做什么 | `agents/content-publisher/Soul.md` |
| References | skill 的按需知识库，运行时才读，不占默认上下文 | `plugins/*/skills/*/references/` |
| 双清单同步 | 新插件要同时改插件清单和市场清单 | `plugin.json` + `marketplace.json` |
| 版本检测 | 用 skill 时顺带检查市场是否有新版本 | `scripts/version-check.sh`、`~/.manji/` |
| Onboarding 文档 | 本套"新手接手"文档，md + HTML 双格式 | `docs/onboarding/`（project-docs 生成） |

## 内部黑话/缩写

| 缩写/黑话 | 全称/出处 | 场景 |
|-----------|----------|------|
| manji / 蛮吉 | 《魁拔》主角，本市场代号 | 市场名、`~/.manji/` 配置目录 |
| 魁拔 | 国产动画，蛮吉的出处 | README 里的命名彩蛋 |
| old-bird / 老鸟 | 资深开发者私房实践 | `plugins/old-bird/` |
| 蒸馏（distill） | 把本机私有配置提炼成可移植模板 | `local-distill-me` skill |
| 零依赖 | Python 只用 stdlib、不 pip install | 全部 `scripts/`，CONTRIBUTING 硬约定 |
| MCP | Model Context Protocol，Claude 的外部工具协议 | `plugins/*/mcps/`（预留） |
| OSS | 阿里云对象存储 | `content-generate:ali-oss` skill |
| media_id | 微信公众号素材/草稿的唯一 ID | `wechat-publisher` 返回值 |
