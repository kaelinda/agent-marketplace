# 蛮吉 (manji) — Claude Code 插件市场

> 一个开源的 Claude Code 插件市场，按 [Anthropic 官方 Marketplace 标准](https://docs.claude.com/en/docs/claude-code/plugins) 组织，收录 **agent / skill / command / hook / MCP** 等可复用的扩展能力。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
[![Plugins](https://img.shields.io/badge/plugins-1-blue.svg)](#-插件目录)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-compatible-8A2BE2.svg)](https://docs.claude.com/en/docs/claude-code)

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

### 1. 添加市场

在 Claude Code 里执行：

```
/plugin marketplace add kaelinda/agent-marketplace
```

> 也支持完整的 git URL（HTTPS/SSH）或本地路径：
> `/plugin marketplace add git@github.com:kaelinda/agent-marketplace.git`
> `/plugin marketplace add /path/to/local/clone`

### 2. 浏览 & 安装

```
/plugin                                # 打开交互式插件管理器
/plugin install agents@manji           # 直接安装某个插件
```

### 3. 试用

以 `agents` 插件下的 `cursor-cli` skill 为例，安装后直接在对话里说："用 cursor 帮我 review 一下当前分支"——Claude 会自动激活 skill，调度 Cursor Agent CLI 执行只读审查并返回结果。

---

## 🧰 插件目录

| 插件 | 类别 | 简介 | 状态 |
| --- | --- | --- | --- |
| [`agents`](./plugins/agents) | 外部 AI Agent 调度 | 把任务派发给 Cursor / Codex 等外部 AI CLI，目前含 `cursor-cli` skill（review / task / ask 三模式） | ✅ stable |
| [`core`](./plugins/core) | 市场核心功能 | 版本检测、自动更新、频率控制，每次使用 skill 时自动检查更新 | ✅ stable |

> 计划中：`memory`（跨会话记忆相关）、`docs`（文档生成相关）等主题型插件，每个插件聚合多个相关 skill。
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

---

## 🛠️ 常用命令

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

---

## 🗂️ 仓库结构

```
agent-marketplace/
├── .claude-plugin/
│   └── marketplace.json              # 市场清单（owner / metadata / plugins[]）
├── plugins/
│   ├── agents/                       # 外部 AI Agent 调度类
│   │   ├── .claude-plugin/
│   │   │   └── plugin.json
│   │   ├── README.md
│   │   └── skills/
│   │       └── cursor-cli/
│   │           ├── SKILL.md
│   │           └── scripts/cursor-dispatch.sh
│   └── memory/                       # 规划中：跨会话记忆类
│       └── ...
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

> Made with 🧡 for the Claude Code community.
