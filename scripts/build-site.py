#!/usr/bin/env python3
"""构建 GitHub Pages 首页。

数据来源（唯一事实来源，无需手工同步）：
  - .claude-plugin/marketplace.json   插件清单（名称 / 描述 / 版本 / 类别 / tags）
  - plugins/<name>/skills/*/SKILL.md  skill 列表与 frontmatter 描述
  - VERSION                           市场版本
  - site/content.json                 首页展示文案（分类中文名 / 状态 / 一句话简介）

产物：
  _site/index.html      单文件页面（CSS/JS 内联，零外部请求）
  _site/favicon.svg
  _site/.nojekyll
  _site/onboarding/     docs/onboarding 的副本（首页「接手文档」入口）

纯标准库，零依赖。用法：python3 scripts/build-site.py [--out _site] [--serve]
"""

from __future__ import annotations

import argparse
import html
import json
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"

FEATURE_ICONS = {
    "spec": '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6"/><path d="M9 15l2 2 4-4"/>',
    "sync": '<path d="M21 12a9 9 0 0 1-9 9 9 9 0 0 1-7.6-4.2"/><path d="M3 12a9 9 0 0 1 9-9 9 9 0 0 1 7.6 4.2"/><path d="M20 3v5h-5"/><path d="M4 21v-5h5"/>',
    "dual": '<rect x="2" y="4" width="13" height="9" rx="2"/><rect x="9" y="11" width="13" height="9" rx="2"/>',
}

STATUS_LABEL = {"stable": "stable", "beta": "beta", "experimental": "experimental"}


# --------------------------------------------------------------------------- helpers
def esc(text: str) -> str:
    """转义为 HTML 文本节点内容。"""
    return html.escape(str(text), quote=False)


def attr(text: str) -> str:
    """转义为 HTML 属性值。"""
    return html.escape(str(text), quote=True)


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def read_frontmatter(path: Path) -> dict:
    """从 SKILL.md 读取极简 YAML frontmatter（只需 name / description）。

    支持 `key: value` 与 `key: >` / `key: |` 折叠块，够用即可，不引入 PyYAML。
    """
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return {}
    match = re.match(r"^---\r?\n(.*?)\r?\n---", text, re.S)
    if not match:
        return {}

    data: dict[str, str] = {}
    key: str | None = None
    block: list[str] = []

    def flush() -> None:
        if key is not None:
            data[key] = " ".join(part.strip() for part in block if part.strip()).strip()

    for line in match.group(1).splitlines():
        head = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", line)
        if head and not line.startswith((" ", "\t")):
            flush()
            key, value = head.group(1), head.group(2).strip()
            block = [] if value in ("", ">", "|", ">-", "|-") else [value]
        elif key is not None:
            block.append(line)
    flush()
    return data


def first_sentence(text: str, limit: int = 110) -> str:
    """从 SKILL.md 描述里截一段可展示的短句（仅作兜底）。"""
    text = re.sub(r"\s+", " ", text).strip()
    for sep in ("。", ". ", "；", "; "):
        idx = text.find(sep)
        if 0 < idx <= limit:
            return text[: idx + (1 if sep in "。；" else 0)].strip()
    return text[:limit].rstrip() + ("…" if len(text) > limit else "")


