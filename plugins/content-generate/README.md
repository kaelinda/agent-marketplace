# Content Generate Plugin

内容创作与发布相关的技能集合。7 个 skill 覆盖技术公众号内容生产全流程：

```text
① 写作                ② 审核               ③ 封面
tech-content-writer → tech-content-audit → wechat-cover-html / wechat-cover-image
                                                    │
④ 排版                ⑤ 资源上传            ⑥ 发布   ▼
md-to-html      →     ali-oss        →     wechat-publisher（公众号草稿箱）
```

## Skills

### md-to-html

将 Markdown 文章渲染为可直接发布的独立 HTML。内置两套主题引擎：

- **MDNice（内联引擎）**：30 套 MDNice 排版主题，CSS 内联到每个元素上。适合直接粘贴到公众号/知乎。
- **Stylesheet（样式表引擎）**：14 套开源 CSS 主题（GitHub、Sakura、LaTeX、Tufte、赫蹏、minimal 等），整段 CSS 放进 `<style>` 块中。适合博客/独立网页发布。

**快速开始：**

```bash
cd plugins/content-generate/skills/md-to-html

# 列出所有可用主题
python3 scripts/md_to_html.py list-themes

# 单主题 → 干净可发布的 HTML
python3 scripts/md_to_html.py render article.md --themes 极客黑 --output article.html

# Stylesheet 主题（博客/网页），用 slug 选
python3 scripts/md_to_html.py render article.md --themes github-light --output article.html
```

**依赖：** Python 3，可选安装 `pygments` 获得代码语法高亮。

```bash
pip install pygments
```

详情请见 [md-to-html 技能文档](skills/md-to-html/SKILL.md)。

### ali-oss

将文件上传到阿里云 OSS（对象存储）。支持配置多个 bucket 并指定默认 bucket，自动探测 region，
列举 / 删除对象，以及生成预签名分享链接。纯 Python 标准库实现，无需安装 SDK；凭证保存在仓库
之外的 `~/.config/ali-oss/config.json`（权限 `0600`）。

**快速开始：**

```bash
cd plugins/content-generate/skills/ali-oss

# 配置 bucket（region 自动探测）并设为默认
python3 scripts/ali_oss.py add-bucket my-bucket \
  --access-key-id "$ALI_OSS_ACCESS_KEY_ID" \
  --access-key-secret "$ALI_OSS_ACCESS_KEY_SECRET" --default

# 上传文件
python3 scripts/ali_oss.py upload ./cover.png --prefix blog/2026
```

详情请见 [ali-oss 技能文档](skills/ali-oss/SKILL.md)。

### wechat-publisher

将 Markdown / HTML 文章一键发布到**微信公众号草稿箱**。支持 4 套排版主题（reader / codefine /
ocean / chatex）、封面图与正文图片自动上传到微信 CDN、多账号切换（`--account tech|parenting`）。
只创建草稿，不会自动群发，需登录公众号后台预览后发布。

常与同插件的 `md-to-html` 配合：先用 `md-to-html` 渲染出公众号样式 HTML，再用本 skill 投递。

**快速开始：**

```bash
cd plugins/content-generate/skills/wechat-publisher
npm install
cp .env.example .env   # 填入你自己的 WECHAT_APP_ID / WECHAT_APP_SECRET，并配置公众号 IP 白名单

# 测试连接
node src/cli.js test

# 发布 Markdown 到草稿箱
node src/cli.js publish --title "文章标题" --markdown ./article.md --cover ./cover.jpg --theme reader

# 或直接发布手写 HTML
python3 scripts/publish_html.py --file ./article.html --title "文章标题" --cover ./cover.jpg
```

**依赖：** Node.js ≥ 18（ESM），可选 Python 3 + `requests`（HTML 发布方式）。

详情请见 [wechat-publisher 技能文档](skills/wechat-publisher/SKILL.md)。

### tech-content-writer

技术公众号文章写作：无 AI 味、由浅入深、简洁严谨、优先引用官方文档。内置禁用词扫描
（`scripts/banned_word_scan.py`）、DeepSeek API 调用模板、X/Twitter 内容抓取指南、
段落化 + 字数迭代方法论等 9 篇参考资料。

**依赖：** 环境变量 `DEEPSEEK_API_KEY`（写作时调用 DeepSeek API）。

详情请见 [tech-content-writer 技能文档](skills/tech-content-writer/SKILL.md)。

### tech-content-audit

发布前内容审核：技术准确性 / 实用性 / 深度 / 风险标注 / 禁止内容五大维度审查，
输出 ✅ 通过 / ⚠️ 修改 / ❌ 拒绝 结论。纯 LLM 审核，无外部依赖；禁用词检查复用
`tech-content-writer` 的 `banned_word_scan.py`。

详情请见 [tech-content-audit 技能文档](skills/tech-content-audit/SKILL.md)。

### wechat-cover-html

公众号 20:9 封面图生成 — HTML + Playwright 管线，**代码密集型文章首选**（封面上能渲染真实
Swift/JS/Python 语法高亮代码）。内置 6 套配色模板（蓝/紫/橙/绿/青/纯文字），输出
1200×540（2x retina）PNG，可选 `--upload` 直传 OSS。

**快速开始：**

```bash
cp ${CLAUDE_PLUGIN_ROOT}/skills/wechat-cover-html/templates/code-card-blue.html /tmp/cover.html
# ...编辑标题与代码片段后渲染：
python3 ${CLAUDE_PLUGIN_ROOT}/skills/wechat-cover-html/scripts/render_cover.py \
  --html /tmp/cover.html --output /tmp/cover.png
```

**依赖：** `pip install playwright && playwright install chromium`；上传需 `OSS_AK` / `OSS_SK`
（bucket / endpoint 可用 `OSS_BUCKET` / `OSS_ENDPOINT` 覆盖）。

详情请见 [wechat-cover-html 技能文档](skills/wechat-cover-html/SKILL.md)。

### wechat-cover-image

公众号封面图生成 — Pillow 纯本地绘制（**无外部 AI 图片服务时的备选方案**）。支持 20:9
（1200×540，官方比例）与 9:16（900×1260，竖版）两种比例，标题 / 副标题 / 品牌标 / 视觉主体。

**依赖：** `pip install pillow`；中文字体 macOS 自带 PingFang，Linux 需 Noto Sans CJK。

详情请见 [wechat-cover-image 技能文档](skills/wechat-cover-image/SKILL.md)。

## 关键 Pitfalls

1. **封面比例**：公众号官方要求 **20:9 横向**（1200×540），不是 9:16 竖版
2. **禁用词扫描**：必须扫描整篇文章（含标题区），不能只扫正文段
3. **凭证管理**：OSS AccessKey / DeepSeek API Key 统一用环境变量，不要硬编码
4. **英文→中文**：「不是X，而是Y」是英文对比结构的自动翻译，每篇初稿几乎必然出现
5. **md-to-html 脚注**：公众号粘贴场景默认开启脚注模式（`<a href>` 会被公众号编辑器剥离）
6. **封面方案选择**：代码密集型文章用 `wechat-cover-html`（支持语法高亮），纯观点/综述用 `wechat-cover-image`
