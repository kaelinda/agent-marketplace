# Content Generate Plugin

内容创作与发布相关的技能集合。

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
