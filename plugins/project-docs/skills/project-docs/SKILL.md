---
name: project-docs
description: 为任意代码仓库一键生成「新手接手文档」— 探索仓库后产出 docs/onboarding/ 下 7 份结构化 Markdown（项目概览/架构总览/目录导览/核心业务流程/快速上手/术语表/导读），并渲染成自包含单页 HTML 站点（侧边栏导航 + mermaid 架构图/时序图 + 亮暗主题 + 站内搜索，离线可用）。触发："生成项目文档"、"新人接手文档"、"帮我快速了解这个项目"、"onboarding docs"、"给新同事写份上手指南"、"/project-docs"。支持 --md（仅 Markdown）与 --html（仅重建 HTML）。
---

# project-docs

给一个仓库生成**新手能直接看懂的接手文档**：先系统性探索代码，再产出一套
结构化 Markdown 文档集，最后渲染成一张可离线打开的可视化 HTML 单页。

设计目标（按优先级）：

1. **操作简单** — `/project-docs` 一条命令跑完全流程，零配置。
2. **可视化程度高** — 架构图、时序图（mermaid）强制产出；HTML 带侧边栏
   导航、阅读路线卡片、搜索、亮暗主题、进度条。
3. **双格式** — Markdown 是唯一事实来源（可提交进仓库、可 review），
   HTML 由 md 一键构建（给新人开箱即看）。
4. **新手视角** — 每份文档回答新人真实会问的问题："这项目是干嘛的？"
   "改 X 应该去哪个文件？""第一天怎么把它跑起来？"

## 命令

| 用法 | 行为 |
|------|------|
| `/project-docs` | 完整流程：探索仓库 → 生成 md 文档集 → 构建 HTML → 打开预览 |
| `/project-docs --md` | 只生成/更新 Markdown，不构建 HTML |
| `/project-docs --html` | 不重新探索，直接用现有 md 重建 HTML（改完 md 后刷新用） |
| `/project-docs update` | 增量刷新：对比现有文档与当前代码，只改过时的部分 |
| `/project-docs <path>` | 对指定目录（而非 cwd）生成文档 |

产物固定落在目标仓库的 `docs/onboarding/`（用户明确指定输出目录时除外）。

## 工作流

### Step 1 — 探索仓库（先看懂，再动笔）

按下面的清单系统性探索。大仓库（>500 文件）优先用子代理/并行搜索分摊，
不要逐文件通读：

1. **定位与背景**：README、CONTRIBUTING、docs/、package.json /
   pyproject.toml / go.mod / pom.xml 等 manifest 的 name+description。
2. **目录地图**：`ls` 顶层 + 二级目录，识别每个目录的职责；留意
   monorepo（packages/、apps/、plugins/）。
3. **入口与启动**：main/index/app 入口文件、scripts 命令（dev/build/test）、
   Dockerfile / CI 配置。
4. **核心业务流程**：从入口顺着 3~5 条最重要的调用链读（用户请求怎么进来、
   数据怎么流转、结果怎么出去）。挑"业务含金量最高"的链路，不是最简单的。
5. **数据模型**：schema / model / entity / 数据库迁移文件。
6. **热点与活跃度**：`git log --oneline -20`、`git log --format= --name-only | sort | uniq -c | sort -rn | head -15`
   找最常改动的文件 —— 那是新人最可能要碰的地方。
7. **业务术语**：从命名、注释、README 中收集领域词汇（含中英对照）。

探索结束时，你应当能一句话回答："这个项目为谁解决什么问题，代码从哪进从哪出。"
回答不了就继续读，不要硬编。

### Step 2 — 生成 Markdown 文档集

在 `docs/onboarding/` 下生成 **7 份 md + 1 份 stats.json**。每份 md 必须带
frontmatter（`title` / `order` / `icon` / `summary`），HTML 构建依赖它。
各文件的骨架和内容要求见
[`references/doc-templates.md`](references/doc-templates.md) —— **生成前先读它**。

