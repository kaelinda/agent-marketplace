# Skills — 技术公众号发布流程

> 6 个 skill 组成完整的技术公众号内容生产管线：从内容抓取 → 写作 → 质检 → 审核 → 封面 → 上传 → 发布。

---

## 🏗️ 架构总览

```
┌─────────────────────────────────────────────────────────────────┐
│                    技术公众号发布流程                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ① 内容抓取          ② 文章写作          ③ 写作质检              │
│  tech-content-writer  tech-content-writer  tech-content-writer   │
│  (X/Twitter/URL)      (DeepSeek API)       (banned_word_scan)    │
│       │                    │                    │                │
│       ▼                    ▼                    ▼                │
│  ④ 内容审核          ⑤ 封面图生成         ⑥ 资源上传              │
│  tech-content-audit   wechat-cover-html    aliyun-oss-upload     │
│  (五大维度审查)        wechat-cover-image   (OSS bucket)          │
│       │                    │                    │                │
│       ▼                    ▼                    ▼                │
│  ┌─────────────────────────────────────────────────────┐        │
│  │              ⑦ 发布（飞书 → 公众号）                   │        │
│  │         md-to-html (带图文章渲染 HTML)                 │        │
│  └─────────────────────────────────────────────────────┘        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## 📋 Skill 清单

| # | Skill | 分类 | 用途 | 文件数 |
|---|-------|------|------|--------|
| 1 | [`tech-content-writer`](./creative/tech-content-writer/) | creative | 技术文章写作（DeepSeek API + 段落化 + 禁用词） | 11 |
| 2 | [`tech-content-audit`](./content/tech-content-audit/) | content | 发布前内容审核（五大维度：准确性/实用性/深度/风险/禁止） | 1 |
| 3 | [`wechat-cover-html`](./creative/wechat-cover-html/) | creative | 封面图生成 — HTML + Playwright（代码密集型首选） | 9 |
| 4 | [`wechat-cover-image`](./creative/wechat-cover-image/) | creative | 封面图生成 — Pillow 零依赖（备选方案） | 2 |
| 5 | [`md-to-html`](./productivity/md-to-html/) | productivity | Markdown → 可发布 HTML（MDNice + 开源 CSS 双引擎） | 56 |
| 6 | [`aliyun-oss-upload`](./productivity/aliyun-oss-upload/) | productivity | 阿里云 OSS 上传（ossutil + Python SDK） | 1 |

## 🔗 依赖关系

```
tech-content-writer
  ├── scripts/banned_word_scan.py    # 禁用词扫描（写作时内置调用）
  ├── references/deepseek-api-script-template.md  # DeepSeek API 调用模板
  ├── references/x-twitter-capture.md             # X/Twitter 内容抓取指南
  └── references/paragraph-wordcount-iteration.md # 段落化 + 字数迭代

tech-content-audit
  └── 依赖 tech-content-writer 的 banned_word_scan.py 做禁用词检查

wechat-cover-html
  ├── scripts/render_cover.py      # Playwright 渲染 + OSS 上传
  └── templates/                   # 6 套配色模板（蓝/紫/橙/绿/青/纯文字）

wechat-cover-image
  └── scripts/gen_cover.py         # Pillow 绘制（20:9 或 9:16）

md-to-html
  ├── scripts/md_to_html.py        # 渲染引擎（30 MDNice + 14 开源主题）
  ├── references/mdnice-themes/    # 30 个 MDNice 主题 CSS
  └── references/theme-hub/        # 14 个开源 CSS 主题

aliyun-oss-upload
  └── 被 wechat-cover-html 的 render_cover.py 内部调用
```

## 🚀 使用方式

### 方式一：Hermes Agent 直接加载

```bash
# 复制到 Hermes skills 目录
cp -r skills/creative/tech-content-writer ~/.hermes/skills/creative/
cp -r skills/content/tech-content-audit ~/.hermes/skills/content/
# ... 其余同理

# 然后在对话中触发
# "写技术文章" → tech-content-writer
# "审核文章"   → tech-content-audit
# "生成封面"   → wechat-cover-html
```

### 方式二：Claude Code 插件安装

```
/plugin install skills@manji
```

### 方式三：独立使用脚本

```bash
# 禁用词扫描
python3 skills/creative/tech-content-writer/scripts/banned_word_scan.py article.md

# 封面图渲染（HTML → PNG）
python3 skills/creative/wechat-cover-html/scripts/render_cover.py \
  --html /tmp/cover.html --output /tmp/cover.png --upload

# Pillow 封面生成
python3 skills/creative/wechat-cover-image/scripts/gen_cover.py \
  --ratio 20x9 --title-line1 "标题" --output /tmp/cover.png

# Markdown → HTML
python3 skills/productivity/md-to-html/scripts/md_to_html.py \
  render article.md --themes 极客黑 --output article.html
```

## ⚙️ 环境要求

| Skill | 依赖 | 说明 |
|-------|------|------|
| tech-content-writer | DeepSeek API Key | `api.deepseek.com/v1`，model: `deepseek-v4-pro` |
| tech-content-audit | 无 | 纯 LLM 审核，无外部依赖 |
| wechat-cover-html | Playwright + Chromium | `pip install playwright && playwright install chromium` |
| wechat-cover-image | Pillow + 中文字体 | macOS 自带 PingFang，Linux 需 Noto Sans CJK |
| md-to-html | Python 3.8+ | 纯标准库 + Pygments（代码高亮） |
| aliyun-oss-upload | oss2 / ossutil | `pip install oss2` 或 `brew install aliyun-cli` |

### 环境变量

```bash
# OSS 上传（所有涉及 OSS 的 skill 共用）
export OSS_AK="your_access_key_id"
export OSS_SK="your_access_key_secret"

# DeepSeek API（tech-content-writer 写作时调用）
export DEEPSEEK_API_KEY="your_api_key"
```

## 📐 目录规范

```
skills/
├── creative/          # 创作类 skill（写作、封面）
├── content/           # 内容治理类 skill（审核、质检）
└── productivity/      # 生产力工具类 skill（格式转换、上传）
```

## ⚠️ 关键 Pitfalls

1. **封面比例**：公众号官方要求 **20:9 横向**（1200×540），不是 9:16 竖版
2. **禁用词扫描**：必须扫描整篇文章（含标题区），不能只扫正文段
3. **OSS AccessKey**：不要硬编码在文件中，统一用环境变量
4. **英文→中文**：「不是X，而是Y」是英文对比结构的自动翻译，每篇初稿几乎必然出现
5. **md-to-html 脚注**：公众号粘贴场景默认开启脚注模式（`<a href>` 会被公众号编辑器剥离）
6. **wechat-cover-html vs wechat-cover-image**：代码密集型文章用 HTML（支持语法高亮），纯观点/综述用 Pillow

## 📝 License

[MIT](../LICENSE) — 各 skill 独立声明，默认与本仓库一致。
