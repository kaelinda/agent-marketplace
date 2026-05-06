# 蛮吉 (manji) — Claude Code 插件市场

> 一个开源的 Claude Code 插件市场，按 [Anthropic 官方 Marketplace 标准](https://docs.claude.com/en/docs/claude-code/plugins) 组织，收录 **agent / skill / command / hook / MCP** 等可复用的扩展能力。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
[![Plugins](https://img.shields.io/badge/plugins-1-blue.svg)](#-插件目录)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-compatible-8A2BE2.svg)](https://docs.claude.com/en/docs/claude-code)

> **蛮吉** 取自《镇魂街》——一只看似憨厚、实则身经百战的契约兽。希望每个插件都像蛮吉一样：朴实、能打、能扛事。

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
/plugin install cursor-cli@manji       # 直接安装某个插件
```

### 3. 试用

以 `cursor-cli` 为例，安装后直接在对话里说："用 cursor 帮我 review 一下当前分支"——Claude 就会自动调度 Cursor Agent CLI 执行只读审查并返回结果。

---

## 🧰 插件目录

| 插件 | 类别 | 简介 | 状态 |
| --- | --- | --- | --- |
| [`cursor-cli`](./plugins/cursor-cli) | agents / skills | 调度 Cursor Agent CLI 执行代码审查、子任务派发或代码问答（review / task / ask 三模式），自带输出截断保护 | ✅ stable |

> 想看到自己的插件出现在这里？ → 跳转 [贡献指南](./CONTRIBUTING.md)

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
│   └── cursor-cli/                   # 单个插件
│       ├── .claude-plugin/
│       │   └── plugin.json           # 插件清单
│       ├── skills/                   # 可选：skill 列表
│       │   └── cursor-cli/
│       │       ├── SKILL.md
│       │       └── scripts/cursor-dispatch.sh
│       ├── agents/                   # 可选：agent 定义
│       ├── commands/                 # 可选：slash commands
│       ├── hooks/                    # 可选：hooks 配置
│       └── README.md                 # 插件级说明
├── CONTRIBUTING.md                   # 贡献指南
├── LICENSE                           # MIT
└── README.md                         # 你正在读的文件
```

> 一个插件可以只包含 skills、只包含 commands、或多类型混合——按需取舍即可。

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