| 文件 | 内容 | 硬性要求 |
|------|------|---------|
| `README.md` | 导读：阅读路线图、5 分钟速览 | order: 0 |
| `01-overview.md` | 一句话定位、业务背景、解决什么问题、技术栈速览 | 技术栈用表格 |
| `02-architecture.md` | 系统架构、模块划分、数据流 | ≥1 张 mermaid flowchart |
| `03-directory-guide.md` | 带注释目录树 + "改 X 去哪儿"速查表 | 速查表必须有 |
| `04-core-flows.md` | 3~5 条核心业务流程 | 每条 ≥1 张 mermaid sequenceDiagram/flowchart |
| `05-getting-started.md` | 环境、安装、运行、测试、常用命令、第一个练手任务 | 命令可直接复制执行 |
| `06-glossary.md` | 业务/领域术语表（含代码中的对应命名） | 表格形式 |

`stats.json`（hero 区徽章数据）：

```json
{
  "项目名": "仓库名或 manifest name",
  "subtitle": "一句话定位",
  "badges": {"语言": "...", "文件数": "...", "提交数": "...", "最近提交": "YYYY-MM-DD"}
}
```

**Markdown 语法边界**（渲染器是轻量实现，只用这些）：ATX 标题（#~######）、
段落、`**粗体**`/`*斜体*`/`~~删除线~~`/`` `行内码` ``、链接/图片、围栏代码块
（含 ```mermaid）、表格、引用块、有序/无序列表（嵌套用 2 空格缩进）、`---`
分隔线。不要用 HTML 标签、脚注、任务列表、定义列表。

**内容纪律**：

- 一切结论来自代码与 git 历史，**禁止编造**（不确定的写"待确认"并注明依据）。
- 每处提到具体文件都写相对路径（如 `src/api/router.ts`），新人能按图索骥。
- mermaid 节点文字里不要出现 `(` `)` `"`，避免解析报错；中文没问题。
- 文档语言跟随仓库主要语言（中文仓库写中文，英文仓库写英文）。

### Step 3 — 构建 HTML 并预览

```bash
python3 <skill_dir>/scripts/build_html.py docs/onboarding -o docs/onboarding/index.html
open docs/onboarding/index.html   # macOS；Linux 用 xdg-open
```

`<skill_dir>` 是本 SKILL.md 所在目录。脚本零第三方依赖（Python 3.8+ stdlib），
产出**单个自包含 HTML**：侧边栏导航（文档 + h2 锚点）、阅读路线卡片、mermaid
实时渲染、亮暗主题切换、站内搜索、阅读进度条、代码复制按钮。

mermaid.js 处理（`--mermaid`，默认 `auto`）：首次构建联网下载并缓存到
`~/.cache/manji-project-docs/`，之后全程离线内联；无网无缓存时退化为 CDN
标签并在页面提示。`none` = 只展示图表源码。

构建完成后向用户报告：生成了哪些文档、HTML 路径、体积，并主动打开预览。

### update 模式

已存在 `docs/onboarding/` 时：

1. 读现有文档 + `git log --since` 上次生成时间（stats.json 的最近提交字段）。
2. 只重写内容过时的章节，保留用户手工修改（diff 前先确认没有覆盖风险）。
3. 重建 HTML。

## 质量自检（交付前过一遍）

- [ ] 7 份 md 全部有 frontmatter，order 连续
- [ ] 02/04 的 mermaid 图在 HTML 里渲染成功（打开检查，不是猜）
- [ ] "改 X 去哪儿"速查表 ≥ 5 行
- [ ] 05 的命令在本机验证过至少启动/测试其一
- [ ] 新人视角通读：无第一次出现却不解释的黑话
- [ ] HTML 打开后侧边栏、搜索、主题切换正常

## 测试

```bash
python3 <skill_dir>/tests/test_build_html.py
```

离线运行（mermaid=none），覆盖 frontmatter、行内/块级渲染、列表嵌套、
mermaid 块、整页构建与排序。