# --------------------------------------------------------------------------- collect
def collect(content: dict) -> list[dict]:
    market = load_json(ROOT / ".claude-plugin" / "marketplace.json")
    overrides = content.get("plugins", {})
    skill_copy = content.get("skills", {})
    categories = content.get("categories", {})

    plugins: list[dict] = []
    for entry in market.get("plugins", []):
        name = entry["name"]
        over = overrides.get(name, {})
        plugin_dir = ROOT / "plugins" / name

        skills = []
        skills_root = plugin_dir / "skills"
        skill_dirs = sorted(
            (d for d in skills_root.iterdir() if d.is_dir() and (d / "SKILL.md").is_file()),
            key=lambda d: d.name,
        ) if skills_root.is_dir() else []
        for skill_dir in skill_dirs:
            skill_name = skill_dir.name
            fm = read_frontmatter(skill_dir / "SKILL.md")
            desc = skill_copy.get(skill_name) or first_sentence(fm.get("description", ""))
            skills.append({"name": skill_name, "desc": desc or "—"})

        hooks = (plugin_dir / "hooks").exists()
        category = entry.get("category", "other")
        plugins.append(
            {
                "name": name,
                "version": entry.get("version", "0.0.0"),
                "category": category,
                "category_label": categories.get(category, category),
                "status": over.get("status", "beta"),
                "tagline": over.get("tagline") or first_sentence(entry.get("description", ""), 90),
                "description": entry.get("description", ""),
                "tags": entry.get("tags", []),
                "skills": skills,
                "hooks": hooks,
            }
        )
    return plugins


# --------------------------------------------------------------------------- render
def render_features(content: dict) -> str:
    out = []
    for item in content.get("features", []):
        path = FEATURE_ICONS.get(item.get("icon", ""), FEATURE_ICONS["spec"])
        out.append(
            f'''<article class="feature">
        <div class="ico" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">{path}</svg></div>
        <h3>{esc(item["title"])}</h3>
        <p>{item["body"]}</p>
      </article>'''
        )
    return "\n        ".join(out)


def render_filters(plugins: list[dict]) -> str:
    seen: dict[str, str] = {}
    for plugin in plugins:
        seen.setdefault(plugin["category"], plugin["category_label"])
    out = ['<button type="button" data-category="all" aria-pressed="true">全部</button>']
    for key, label in seen.items():
        out.append(f'<button type="button" data-category="{attr(key)}" aria-pressed="false">{esc(label)}</button>')
    return "\n          ".join(out)


def render_cards(plugins: list[dict], repo: str) -> str:
    out = []
    for plugin in plugins:
        name = plugin["name"]
        haystack = " ".join(
            [name, plugin["tagline"], plugin["description"], plugin["category_label"]]
            + plugin["tags"]
            + [s["name"] for s in plugin["skills"]]
            + [s["desc"] for s in plugin["skills"]]
        ).lower()

        skills = "\n          ".join(
            f'<li><code class="sname">{esc(s["name"])}</code><span>{esc(s["desc"])}</span></li>'
            for s in plugin["skills"]
        )
        hook_tag = '<span class="tag">hook</span>' if plugin["hooks"] else ""
        status = plugin["status"]

        out.append(
            f'''<article class="card reveal" data-category="{attr(plugin["category"])}" data-haystack="{attr(haystack)}">
        <div class="card-top">
          <h3><a href="{attr(repo)}/tree/main/plugins/{attr(name)}" target="_blank" rel="noopener noreferrer">{esc(name)}</a></h3>
          <span class="ver">v{esc(plugin["version"])}</span>
        </div>
        <div class="tags">
          <span class="tag cat">{esc(plugin["category_label"])}</span>
          <span class="tag {attr(status)}">{esc(STATUS_LABEL.get(status, status))}</span>
          <span class="tag">{len(plugin["skills"])} skill{"s" if len(plugin["skills"]) != 1 else ""}</span>
          {hook_tag}
        </div>
        <p class="tagline">{esc(plugin["tagline"])}</p>
        <ul class="skills">
          {skills}
        </ul>
        <div class="card-foot">
          <a href="{attr(repo)}/tree/main/plugins/{attr(name)}" target="_blank" rel="noopener noreferrer">查看源码 →</a>
          <code class="install-cmd">/plugin install {esc(name)}@manji</code>
        </div>
      </article>'''
        )
    return "\n        ".join(out)


