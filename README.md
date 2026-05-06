# 蛮吉 (manji) — Claude Code 插件市场

> 一个开源的 Claude Code 插件市场，按官方 Marketplace 标准组织，收录 agent / skill / command / hook / mcp 等扩展能力。

## 安装

在 Claude Code 中执行（替换为你 fork 后的仓库地址）：

```
/plugin marketplace add kaelinda/agent-marketplace
```

之后即可浏览和安装：

```
/plugin install cursor-cli@manji
```

> 也支持 `/plugin marketplace add <git-url>`（HTTPS / SSH / 本地路径都行）。

## 插件目录

| 名称 | 类别 | 说明 |
| --- | --- | --- |
| [`cursor-cli`](./plugins/cursor-cli) | agents | 调度 Cursor Agent CLI 执行代码审查、子任务派发或代码问答（review / task / ask 三模式） |

## 仓库结构

```
agent-marketplace/
├── .claude-plugin/
│   └── marketplace.json          # 市场清单
├── plugins/
│   └── cursor-cli/               # 单个插件目录
│       ├── .claude-plugin/
│       │   └── plugin.json
│       ├── skills/
│       │   └── cursor-cli/
│       │       ├── SKILL.md
│       │       └── scripts/cursor-dispatch.sh
│       └── README.md
├── LICENSE
└── README.md
```

## 贡献新插件

1. 在 `plugins/` 下新建 `<your-plugin>/` 目录
2. 添加 `.claude-plugin/plugin.json`（`name` / `version` / `description` / `author` 必填）
3. 按需添加 `agents/` / `commands/` / `skills/` / `hooks/` / `mcps/`
4. 在根 `marketplace.json` 的 `plugins` 数组里追加一条记录
5. 提 PR

> 请保持插件**自包含**：不要依赖仓库以外的脚本或私有基础设施。

## 许可证

[MIT](./LICENSE)
