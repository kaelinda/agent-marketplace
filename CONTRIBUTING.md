# 贡献指南

感谢你愿意为 **manji（蛮吉）** 贡献插件！这份文档讲清楚：

- 插件应该长什么样（目录布局 + manifest）
- 各类型组件（agent / command / skill / hook / MCP）写法
- 命名 / 版本 / 依赖约定
- 本地联调 + 自检步骤
- PR Checklist

> 上游标准参考：[Claude Code Plugins 官方文档](https://docs.claude.com/en/docs/claude-code/plugins)。本指南只补充本市场的额外约定。

---

## 📐 插件目录布局

每个插件是 `plugins/<plugin-name>/` 下的一个独立目录，结构如下（**所有子目录都是可选的，按需添加**）：

```
plugins/<plugin-name>/
├── .claude-plugin/
│   └── plugin.json          # 必填：插件清单
├── README.md                # 强烈推荐：插件级说明
├── agents/                  # 可选：subagents
│   └── <agent-name>.md
├── commands/                # 可选：slash commands
│   └── <command-name>.md
├── skills/                  # 可选：skills
│   └── <skill-name>/
│       ├── SKILL.md         # frontmatter 必填 name + description
│       ├── scripts/         # 可选：辅助脚本
│       └── ...              # 可选：参考资料、模板
├── hooks/                   # 可选：hooks
│   └── hooks.json
└── mcps/                    # 可选：MCP 服务器配置
    └── <server-name>.json
```

> 实际示例可直接参考 [`plugins/agents/`](./plugins/agents)（含一个 `cursor-cli` skill）。

---

## 📋 Manifest 规范

### `plugins/<name>/.claude-plugin/plugin.json`

最小可用：

```json
{
  "name": "my-plugin",
  "version": "0.1.0",
  "description": "一句话说清这个插件干什么",
  "author": {
    "name": "你的名字或 ID",
    "email": "可选"
  },
  "license": "MIT",
  "keywords": ["keyword1", "keyword2"]
}
```

可选字段：

| 字段 | 说明 |
| --- | --- |
| `homepage` | 插件主页 URL |
| `repository` | 源码仓库地址（如果插件代码也托管在外部） |
| `bugs` | issue 地址 |
| `engines.claude-code` | 兼容的 Claude Code 版本范围（如 `">=2.0.0"`） |

### 在根 `marketplace.json` 注册

每个插件必须在 `.claude-plugin/marketplace.json` 的 `plugins[]` 数组中注册一条：

```json
{
  "name": "my-plugin",
  "source": "./plugins/my-plugin",
  "description": "插件做什么 ……",
  "version": "0.1.0",
  "category": "agents",
  "tags": ["tag1", "tag2"]
}
```

> `source` 必须是相对仓库根的路径，且与 `plugins/<name>/.claude-plugin/plugin.json` 中的 `name` 一致。

---

## 🧩 各类型组件

### 1. Agent（subagents/）

文件：`agents/<agent-name>.md`，frontmatter 描述身份与触发条件，正文是系统 prompt。

```markdown
---
name: my-reviewer
description: 在用户要求做严格代码审查时使用
tools: Read, Grep, Bash
---

你是一名严格的代码审查官，遵循以下原则：……
```

### 2. Command（commands/）

文件：`commands/<command-name>.md`，用户输入 `/<command-name>` 即可触发。

```markdown
---
description: 把当前 diff 用 cursor 跑一遍 review
argument-hint: [base-branch]
---

请使用 agents 插件下的 cursor-cli skill 的 review 模式，对当前分支相对 $1 的 diff 做安全和性能审查……
```

### 3. Skill（skills/）

文件：`skills/<skill-name>/SKILL.md`，**frontmatter 的 `description` 决定 Claude 何时主动激活**——把触发场景写清楚，越具体越容易命中。

```markdown
---
name: my-skill
description: >
  当用户提到 X / Y / Z 时使用。具体场景：
  (1) ...
  (2) ...
---

# 主体内容（指导 Claude 怎么做）
...
```

附属脚本放 `skills/<skill-name>/scripts/`，用 `bash "<skill_dir>/scripts/foo.sh"` 调用即可（Claude Code 会替换 `<skill_dir>`）。

### 4. Hook（hooks/）

文件：`hooks/hooks.json`，结构与 Claude Code 全局 hooks 一致：

```json
{
  "PreToolUse": [
    {
      "matcher": "Bash",
      "hooks": [
        { "type": "command", "command": "echo \"about to run bash\"" }
      ]
    }
  ]
}
```

### 5. MCP（mcps/ 或 .mcp.json）

参考官方 MCP 配置格式：

```json
{
  "mcpServers": {
    "my-server": {
      "command": "node",
      "args": ["server.js"]
    }
  }
}
```

---

## 🏷️ 命名 / 版本约定

- **插件名**：`kebab-case`，与所在目录名一致，与 `plugin.json.name`、`marketplace.json` 里的 `name` 三处保持一致
- **版本**：遵循 [SemVer](https://semver.org/)，从 `0.1.0` 起步；破坏性改动升 major
- **避免**：用 `nc-`、`org-` 等内部前缀；插件应在公开市场场景下"自包含"
- **关键词**：`keywords` 至少 3 个，便于检索

---

## 🚫 自包含原则（重要）

插件**不允许**：

- 依赖仓库外的私有脚本、私有 MCP 服务、内部 API
- 默认上传任何用户数据到第三方
- 在未提示的情况下做写操作（写文件、改 git、调外部接口都要先告知用户）

如果插件需要外部依赖（如 `cursor-cli` skill 依赖 `cursor` CLI 和 `jq`），必须：

1. 在插件 README 中明确列出依赖
2. 在主入口（SKILL.md / agent prompt）里包含**前置检查**逻辑
3. 缺失依赖时给出清晰的安装提示，而不是直接报错退出

---

## 🧪 本地联调

把仓库当作本地市场加载：

```bash
# 在另一个项目里
claude
> /plugin marketplace add /Users/you/path/to/agent-marketplace
> /plugin install <your-plugin>@manji
```

修改后：

```
/plugin marketplace update manji
```

> 推荐另开一个空白测试仓库做联调，避免污染真实项目。

---

## ✅ 自检 Checklist（提 PR 前过一遍）

- [ ] `plugins/<name>/.claude-plugin/plugin.json` 存在且 JSON 合法
- [ ] `name` / 目录名 / `marketplace.json` 中三处一致
- [ ] `version` 是合法 SemVer
- [ ] 在根 `marketplace.json` 的 `plugins[]` 注册了入口
- [ ] 写了 `plugins/<name>/README.md`，含：能干什么 / 触发场景 / 依赖 / 用法示例
- [ ] 没有依赖任何私有 / 内部基础设施
- [ ] 在自己机器上跑通了 `/plugin install <name>@manji` + 一个真实用例
- [ ] （可选）提供截图或文字示例放进 PR description

JSON 校验小命令：

```bash
python3 -c "import json,sys; [json.load(open(p)) for p in sys.argv[1:]]; print('OK')" \
  .claude-plugin/marketplace.json plugins/<your>/.claude-plugin/plugin.json
```

Bash 脚本语法检查：

```bash
bash -n plugins/<your>/skills/*/scripts/*.sh
```

---

## 📬 PR 流程

1. **Fork** 本仓库
2. 新建分支：`feat/<plugin-name>` 或 `fix/<plugin-name>-<bug>`
3. 提交信息推荐使用 [Conventional Commits](https://www.conventionalcommits.org/)：
   - `feat(agents): 新增 codex-cli skill`
   - `fix(agents/cursor-cli): 修复 jq 不存在时的回退逻辑`
   - `docs: 完善 CONTRIBUTING`
4. 提 PR 到 `main`，描述：
   - **动机**：为什么需要这个插件 / 这个改动
   - **设计要点**：关键决策、依赖
   - **演示**：截图或一段对话示例
5. 等待 review；通过后维护者会合并

---

## 🆘 需要帮助？

- 不确定某个字段怎么写 → 直接看 [`plugins/agents/`](./plugins/agents) 的实现
- 有疑问 → [开 Issue](https://github.com/kaelinda/agent-marketplace/issues)
- 想加个全新类型的能力但不确定能不能进 → 先开 RFC issue 讨论

期待你的贡献 ✨
