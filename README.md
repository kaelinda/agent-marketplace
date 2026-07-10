# 蛮吉 (manji) — Claude Code 插件市场，Codex 可兼容使用

> 一个开源的 AI 编码插件市场，按 [Anthropic Marketplace 标准](https://docs.claude.com/en/docs/claude-code/plugins) 组织，收录 **agent / skill / command / hook / MCP** 等可复用能力。Claude Code 可原生使用，Codex CLI 可通过兼容模式安装。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
[![Plugins](https://img.shields.io/badge/plugins-7-blue.svg)](#-插件目录)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-compatible-8A2BE2.svg)](https://docs.claude.com/en/docs/claude-code)
[![Codex](https://img.shields.io/badge/Codex-compatibility%20mode-111111.svg)](https://developers.openai.com/codex/)

> **蛮吉** 是国产动画《魁拔》的主角——一个憨直、热血、不知疲倦的小纹耀，从一根小铁棍打到能扛魁拔。希望每个插件都像蛮吉一样：朴实、能打、越战越强。

---

## 📚 目录

- [快速上手](#-快速上手)
- [插件目录](#-插件目录)
- [常用命令](#-常用命令)
- [仓库结构](#-仓库结构)
- [贡献插件](#-贡献插件)
- [路线图](#-路线图)
- [许可证](#-许可证)

---

## 🚀 快速上手

### Claude Code

在 Claude Code 里执行：

```text
/plugin marketplace add kaelinda/agent-marketplace
/plugin install playground@manji
```

> 也支持完整的 git URL（HTTPS/SSH）或本地路径：
> `/plugin marketplace add git@github.com:kaelinda/agent-marketplace.git`
> `/plugin marketplace add /path/to/local/clone`

安装后直接描述任务，Claude Code 会按 `SKILL.md` 的触发条件选择对应能力。例如：

```text
根据我的 Claude Code 和 Codex 会话记录分析 MBTI
```

### Codex CLI（兼容模式）

当前 Codex CLI 可以读取仓库现有的 Claude Marketplace 清单：

```bash
codex plugin marketplace add kaelinda/agent-marketplace
codex plugin add playground@manji
```

添加本地 clone 时，把第一条命令的仓库名换成绝对路径。安装后新开 Codex 会话，让新增 skills 进入会话上下文。

> **兼容边界**：当前版本尚未提供 Codex 原生 `.agents/plugins/marketplace.json` 和 `.codex-plugin/plugin.json`。依赖 `${CLAUDE_PLUGIN_ROOT}`、`AskUserQuestion` 或 `CLAUDE.local.md` 的流程仍偏向 Claude Code；建议先在 Codex 中使用 `playground`、`project-docs`，或不依赖这些约定的独立 skills。完整双端适配计划见 [Codex 双运行时设计](./docs/superpowers/specs/2026-07-10-codex-dual-runtime-design.md)。

---

## 🧰 插件目录

| 插件 | 类别 | 简介 | 状态 |
| --- | --- | --- | --- |
| [`agents`](./plugins/agents) | 外部 AI Agent 调度 | 把任务派发给 Cursor / Codex 等外部 AI CLI，目前含 `cursor-cli` skill（review / task / ask 三模式） | ✅ stable |
| [`core`](./plugins/core) | 市场核心功能 | 版本检测、自动更新、频率控制，每次使用 skill 时自动检查更新 | ✅ stable |
| [`memory`](./plugins/memory) | 跨会话记忆 | 长期记忆持久化 + 召回 + 治理；6 个 skill（recall/capture/commit/doctor/admin/share），支持 OpenViking / MCP / mem0 三后端 | 🟡 v0.2.0 (Phase 2 完成) |
| [`content-generate`](./plugins/content-generate) | 内容创作与发布 | 技术公众号全流程 7 skill：`tech-content-writer`（文章写作）、`tech-content-audit`（发布前审核）、`wechat-cover-html` / `wechat-cover-image`（20:9 封面图）、`md-to-html`（Markdown → 可发布 HTML）、`ali-oss`（阿里云 OSS 上传）、`wechat-publisher`（公众号草稿箱发布，多主题 + 多账号） | ✅ v0.4.0 |
| [`playground`](./plugins/playground) | 趣味/实验 | `mbti-test`（根据本机 Claude Code / Codex 会话历史推断 MBTI，纯本地、不上传、娱乐向） | 🧪 v0.1.0 (experimental) |
| [`old-bird`](./plugins/old-bird) | 配置 / 工作流治理 | `local-distill-me`（把 `CLAUDE.local.md` 私有规则体系**纯本地**蒸馏并移植到项目，多 worktree 零漂移；引导式向导） | 🆕 v0.1.0 |
| [`project-docs`](./plugins/project-docs) | 文档生成 | `project-docs`（一键为任意仓库生成新手接手文档：7 份结构化 md + 自包含单页 HTML，mermaid 架构图/时序图 + 亮暗主题 + 站内搜索 + 阅读进度条，离线可用、零第三方依赖；[本仓库的示例产物](./docs/onboarding/)） | 🆕 v0.1.0 |

> 计划中：更多主题型插件，每个插件聚合多个相关 skill。
>
> 想看到自己的插件出现在这里？ → 跳转 [贡献指南](./CONTRIBUTING.md)

---

## 🔄 版本检测

manji 内置了版本检测功能，参考 [gstack](https://github.com/garrytan/gstack) 的更新方案：

- **自动检查**：每次使用市场中的 skill 时自动检查是否有新版本
- **频率控制**：已是最新时缓存 60 分钟，有新版本时缓存 12 小时
- **推迟递增**：用户选择"稍后提醒"后，推迟时间递增（24h → 48h → 7d）
- **交互式选择**：检测到新版本时提供 4 个选项：
  - 立即更新
  - 自动保持最新（写入配置，今后自动更新）
  - 稍后提醒
  - 不再检查

配置存储在 `~/.manji/config.json`，缓存在 `~/.manji/last-update-check`。

> 上述自动更新交互当前面向 Claude Code。Codex 兼容模式请使用 `codex plugin marketplace upgrade manji` 更新市场快照。

---

## 🛠️ 常用命令

### Claude Code

| 命令 | 作用 |
| --- | --- |
| `/plugin marketplace add <ref>` | 添加一个市场（git URL / `owner/repo` / 本地路径） |
| `/plugin marketplace list` | 查看已添加的市场 |
| `/plugin marketplace update manji` | 拉取本市场最新内容 |
| `/plugin marketplace remove manji` | 移除本市场（不影响已装插件） |
| `/plugin install <name>@manji` | 从本市场安装插件 |
| `/plugin list` | 查看已安装插件 |
| `/plugin uninstall <name>` | 卸载插件 |
| `/plugin` | 打开交互式 UI（推荐） |

### Codex CLI

| 命令 | 作用 |
| --- | --- |
| `codex plugin marketplace add <ref>` | 添加市场（Git 仓库或本地路径） |
| `codex plugin marketplace list` | 查看已添加的市场 |
| `codex plugin marketplace upgrade manji` | 更新 manji 市场快照 |
| `codex plugin marketplace remove manji` | 移除市场 |
| `codex plugin add <name>@manji` | 安装插件 |
| `codex plugin list` | 查看可用及已安装插件 |
| `codex plugin remove <name>@manji` | 卸载插件 |

---

## 🗂️ 仓库结构

```
agent-marketplace/
├── .claude-plugin/
│   └── marketplace.json              # 市场清单（owner / metadata / plugins[]）
├── plugins/
│   ├── agents/                       # 外部 AI Agent 调度
│   ├── core/                         # 市场版本检测与更新
│   ├── memory/                       # 跨会话长期记忆
│   ├── content-generate/             # 内容创作与发布
│   ├── playground/                   # 实验性工具
│   ├── project-docs/                 # 新手接手文档生成
│   └── old-bird/                     # 本地工作流治理
│       ├── .claude-plugin/plugin.json
│       ├── README.md
│       └── skills/<skill>/
│           ├── SKILL.md
│           └── scripts/
├── docs/onboarding/                  # 本仓库示例接手文档
├── CONTRIBUTING.md                   # 贡献指南
├── LICENSE                           # MIT
└── README.md                         # 你正在读的文件
```

> 每个 plugin 是一个**主题包**，聚合若干相关的 skills / commands / agents。一个 plugin 可以只装 skills、只装 commands，或多类型混合——按需取舍。

---

## 🤝 贡献插件

欢迎 PR！请先阅读 **[CONTRIBUTING.md](./CONTRIBUTING.md)** 了解：

- 插件目录布局规范
- `plugin.json` / `marketplace.json` 字段定义
- 命名、版本、依赖约定
- 本地联调与自检流程
- PR Checklist

简版三步：

1. Fork → 在 `plugins/<your-plugin>/` 下放好你的插件
2. 在根 `marketplace.json` 的 `plugins[]` 追加一条记录
3. 提 PR，附上插件演示截图或一段使用示例

---

## 🗺️ 路线图

- [ ] 完成 [Codex 原生双运行时适配](./docs/superpowers/specs/2026-07-10-codex-dual-runtime-design.md)（目标版本 `v0.7.0`）
- [ ] 加一个 `validate.sh` 脚本，CI 里自动校验 manifest schema 与 SKILL.md frontmatter
- [ ] 收录至少一个 **command 类**插件（`/...` 类型）
- [ ] 收录至少一个 **hook 类**插件（PreToolUse / Stop 等）
- [ ] 收录至少一个 **MCP 类**插件
- [ ] 提供英文版 README

> 有想法或想要的插件 → 欢迎开 Issue 提需求。

---

## 📄 许可证

[MIT](./LICENSE) © 2026 kael

> 各插件可在自身 `plugin.json` 中声明独立 license（默认与本仓库一致）。

---

> Made for the Claude Code and Codex community.