def render_commands(content: dict) -> str:
    out = []
    for row in content.get("commands", []):
        def cell(value: str) -> str:
            return "—" if value.strip() == "—" else f"<code>{esc(value)}</code>"

        out.append(
            f'<tr><td>{esc(row["action"])}</td><td>{cell(row["claude"])}</td><td>{cell(row["codex"])}</td></tr>'
        )
    return "\n            ".join(out)


def render_roadmap(content: dict) -> str:
    check = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 6L9 17l-5-5"/></svg>'
    out = []
    for item in content.get("roadmap", []):
        done = bool(item.get("done"))
        out.append(
            f'<li class="{"done" if done else ""}">'
            f'<span class="box" aria-hidden="true">{check if done else ""}</span>'
            f'<span>{esc(item["text"])}</span></li>'
        )
    return "\n            ".join(out)


# --------------------------------------------------------------------------- build
def build(out_dir: Path) -> Path:
    content = load_json(SITE / "content.json")
    site_meta = content["site"]
    repo = site_meta["repo"].rstrip("/")
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()

    plugins = collect(content)
    skill_total = sum(len(p["skills"]) for p in plugins)
    hook_total = sum(1 for p in plugins if p["hooks"])

    tokens = {
        "TITLE": esc(site_meta["title"]),
        "DESCRIPTION": attr(site_meta["description"]),
        "URL": attr(site_meta["url"]),
        "REPO": attr(repo),
        "HERO_TITLE": site_meta["hero_title"],
        "HERO_SUBTITLE": site_meta["hero_subtitle"],
        "VERSION": esc(version),
        "PLUGIN_COUNT": str(len(plugins)),
        "SKILL_COUNT": str(skill_total),
        "HOOK_COUNT": str(hook_total),
        "FEATURES": render_features(content),
        "FILTERS": render_filters(plugins),
        "CARDS": render_cards(plugins, repo),
        "COMMAND_ROWS": render_commands(content),
        "ROADMAP": render_roadmap(content),
        "BUILT_AT": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "STYLES": (SITE / "styles.css").read_text(encoding="utf-8"),
        "SCRIPT": (SITE / "app.js").read_text(encoding="utf-8"),
    }

    page = (SITE / "template.html").read_text(encoding="utf-8")
    for key, value in tokens.items():
        page = page.replace("{{" + key + "}}", value)

    leftover = re.findall(r"\{\{([A-Z_]+)\}\}", page)
    if leftover:
        sys.exit(f"[build-site] 模板存在未替换的占位符: {sorted(set(leftover))}")

    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)

    (out_dir / "index.html").write_text(page, encoding="utf-8")
    (out_dir / ".nojekyll").write_text("", encoding="utf-8")
    shutil.copy2(SITE / "favicon.svg", out_dir / "favicon.svg")

    onboarding_src = ROOT / "docs" / "onboarding"
    if (onboarding_src / "index.html").exists():
        shutil.copytree(onboarding_src, out_dir / "onboarding")

    size_kb = (out_dir / "index.html").stat().st_size / 1024
    print(f"[build-site] {out_dir.relative_to(ROOT)}/index.html — {size_kb:.1f} KB")
    print(f"[build-site] {len(plugins)} 插件 / {skill_total} skills / {hook_total} hook 插件 / v{version}")
    return out_dir


def main() -> None:
    parser = argparse.ArgumentParser(description="构建 manji GitHub Pages 首页")
    parser.add_argument("--out", default="_site", help="输出目录（默认 _site）")
    parser.add_argument("--serve", action="store_true", help="构建后启动本地预览服务器")
    parser.add_argument("--port", type=int, default=8000, help="预览端口（默认 8000）")
    args = parser.parse_args()

    out_dir = build((ROOT / args.out).resolve())

    if args.serve:
        import functools
        from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

        handler = functools.partial(SimpleHTTPRequestHandler, directory=str(out_dir))
        print(f"[build-site] http://localhost:{args.port}/  (Ctrl+C 退出)")
        ThreadingHTTPServer(("127.0.0.1", args.port), handler).serve_forever()


if __name__ == "__main__":
    main()
