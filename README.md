<div align="center">

# 蛮吉 · manji

**一个开源的 AI 编码插件市场**

按 [Anthropic Marketplace 标准](https://docs.claude.com/en/docs/claude-code/plugins)组织，收录 agent / skill / command / hook / MCP 等可复用能力。<br>
Claude Code 原生支持，Codex CLI 兼容模式可用。

[![License](https://img.shields.io/badge/license-MIT-yellow.svg)](./LICENSE)
[![Version](https://img.shields.io/badge/version-0.10.0-brightgreen.svg)](./VERSION)
[![Plugins](https://img.shields.io/badge/plugins-10-blue.svg)](#插件目录)
[![Skills](https://img.shields.io/badge/skills-24-blue.svg)](#插件目录)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-native-8A2BE2.svg)](https://docs.claude.com/en/docs/claude-code)
[![Codex](https://img.shields.io/badge/Codex-compatible-111111.svg)](https://developers.openai.com/codex/)

</div>

---

## 安装

**Claude Code**

```text
/plugin marketplace add kaelinda/agent-marketplace
/plugin install playground@manji
```

**Codex CLI**（兼容模式）

```bash
codex plugin marketplace add kaelinda/agent-marketplace
codex plugin add playground@manji
```

市场来源支持 `owner/repo`、完整 git URL（HTTPS / SSH）与本地路径：

```text
/plugin marketplace add git@github.com:kaelinda/agent-marketplace.git
/plugin marketplace add /path/to/local/clone
```

安装后直接描述任务即可，运行时会按各 `SKILL.md` 的触发条件自动选择能力：

```text
根据我的 Claude Code 和 Codex 会话记录分析 MBTI
```

> [!NOTE]
> **Codex 兼容边界**：当前尚未提供 Codex 原生的 `.agents/plugins/marketplace.json` 与 `.codex-plugin/plugin.json`。依赖 `${CLAUDE_PLUGIN_ROOT}`、`AskUserQuestion` 或 `CLAUDE.local.md` 的流程仍偏向 Claude Code；在 Codex 中建议优先使用 `playground`、`project-docs` 等不依赖上述约定的插件。完整适配计划见 [Codex 双运行时设计](./docs/superpowers/specs/2026-07-10-codex-dual-runtime-design.md)。

---

## 插件目录

每个 plugin 是一个**主题包**，聚合若干相关的 skills / commands / agents。

| 插件 | 类别 | 一句话简介 | Skills | 版本 | 状态 |
| :--- | :--- | :--- | :---: | :---: | :---: |
| [`core`](./plugins/core) | 市场核心 | 版本检测与自动更新 | 1 | `0.1.0` | stable |
| [`agents`](./plugins/agents) | Agent 调度 | 把任务派发给 Cursor / Codex 等外部 AI CLI | 1 | `0.1.0` | stable |
| [`memory`](./plugins/memory) | 跨会话记忆 | 长期记忆的持久化、召回与治理 | 6 | `0.2.0` | beta |
| [`content-generate`](./plugins/content-generate) | 内容创作 | 技术公众号全流程：写作 → 审核 → 封面 → 排版 → 发布 | 7 | `0.6.0` | stable |
| [`product`](./plugins/product) | 产品分析 | 产品拆解、竞品定位、AI 架构评审、UI 风格逆向 | 4 | `0.3.0` | beta |
| [`design`](./plugins/design) | 设计 | Apple 级 App 图标设计工作流 | 1 | `0.1.0` | beta |
| [`project-docs`](./plugins/project-docs) | 文档生成 | 一键生成新手接手文档（Markdown + 单页 HTML 站点） | 1 | `0.1.0` | beta |
| [`evolution-log`](./plugins/evolution-log) | 演进记录 | 项目演进日志：记录 / 查询「从什么变成什么、为什么、谁牵头」，含 Stop hook 自动兜底 | 1 | `0.2.0` | beta |
| [`old-bird`](./plugins/old-bird) | 工作流治理 | 私有指令体系的本地蒸馏与跨 worktree 移植 | 1 | `0.1.0` | beta |
| [`playground`](./plugins/playground) | 趣味实验 | 从本机会话历史推断 MBTI，纯本地、娱乐向 | 1 | `0.1.0` | experimental |

<details>
<summary><b>展开查看全部 24 个 skill</b></summary>

<br>

**core** — 市场核心

| Skill | 说明 |
| :--- | :--- |
| `version-update` | 使用 skill 时自动检查市场新版本，含频率控制与交互式更新 |

**agents** — 外部 AI Agent 调度

| Skill | 说明 |
| :--- | :--- |
| `cursor-cli` | 调度 Cursor CLI，支持 review / task / ask 三种模式 |

**memory** — 跨会话长期记忆（后端支持 OpenViking / MCP / mem0，identity 默认 fail-closed）

| Skill | 说明 |
| :--- | :--- |
| `memory-recall` | 召回历史记忆 |
| `memory-capture` | 捕获当前会话中值得留存的信息 |
| `memory-commit` | 将记忆写入后端 |
| `memory-doctor` | 记忆库体检与修复 |
| `memory-admin` | 记忆治理与运维 |
| `memory-share` | 跨 agent 记忆共享 |

**content-generate** — 内容创作与发布

| Skill | 说明 |
| :--- | :--- |
| `tech-content-writer` | 技术文章写作，去 AI 味 + 禁用词扫描 |
| `tech-content-audit` | 发布前五大维度内容审核 |
| `wechat-cover-html` | 20:9 封面图，HTML + Playwright 渲染（代码密集型首选） |
| `wechat-cover-image` | 20:9 封面图，Pillow 备选方案 |
| `md-to-html` | Markdown → 可发布 HTML，内置 MDNice 与开源 CSS 双主题引擎 |
| `ali-oss` | 上传文件到阿里云 OSS，支持多 bucket、region 探测、预签名链接 |
| `wechat-publisher` | 发布到公众号草稿箱，多主题排版 + 图片自动上传 + 多账号切换 |

**product** — 产品 / 商业 / 技术 / 设计分析

| Skill | 说明 |
| :--- | :--- |
| `product-teardown` | Principal-PM 级产品拆解，Product / Business / Technology / Strategy 四层框架，输出双语可打印 HTML 报告 |
| `competitor-landscape` | 竞品矩阵与二维定位图 |
| `ai-architecture-review` | AI/Agent 产品技术架构深挖：Model / Tool / Memory / Planning / Agent / Workflow / Evaluation |
| `copy-ui-style` | 从截图 / URL / 代码仓库逆向 UI 设计系统，产出 tokens + AI 编码规则，含 WCAG 对比度检查 |

**design** — 设计

| Skill | 说明 |
| :--- | :--- |
| `apple-icon-studio` | 品牌内核 → 隐喻生成（10 淘 7）→ 形态 → 材质 → 构图 → 色彩 → 对抗式评审（11 条否决 + 6 维加权评分，低于 85 不发）→ 出图 Prompt → Icon Composer 参数。含 10 个行业 Icon DNA 库、5 个完整案例、双语 HTML 简报，以及 1024 母版一键生成 iOS/macOS/Web 图标集 |

**project-docs** — 文档生成

| Skill | 说明 |
| :--- | :--- |
| `project-docs` | 为任意仓库生成 7 份结构化 Markdown 与自包含单页 HTML 站点：mermaid 架构图/时序图、亮暗主题、站内搜索、阅读进度条；离线可用，纯 Python stdlib 零依赖（[本仓库示例产物](./docs/onboarding/)） |

**evolution-log** — 演进记录（唯一一个带 hook 的插件）

| Skill | 说明 |
| :--- | :--- |
| `evolution-log` | 维护随代码库流转的项目演进日志：初始化（幂等，支持 `--dry-run`）/ 记录（七要素 + 冲突检查 + supersedes 链）/ 查询（三跳漏斗控制上下文开销）/ 草稿确认。配套 Stop hook 在每轮结束前规则快筛，命中后把「先自评是否真为方案级变更」回注给会话内模型做二级判定 —— opt-in、fail-open、单会话至多阻断一次、不发起任何网络请求 |

**old-bird** — 配置 / 工作流治理

| Skill | 说明 |
| :--- | :--- |
| `local-distill-me` | 把「`CLAUDE.local.md` 索引 + `~/.claude/shared` 共享规则」私有指令体系纯本地蒸馏并移植到项目，多 worktree 零漂移；引导式向导 |

**playground** — 趣味 / 实验

| Skill | 说明 |
| :--- | :--- |
| `mbti-test` | 根据本机 Claude Code / Codex 会话历史推断 MBTI，支持 `--html` 导出离线报告；纯本地、不上传 |

</details>

> 想看到自己的插件出现在这里？→ [贡献指南](./CONTRIBUTING.md)

---

## 常用命令

| 操作 | Claude Code | Codex CLI |
| :--- | :--- | :--- |
| 添加市场 | `/plugin marketplace add <ref>` | `codex plugin marketplace add <ref>` |
| 查看市场 | `/plugin marketplace list` | `codex plugin marketplace list` |
| 更新市场 | `/plugin marketplace update manji` | `codex plugin marketplace upgrade manji` |
| 移除市场 | `/plugin marketplace remove manji` | `codex plugin marketplace remove manji` |
| 安装插件 | `/plugin install <name>@manji` | `codex plugin add <name>@manji` |
| 查看插件 | `/plugin list` | `codex plugin list` |
| 卸载插件 | `/plugin uninstall <name>` | `codex plugin remove <name>@manji` |
| 交互式 UI | `/plugin` | — |

**版本检测**（参考 [gstack](https://github.com/garrytan/gstack) 的更新方案）

`core` 插件在每次使用 skill 时自动检查新版本：已是最新缓存 60 分钟，有新版本缓存 12 小时；选择「稍后提醒」后推迟时间递增（24h → 48h → 7d）。检测到新版本时可选择立即更新 / 自动保持最新 / 稍后提醒 / 不再检查。配置存于 `~/.manji/config.json`，缓存存于 `~/.manji/last-update-check`。

> 上述交互面向 Claude Code；Codex 兼容模式请用 `codex plugin marketplace upgrade manji` 更新市场快照。

---

## 仓库结构

```
agent-marketplace/
├── .claude-plugin/
│   └── marketplace.json          # 市场清单：owner / metadata / plugins[]
├── plugins/
│   └── <plugin>/                 # 一个主题包
│       ├── .claude-plugin/
│       │   └── plugin.json       # 插件清单
│       ├── skills/<skill>/
│       │   ├── SKILL.md          # 触发条件与执行流程
│       │   └── scripts/
│       └── README.md
├── docs/
│   ├── onboarding/               # 本仓库示例接手文档
│   └── superpowers/specs/        # 设计文档
├── CONTRIBUTING.md
├── LICENSE
├── VERSION
└── README.md
```

---

## 贡献

欢迎 PR。三步走：

1. Fork 仓库，在 `plugins/<your-plugin>/` 下放好你的插件
2. 在根 `marketplace.json` 的 `plugins[]` 追加一条记录
3. 提 PR，附上插件演示截图或一段使用示例

完整的目录布局规范、清单字段定义、命名与版本约定、本地联调流程及 PR Checklist，见 **[CONTRIBUTING.md](./CONTRIBUTING.md)**。

---

## 路线图

- [ ] 完成 [Codex 原生双运行时适配](./docs/superpowers/specs/2026-07-10-codex-dual-runtime-design.md)（目标 `v0.7.0`）
- [ ] 增加 `validate.sh`，在 CI 中校验 manifest schema 与 `SKILL.md` frontmatter
- [ ] 收录至少一个 **command 类**插件
- [x] 收录至少一个 **hook 类**插件（PreToolUse / Stop 等）→ [`evolution-log`](./plugins/evolution-log)
- [ ] 收录至少一个 **MCP 类**插件
- [ ] 提供英文版 README

> 有想法或想要的插件 → 欢迎开 Issue。

---

## 许可证

[MIT](./LICENSE) © 2026 kael。各插件可在自身 `plugin.json` 中声明独立 license，默认与本仓库一致。

---

<div align="center">

**蛮吉** 是国产动画《魁拔》的主角 —— 一个憨直、热血、不知疲倦的小纹耀，从一根小铁棍打到能扛魁拔。<br>
希望每个插件都像蛮吉一样：朴实、能打、越战越强。

<sub>Made for the Claude Code and Codex community.</sub>

</div>
