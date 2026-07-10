# project-docs — 新手接手文档生成器

一条命令，把任意仓库变成新人能直接看懂的项目：

```
/project-docs
```

Claude 会系统性探索代码（README/manifest → 目录地图 → 入口 → 核心调用链 → 数据模型 → git 热点 → 领域术语），然后在 `docs/onboarding/` 产出 **Markdown + HTML 双格式**的接手文档。

## 产物

| 文件 | 内容 |
|------|------|
| `README.md` | 导读：按角色的阅读路线图 + 5 分钟速览 |
| `01-overview.md` | 项目概览：一句话定位、业务背景、技术栈 |
| `02-architecture.md` | 架构总览：mermaid 架构图、模块职责、数据流 |
| `03-directory-guide.md` | 目录导览：注释目录树 + 「改 X 去哪儿」速查表 |
| `04-core-flows.md` | 核心业务流程：3~5 条调用链，每条配时序图/流程图 |
| `05-getting-started.md` | 快速上手:环境、启动、测试、第一个练手任务 |
| `06-glossary.md` | 术语表：业务词汇 ↔ 代码命名对照 |
| `index.html` | 以上全部渲染成**一张自包含单页**（见下） |

## HTML 可视化

`index.html` 零依赖离线打开，自带：

- 📖 侧边栏导航（文档 + 章节锚点，滚动自动高亮）
- 🗺️ 阅读路线卡片（首屏一眼看全七份文档）
- 🧜 mermaid 实时渲染（架构图/时序图，首次构建联网缓存，之后离线）
- 🌓 亮/暗主题切换（mermaid 图跟随重渲染）
- 🔍 站内搜索（标题 + 正文）
- 📊 阅读进度条、代码一键复制、移动端适配

## 用法

| 命令 | 行为 |
|------|------|
| `/project-docs` | 完整流程：探索 → 生成 md → 构建 HTML → 打开预览 |
| `/project-docs --md` | 只生成 Markdown |
| `/project-docs --html` | 用现有 md 重建 HTML（手改 md 后刷新） |
| `/project-docs update` | 增量刷新过时章节 |
| `/project-docs <path>` | 对指定目录生成 |

也可以直接说自然语言："帮我给这个项目生成一份新人接手文档"。

手动重建 HTML：

```bash
python3 plugins/project-docs/skills/project-docs/scripts/build_html.py docs/onboarding
open docs/onboarding/index.html
```

## 设计原则

1. **操作简单** — 零配置，一条命令端到端。
2. **可视化优先** — 架构图与时序图是硬性要求，不是可选项。
3. **md 是唯一事实来源** — 可 review、可提交、可增量维护；HTML 是一键构建的视图。
4. **新手视角** — 回答真实问题："这是干嘛的？改 X 去哪儿？第一天怎么跑起来？"
5. **零第三方依赖** — 构建脚本 Python 3.8+ stdlib，测试离线可跑。

## 测试

```bash
python3 plugins/project-docs/skills/project-docs/tests/test_build_html.py
```

## 示例

本仓库的 [`docs/onboarding/`](../../docs/onboarding/) 就是这个 skill 对 manji 自身的产物，可直接打开 `index.html` 感受效果。
