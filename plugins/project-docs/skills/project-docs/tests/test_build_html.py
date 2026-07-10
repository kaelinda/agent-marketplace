#!/usr/bin/env python3
"""Offline tests for build_html.py — stdlib unittest, no network (mermaid=none)."""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import build_html  # noqa: E402


class TestFrontmatter(unittest.TestCase):
    def test_parse(self):
        meta, body = build_html.parse_frontmatter(
            "---\ntitle: 概览\norder: 1\nicon: 🧭\n---\n正文"
        )
        self.assertEqual(meta["title"], "概览")
        self.assertEqual(meta["order"], "1")
        self.assertEqual(body.strip(), "正文")

    def test_no_frontmatter(self):
        meta, body = build_html.parse_frontmatter("# 标题\n正文")
        self.assertEqual(meta, {})
        self.assertIn("# 标题", body)


class TestInline(unittest.TestCase):
    def test_code_span_not_formatted(self):
        out = build_html.render_inline("run `a **b** c` now")
        self.assertIn("<code>a **b** c</code>", out)

    def test_bold_italic_link(self):
        out = build_html.render_inline("**加粗** *斜体* [doc](https://x.y)")
        self.assertIn("<strong>加粗</strong>", out)
        self.assertIn("<em>斜体</em>", out)
        self.assertIn('href="https://x.y"', out)

    def test_html_escaped(self):
        out = build_html.render_inline("a <script> b")
        self.assertNotIn("<script>", out)


class TestBlocks(unittest.TestCase):
    def test_heading_ids_and_collection(self):
        html_out, headings = build_html.render_markdown("## 系统架构\n\n正文")
        self.assertEqual(headings[0][0], 2)
        self.assertEqual(headings[0][1], "系统架构")
        self.assertIn('<h2 id="', html_out)

    def test_table(self):
        md = "| a | b |\n|---|---|\n| 1 | 2 |"
        html_out, _ = build_html.render_markdown(md)
        self.assertIn("<table>", html_out)
        self.assertIn("<td", html_out)

    def test_nested_list_is_valid_html(self):
        md = "- A\n- B\n  - B1"
        html_out, _ = build_html.render_markdown(md)
        self.assertIn("<li>B\n<ul>", html_out.replace("</li>", "").replace("  ", ""))
        self.assertEqual(html_out.count("<ul>"), html_out.count("</ul>"))

    def test_mermaid_block(self):
        md = "```mermaid\nflowchart LR\n A-->B\n```"
        html_out, _ = build_html.render_markdown(md)
        self.assertIn('<pre class="mermaid">', html_out)
        self.assertIn("A--&gt;B", html_out)

    def test_code_block_escaped(self):
        md = "```js\nif (a < b) {}\n```"
        html_out, _ = build_html.render_markdown(md)
        self.assertIn("a &lt; b", html_out)
        self.assertIn('class="language-js"', html_out)

    def test_blockquote(self):
        html_out, _ = build_html.render_markdown("> 提示\n> 第二行")
        self.assertIn("<blockquote>", html_out)


class TestBuild(unittest.TestCase):
    def test_full_build_offline(self):
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            (d / "01-a.md").write_text(
                "---\ntitle: 概览\norder: 1\nicon: 🧭\nsummary: s\n---\n## 一节\n内容",
                encoding="utf-8",
            )
            (d / "02-b.md").write_text(
                "---\ntitle: 架构\norder: 2\n---\n```mermaid\nflowchart LR\nA-->B\n```",
                encoding="utf-8",
            )
            (d / "stats.json").write_text(
                '{"项目名":"demo","badges":{"语言":"py"}}', encoding="utf-8"
            )
            out = build_html.build(d, d / "index.html", mermaid="none")
            page = out.read_text(encoding="utf-8")
            self.assertIn("demo", page)
            self.assertIn("概览", page)
            self.assertIn('class="badge"', page)
            self.assertIn('pre class="mermaid"', page)
            # order respected: 概览 nav entry before 架构
            self.assertLess(page.index("🧭 概览"), page.index("架构"))

    def test_order_fallback_filename(self):
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            (d / "02-b.md").write_text("---\ntitle: B\n---\nx", encoding="utf-8")
            (d / "01-a.md").write_text("---\ntitle: A\n---\nx", encoding="utf-8")
            docs = build_html.collect_docs(d)
            self.assertEqual([x["title"] for x in docs], ["A", "B"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
