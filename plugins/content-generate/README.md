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
