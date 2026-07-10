---
title: 核心业务流程
order: 4
icon: 🔀
summary: 4 条最重要链路的图解：安装、触发、贡献、版本更新
---

## 流程一：用户安装并使用插件

用户视角的主链路 —— 从添加市场到 skill 干活。

```mermaid
sequenceDiagram
  participant U as 用户
  participant CC as Claude Code
  participant R as manji 仓库

  U->>CC: /plugin marketplace add kaelinda/agent-marketplace
  CC->>R: clone 仓库并读 marketplace.json
  U->>CC: /plugin install content-generate@manji
  CC->>R: 拉取 plugins/content-generate
  U->>CC: 帮我把这篇文章发到公众号草稿箱
  CC->>CC: 匹配 wechat-publisher 的 description
  CC->>R: 读 SKILL.md 并按手册执行 scripts
  CC-->>U: 返回草稿 media_id
```

1. 添加市场：Claude Code 读 `.claude-plugin/marketplace.json` 拿到 `plugins[]`（`.claude-plugin/marketplace.json`）
2. 安装插件：按 `source` 字段定位 `plugins/<name>/`，读 `plugin.json`
3. 对话触发：Claude 用各 skill frontmatter 的 `description` 做语义匹配
4. 执行：按 SKILL.md 正文的手册跑 `scripts/` 下的脚本

**关键文件**：`.claude-plugin/marketplace.json`、`plugins/<name>/.claude-plugin/plugin.json`、`plugins/<name>/skills/<skill>/SKILL.md`

## 流程二：skill 的触发与执行

理解这条链路才能写好 SKILL.md —— 它是本仓库最核心的"业务逻辑"。

```mermaid
flowchart TB
  A[用户一句话请求] --> B{Claude 扫描已装 skill 的 description}
  B -->|命中| C[加载 SKILL.md 正文进上下文]
  B -->|未命中| Z[普通对话处理]
  C --> D[按手册执行: 探索 / 提问 / 跑脚本]
  D --> E{需要辅助材料?}
  E -->|是| F[按需读 references/ 下的文档]
  E -->|否| G[产出结果]
  F --> G
```

要点：`description` 是**触发器**（写场景与触发词），正文是**执行手册**（写步骤与硬性要求），`references/` 是**按需知识**（大而全的细节别塞进 SKILL.md，会浪费上下文）。

**关键文件**：任意 `plugins/*/skills/*/SKILL.md`（好例子：`plugins/playground/skills/mbti-test/SKILL.md`）

## 流程三：贡献一个新插件

维护者/贡献者视角的写路径，也是本仓库最频繁的变更类型。

```mermaid
flowchart LR
  A[创建 plugins/name 目录骨架] --> B[写 plugin.json 清单]
  B --> C[写 skills/*/SKILL.md + scripts + tests]
  C --> D[根 marketplace.json 注册 plugins 条目]
  D --> E[README.md 插件目录表加一行]
  E --> F[VERSION 与 metadata.version 同步升版]
  F --> G[本地联调 + 跑离线测试]
  G --> H[按 CONTRIBUTING 的 checklist 提 PR]
```

1. 目录骨架照抄现有插件（`plugins/playground/` 最小）
2. **双清单 + 门面**三处同步是最易漏的：`marketplace.json`、`README.md`、`VERSION`
3. 脚本零第三方依赖、测试可离线跑，是 review 的硬门槛

**关键文件**：`CONTRIBUTING.md`、`.claude-plugin/marketplace.json`、`README.md`、`VERSION`

## 流程四：市场版本检测与更新

core 插件让所有已装用户能感知市场更新。

```mermaid
sequenceDiagram
  participant SK as 任意 skill 运行时
  participant VC as version-check.sh
  participant CFG as ~/.manji/
  participant R as 远端仓库

  SK->>VC: 使用 skill 时顺带检查
  VC->>CFG: 读缓存 last-update-check
  alt 缓存未过期
    VC-->>SK: 跳过
  else 需要检查
    VC->>R: 比对远端 VERSION
    VC-->>SK: 有新版本 → 4 选项交互
    SK->>CFG: 记录选择 config.json 推迟递增 24h→48h→7d
  end
```

**关键文件**：`scripts/version-check.sh`、`scripts/manji-upgrade.sh`、`plugins/core/skills/version-update/`
