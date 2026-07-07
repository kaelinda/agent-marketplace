# Cover Image HTML Template System

> 配套 `wechat-cover-html` skill 使用。2026-06-25 实测建立的 6 套模板系统。

## Why this exists

公众号 (WeChat) 技术文章的封面需要「代码片段一等公民」——AI 生成的封面（`image_generate`）在等宽字体渲染、代码高亮、JetBrains Mono 字体支持上一致性差。HTML + Playwright 渲染是当前最可靠的方案，但每次手写 HTML + 上传 OSS + 发飞书是 ~30 行 Python 代码。`wechat-cover-html` skill 封装好了这个流程。

## Available templates (按主题选配色)

| 主题 | 模板 | 主色 |
|---|---|---|
| iOS 27 / SwiftUI / 编译器版本 | `code-card-blue.html` | 蓝-青 `#5e9fff → #5ed4ff` |
| AI 工具 / Agent Skills / Claude / Cursor | `code-card-purple.html` | 紫-靛 `#a78bfa → #6366f1` |
| CI/CD / Bazel / 远程构建 / Linux 工具链 | `code-card-orange.html` | 橙-红 `#fb923c → #f43f5e` |
| LLDB / 终端 / DevTools / 调试器 | `code-card-green.html` | 绿 `#4ade80 → #22c55e` |
| 前端 / UI 设计 / Tailwind / 设计系统 | `code-card-cyan.html` | 青 `#2dd4bf → #5eead4` |
| 纯观点 / 周报 / 综述（无代码） | `text-only-blue.html` | 蓝-青（大字号） |

## Template anatomy (5 zones to customize)

每个 `code-card-*.html` 都有 5 个固定区域（编辑时**保持结构**，改文本就行）：

| # | 区域 | CSS 类 | 内容示例 |
|---|---|---|---|
| 1 | Tag | `.tag` | `AI 编程 · SwiftUI` |
| 2 | Version badge | `.version-badge` | `v 4.0.0` 或 `Xcode 27` |
| 3 | Title (2 lines) | `.title` | 第二行用 `<span class="hl">` 渐变高亮 |
| 4 | Subtitle | `.subtitle` | 1-2 行说明 |
| 5 | Code card | `.code-card > .code-body` | 6-12 行代码 + 8 类语法高亮 token |

## Syntax tokens (8 classes)

```css
.kw  { color: #ff7b72; }   /* keywords (let, var, func, struct) */
.ty  { color: #79c0ff; }   /* types (String, AsyncImage, Task) */
.fn  { color: #d2a8ff; }   /* functions / methods */
.str { color: #a5d6ff; }   /* strings */
.cm  { color: #8b949e; font-style: italic; }   /* comments */
.num { color: #fda4af; font-weight: 700; }    /* numbers */
.pr  { color: #ffa657; }   /* parameters / flags */
.ne  { color: #fca5a5; font-weight: 700; }   /* NEVER / forbidden (only cyan theme) */
```

## Render command

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/wechat-cover-html/scripts/render_cover.py \
  --html ${CLAUDE_PLUGIN_ROOT}/skills/wechat-cover-html/templates/code-card-blue.html \
  --output /tmp/cover.png \
  --upload --slug my-article-20260625 \
  --feishu-chat-id oc_cde2971ca05c08d8b36f4a3f86a6544a \
  --title "..." --summary "..."
```

这一步：渲染 PNG → 上传 OSS → 发飞书 post 消息一条龙。

## Design constraints (DO NOT violate)

- **字号不要改**：标题 34px / 副标题 15px / chip 12px / 代码 12-13px
- **不要 emoji**：Playwright 渲染下部分 emoji 变豆腐方块；用 Unicode 符号（★ · → ◆）
- **代码块 ≤ 12 行**：超过会被卡片裁切
- **feature-chip ≤ 6 个**：超过换行挤压标题
- **作者行必须有**：建立信任 + 区分「AI 自动内容」

## When NOT to use this system

- 用户要 emoji-heavy / 节日风 / 卡通插画风封面 → `image_generate` 更合适
- 9:16 竖版封面（旧版公众号） → 用 `wechat-cover-image` Pillow 路线
- 用户自己提供图 → 直接用 `image_generate` 之外的工具（如 `comfyui`）

## Color palette inspiration origin

6 套配色从 2026-06-23 五篇连续发布实测演化而来：
- 紫色（SwiftUI Agent Skill 首发）+ 蓝（AsyncImage iOS 27）+ 红（Swift 6.4 Concurrency）+ 青（UI Skills 否定式约束）+ 绿（LLDB MCP 终端）+ 橙（Bazel iOS Linux 远程构建）
- 每套配色对应一类文章主题，未来扩 7-12 套时按相同命名规则（`code-card-<color>.html`）

## Files

- `${CLAUDE_PLUGIN_ROOT}/skills/wechat-cover-html/SKILL.md` — skill 规范
- `${CLAUDE_PLUGIN_ROOT}/skills/wechat-cover-html/scripts/render_cover.py` — CLI 工具
- `${CLAUDE_PLUGIN_ROOT}/skills/wechat-cover-html/templates/` — 6 套模板 + README 决策表