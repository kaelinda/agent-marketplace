#!/usr/bin/env python3
"""build_html.py — render an onboarding doc set (markdown files) into one
self-contained, offline-friendly HTML page.

Zero third-party dependencies (Python 3.8+ stdlib only).

Usage:
    python3 build_html.py <docs_dir> [-o index.html] [--title TITLE]
                          [--mermaid auto|cdn|inline|none]

Input convention (produced by the project-docs skill):
    <docs_dir>/*.md          doc sections, ordered by frontmatter `order`
                             (fallback: filename sort). Files starting with
                             `_` are ignored.
    <docs_dir>/stats.json    optional; {"项目名": "...", "badges": {...},
                             "subtitle": "..."} rendered in the hero header.

Each markdown file may start with YAML-ish frontmatter:
    ---
    title: 项目概览
    order: 1
    icon: 🧭
    summary: 一句话说明这份文档讲什么
    ---
"""

import argparse
import html
import json
import os
import re
import sys
import urllib.request
from datetime import datetime
from pathlib import Path

MERMAID_CDN = "https://cdn.jsdelivr.net/npm/mermaid@10.9.1/dist/mermaid.min.js"
MERMAID_CACHE = Path(
    os.environ.get("PROJECT_DOCS_CACHE", Path.home() / ".cache" / "manji-project-docs")
) / "mermaid.min.js"


# ---------------------------------------------------------------------------
# frontmatter
# ---------------------------------------------------------------------------

def parse_frontmatter(text):
    """Return (meta dict, body). Supports a flat `key: value` block."""
    meta = {}
    if text.startswith("---"):
        lines = text.splitlines()
        for i, line in enumerate(lines[1:], start=1):
            if line.strip() in ("---", "..."):
                for raw in lines[1:i]:
                    if ":" in raw:
                        k, _, v = raw.partition(":")
                        meta[k.strip()] = v.strip().strip("\"'")
                return meta, "\n".join(lines[i + 1:])
            if i > 40:  # frontmatter should be short; bail out
                break
    return meta, text


# ---------------------------------------------------------------------------
# markdown rendering (deliberately small: the skill controls the md flavor)
# ---------------------------------------------------------------------------

_slug_counts = {}


def slugify(text):
    s = re.sub(r"<[^>]+>", "", text)
    s = re.sub(r"[^\w一-鿿\- ]+", "", s).strip().lower()
    s = re.sub(r"[\s]+", "-", s) or "sec"
    n = _slug_counts.get(s, 0)
    _slug_counts[s] = n + 1
    return s if n == 0 else f"{s}-{n}"


def render_inline(text):
    """Escape HTML then apply inline markdown."""
    codes = []

    def stash(m):
        codes.append(m.group(1))
        return f"\x00{len(codes) - 1}\x00"

    text = re.sub(r"`([^`]+)`", stash, text)
    text = html.escape(text, quote=False)
    # images before links
    text = re.sub(
        r"!\[([^\]]*)\]\(([^)\s]+)\)",
        r'<img src="\2" alt="\1" loading="lazy">',
        text,
    )
    text = re.sub(
        r"\[([^\]]+)\]\(([^)\s]+)\)",
        r'<a href="\2" target="_blank" rel="noopener">\1</a>',
        text,
    )
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"__([^_]+)__", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<![\w*])\*([^*\n]+)\*(?![\w*])", r"<em>\1</em>", text)
    text = re.sub(r"~~([^~]+)~~", r"<del>\1</del>", text)

    def unstash(m):
        return "<code>" + html.escape(codes[int(m.group(1))], quote=False) + "</code>"

    return re.sub(r"\x00(\d+)\x00", unstash, text)


def _table_align(sep_cells):
    aligns = []
    for c in sep_cells:
        c = c.strip()
        if c.startswith(":") and c.endswith(":"):
            aligns.append("center")
        elif c.endswith(":"):
            aligns.append("right")
        else:
            aligns.append("left")
    return aligns


def _split_row(line):
    return [c.strip() for c in line.strip().strip("|").split("|")]


def render_markdown(body):
    """Return (html, headings) where headings = [(level, text, anchor_id)]."""
    lines = body.splitlines()
    out, headings = [], []
    i, n = 0, len(lines)

    while i < n:
        line = lines[i]
        stripped = line.strip()

        if not stripped:
            i += 1
            continue

        # fenced code / mermaid
        m = re.match(r"^(```+|~~~+)\s*(\S*)\s*$", stripped)
        if m:
            fence, lang = m.group(1)[:3], m.group(2).lower()
            block = []
            i += 1
            while i < n and not lines[i].strip().startswith(fence):
                block.append(lines[i])
                i += 1
            i += 1  # skip closing fence
            code = "\n".join(block)
            if lang == "mermaid":
                out.append(
                    '<div class="mermaid-wrap"><pre class="mermaid">'
                    + html.escape(code, quote=False)
                    + "</pre></div>"
                )
            else:
                cls = f' class="language-{html.escape(lang)}"' if lang else ""
                out.append(
                    f"<pre><code{cls}>" + html.escape(code, quote=False) + "</code></pre>"
                )
            continue

        # heading
        m = re.match(r"^(#{1,6})\s+(.*?)\s*#*\s*$", stripped)
        if m:
            level = len(m.group(1))
            text = m.group(2)
            hid = slugify(text)
            headings.append((level, text, hid))
            out.append(f'<h{level} id="{hid}">{render_inline(text)}</h{level}>')
            i += 1
            continue

        # table
        if (
            stripped.startswith("|")
            and i + 1 < n
            and re.match(r"^\s*\|?[\s:|-]+\|?\s*$", lines[i + 1])
            and "-" in lines[i + 1]
        ):
            header = _split_row(stripped)
            aligns = _table_align(_split_row(lines[i + 1]))
            i += 2
            rows = []
            while i < n and lines[i].strip().startswith("|"):
                rows.append(_split_row(lines[i]))
                i += 1
            th = "".join(
                f'<th style="text-align:{aligns[j] if j < len(aligns) else "left"}">{render_inline(c)}</th>'
                for j, c in enumerate(header)
            )
            trs = []
            for r in rows:
                tds = "".join(
                    f'<td style="text-align:{aligns[j] if j < len(aligns) else "left"}">{render_inline(c)}</td>'
                    for j, c in enumerate(r)
                )
                trs.append(f"<tr>{tds}</tr>")
            out.append(
                '<div class="table-wrap"><table><thead><tr>'
                + th
                + "</tr></thead><tbody>"
                + "".join(trs)
                + "</tbody></table></div>"
            )
            continue

        # blockquote
        if stripped.startswith(">"):
            quote = []
            while i < n and lines[i].strip().startswith(">"):
                quote.append(re.sub(r"^\s*> ?", "", lines[i]))
                i += 1
            inner, _ = render_markdown("\n".join(quote))
            out.append(f"<blockquote>{inner}</blockquote>")
            continue

        # horizontal rule
        if re.match(r"^(\*{3,}|-{3,}|_{3,})$", stripped):
            out.append("<hr>")
            i += 1
            continue

        # lists (nested via indentation, 2 spaces per level)
        m = re.match(r"^(\s*)([-*+]|\d+\.)\s+(.*)$", line)
        if m:
            items = []  # (level, ordered, text)
            while i < n:
                mi = re.match(r"^(\s*)([-*+]|\d+\.)\s+(.*)$", lines[i])
                if not mi:
                    if lines[i].strip() == "" and i + 1 < n and re.match(
                        r"^(\s*)([-*+]|\d+\.)\s+", lines[i + 1]
                    ):
                        i += 1
                        continue
                    break
                indent = len(mi.group(1).replace("\t", "    "))
                level = min(indent // 2, 5)
                ordered = mi.group(2)[0].isdigit()
                items.append((level, ordered, mi.group(3)))
                i += 1
            out.append(_render_list(items))
            continue

        # paragraph
        para = [stripped]
        i += 1
        while i < n and lines[i].strip() and not _is_block_start(lines[i]):
            para.append(lines[i].strip())
            i += 1
        out.append(f"<p>{render_inline(' '.join(para))}</p>")

    return "\n".join(out), headings


def _is_block_start(line):
    s = line.strip()
    return bool(
        re.match(r"^(#{1,6}\s|```|~~~|>|\|)", s)
        or re.match(r"^(\s*)([-*+]|\d+\.)\s+", line)
        or re.match(r"^(\*{3,}|-{3,}|_{3,})$", s)
    )


def _render_list(items):
    out = []

    def rec(i, level):
        tag = "ol" if items[i][1] else "ul"
        out.append(f"<{tag}>")
        while i < len(items):
            lv, _, text = items[i]
            if lv < level:
                break
            if lv == level:
                out.append(f"<li>{render_inline(text)}")
                i += 1
                if i < len(items) and items[i][0] > level:
                    i = rec(i, items[i][0])
                out.append("</li>")
            else:  # deeper than expected (skipped a level) — recurse anyway
                i = rec(i, lv)
        out.append(f"</{tag}>")
        return i

    rec(0, items[0][0])
    return "\n".join(out)


# ---------------------------------------------------------------------------
# mermaid loader
# ---------------------------------------------------------------------------

def mermaid_snippet(mode):
    """Return the <script> block that makes .mermaid pre blocks render."""
    if mode == "none":
        return "<script>window.__mermaidMode='none';</script>"

    if mode in ("auto", "inline"):
        js = None
        if MERMAID_CACHE.exists() and MERMAID_CACHE.stat().st_size > 100_000:
            js = MERMAID_CACHE.read_text(encoding="utf-8", errors="replace")
        elif mode in ("auto", "inline"):
            try:
                print(f"[build_html] downloading mermaid.js -> {MERMAID_CACHE} …", file=sys.stderr)
                MERMAID_CACHE.parent.mkdir(parents=True, exist_ok=True)
                with urllib.request.urlopen(MERMAID_CDN, timeout=15) as r:
                    data = r.read()
                MERMAID_CACHE.write_bytes(data)
                js = data.decode("utf-8", errors="replace")
            except Exception as e:  # offline → fall back to CDN tag
                print(f"[build_html] mermaid download failed ({e}); falling back to CDN tag", file=sys.stderr)
                if mode == "inline":
                    print("[build_html] WARNING: --mermaid inline requested but no cached copy; using CDN", file=sys.stderr)
        if js:
            return "<script>" + js + "</script>"

    # cdn (or auto-fallback)
    return (
        f'<script src="{MERMAID_CDN}" '
        'onerror="window.__mermaidFailed=true;document.documentElement.classList.add(\'mermaid-offline\')">'
        "</script>"
    )


# ---------------------------------------------------------------------------
# page template
# ---------------------------------------------------------------------------

PAGE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__ · 新手上手文档</title>
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Ctext y='.9em' font-size='90'%3E%F0%9F%93%96%3C/text%3E%3C/svg%3E">
<style>
:root{
  --bg:#f7f8fa; --panel:#ffffff; --text:#1f2430; --muted:#6b7280;
  --border:#e5e7eb; --accent:#4f6ef7; --accent-soft:#eef1fe;
  --code-bg:#f3f4f6; --hero1:#4f6ef7; --hero2:#7c4ff7; --shadow:0 1px 3px rgba(16,24,40,.08);
}
[data-theme="dark"]{
  --bg:#0f1117; --panel:#171a23; --text:#e5e7ef; --muted:#9aa1b2;
  --border:#262b38; --accent:#7b93ff; --accent-soft:#1d2440;
  --code-bg:#11141c; --hero1:#3b4fd8; --hero2:#6b3bd8; --shadow:0 1px 3px rgba(0,0,0,.4);
}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;font:15px/1.75 -apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Hiragino Sans GB","Microsoft YaHei",sans-serif;background:var(--bg);color:var(--text)}
a{color:var(--accent);text-decoration:none}
a:hover{text-decoration:underline}
#progress{position:fixed;top:0;left:0;height:3px;width:0;background:linear-gradient(90deg,var(--hero1),var(--hero2));z-index:99}
.layout{display:flex;min-height:100vh}
/* sidebar */
#sidebar{width:280px;flex:none;background:var(--panel);border-right:1px solid var(--border);
  position:sticky;top:0;height:100vh;overflow-y:auto;padding:20px 14px;transition:transform .2s}
#sidebar .brand{font-weight:700;font-size:16px;margin:0 6px 14px;display:flex;align-items:center;gap:8px}
#search{width:100%;padding:8px 12px;border:1px solid var(--border);border-radius:8px;background:var(--bg);
  color:var(--text);font-size:13px;outline:none;margin-bottom:6px}
#search:focus{border-color:var(--accent)}
#search-results{list-style:none;margin:0 0 8px;padding:0;max-height:260px;overflow-y:auto}
#search-results li a{display:block;padding:6px 10px;border-radius:6px;font-size:13px;color:var(--text)}
#search-results li a:hover{background:var(--accent-soft);text-decoration:none}
#search-results .sr-doc{color:var(--muted);font-size:11px;display:block}
nav.toc{margin-top:8px}
nav.toc a{display:block;padding:6px 10px;border-radius:6px;color:var(--text);font-size:14px}
nav.toc a.h2{padding-left:26px;font-size:13px;color:var(--muted)}
nav.toc a:hover{background:var(--accent-soft);text-decoration:none}
nav.toc a.active{background:var(--accent-soft);color:var(--accent);font-weight:600}
/* main */
main{flex:1;min-width:0;padding:32px 48px 96px}
.inner{max-width:880px;margin:0 auto}
.hero{border-radius:16px;padding:40px 44px;color:#fff;background:linear-gradient(120deg,var(--hero1),var(--hero2));
  box-shadow:var(--shadow);margin-bottom:28px}
.hero h1{margin:0 0 6px;font-size:30px}
.hero p{margin:0 0 14px;opacity:.92}
.badges{display:flex;flex-wrap:wrap;gap:8px}
.badge{background:rgba(255,255,255,.18);border:1px solid rgba(255,255,255,.28);border-radius:999px;
  padding:3px 12px;font-size:12.5px;backdrop-filter:blur(2px)}
.gen{font-size:12px;opacity:.75;margin-top:14px}
/* reading map cards */
.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:14px;margin-bottom:36px}
.card{background:var(--panel);border:1px solid var(--border);border-radius:12px;padding:16px 18px;
  box-shadow:var(--shadow);transition:transform .12s,border-color .12s;display:block;color:var(--text)}
.card:hover{transform:translateY(-2px);border-color:var(--accent);text-decoration:none}
.card .ic{font-size:22px}
.card h3{margin:6px 0 4px;font-size:15px}
.card p{margin:0;font-size:13px;color:var(--muted)}
.card .idx{float:right;color:var(--muted);font-size:12px;font-weight:600}
/* doc sections */
section.doc{background:var(--panel);border:1px solid var(--border);border-radius:14px;
  padding:8px 40px 28px;margin-bottom:28px;box-shadow:var(--shadow)}
section.doc>h1{font-size:24px;border-bottom:1px solid var(--border);padding-bottom:12px}
h1,h2,h3,h4{line-height:1.4;scroll-margin-top:24px}
h2{font-size:20px;margin-top:36px;padding-left:12px;border-left:4px solid var(--accent)}
h3{font-size:16.5px}
code{background:var(--code-bg);border:1px solid var(--border);border-radius:5px;padding:1.5px 6px;
  font:12.5px/1.6 "SF Mono",Menlo,Consolas,monospace}
pre{background:var(--code-bg);border:1px solid var(--border);border-radius:10px;padding:16px;
  overflow-x:auto;position:relative}
pre code{background:none;border:none;padding:0;font-size:13px}
pre .copy{position:absolute;top:8px;right:8px;border:1px solid var(--border);background:var(--panel);
  color:var(--muted);border-radius:6px;font-size:11px;padding:3px 9px;cursor:pointer;opacity:0;transition:opacity .15s}
pre:hover .copy{opacity:1}
blockquote{margin:16px 0;padding:10px 18px;border-left:4px solid var(--accent);
  background:var(--accent-soft);border-radius:0 8px 8px 0;color:var(--muted)}
blockquote p{margin:4px 0}
.table-wrap{overflow-x:auto}
table{border-collapse:collapse;width:100%;margin:16px 0;font-size:14px}
th,td{border:1px solid var(--border);padding:8px 12px}
th{background:var(--code-bg)}
img{max-width:100%;border-radius:8px}
hr{border:none;border-top:1px solid var(--border);margin:28px 0}
/* mermaid */
.mermaid-wrap{background:var(--panel);border:1px dashed var(--border);border-radius:10px;
  padding:14px;margin:18px 0;text-align:center;overflow-x:auto}
pre.mermaid{background:none;border:none;text-align:left}
html.mermaid-offline pre.mermaid::before{content:"⚠ 离线且无缓存，无法渲染图表 —— 以下为 mermaid 源码";
  display:block;color:var(--muted);font-size:12px;margin-bottom:8px}
/* floating buttons */
.fab{position:fixed;right:22px;border:1px solid var(--border);background:var(--panel);color:var(--text);
  border-radius:50%;width:40px;height:40px;font-size:17px;cursor:pointer;box-shadow:var(--shadow);z-index:60}
#theme-btn{bottom:76px}
#top-btn{bottom:24px;display:none}
#menu-btn{display:none;position:fixed;left:16px;top:14px;z-index:70}
footer{color:var(--muted);font-size:12.5px;text-align:center;margin-top:40px}
@media (max-width:900px){
  #sidebar{position:fixed;z-index:65;transform:translateX(-100%)}
  #sidebar.open{transform:translateX(0)}
  #menu-btn{display:block}
  main{padding:64px 18px 80px}
  section.doc{padding:4px 20px 20px}
  .hero{padding:28px 24px}
}
</style>
</head>
<body>
<div id="progress"></div>
<button class="fab" id="menu-btn" title="目录">☰</button>
<div class="layout">
<aside id="sidebar">
  <div class="brand">📖 <span>__TITLE__</span></div>
  <input id="search" type="search" placeholder="搜索文档… (标题/正文)">
  <ul id="search-results"></ul>
  <nav class="toc">__NAV__</nav>
</aside>
<main>
<div class="inner">
  <div class="hero">
    <h1>__TITLE__</h1>
    <p>__SUBTITLE__</p>
    <div class="badges">__BADGES__</div>
    <div class="gen">🕒 生成于 __GENERATED__ · 由 manji · project-docs skill 生成</div>
  </div>
  <div class="cards">__CARDS__</div>
  __CONTENT__
  <footer>本页面为自包含离线文档 · 亮/暗主题自动跟随系统，可点右下角切换 · manji project-docs</footer>
</div>
</main>
</div>
<button class="fab" id="theme-btn" title="切换主题">🌓</button>
<button class="fab" id="top-btn" title="回到顶部">↑</button>
__MERMAID_LOADER__
<script>
(function(){
  var root=document.documentElement;
  var saved=localStorage.getItem('pd-theme');
  if(saved){root.setAttribute('data-theme',saved)}
  else if(window.matchMedia&&window.matchMedia('(prefers-color-scheme: dark)').matches){root.setAttribute('data-theme','dark')}

  function currentTheme(){return root.getAttribute('data-theme')==='dark'?'dark':'light'}

  // mermaid
  var mermaidSrc=[];
  function renderMermaid(){
    if(!window.mermaid){root.classList.add('mermaid-offline');return}
    var nodes=document.querySelectorAll('pre.mermaid');
    nodes.forEach(function(n,i){
      if(mermaidSrc[i]===undefined){mermaidSrc[i]=n.textContent}
      n.removeAttribute('data-processed');n.innerHTML='';n.textContent=mermaidSrc[i];
    });
    try{
      mermaid.initialize({startOnLoad:false,securityLevel:'loose',
        theme:currentTheme()==='dark'?'dark':'default'});
      mermaid.run({querySelector:'pre.mermaid'});
    }catch(e){console.warn('mermaid render failed',e)}
  }
  if(document.readyState==='loading'){document.addEventListener('DOMContentLoaded',renderMermaid)}
  else{renderMermaid()}

  // theme toggle
  document.getElementById('theme-btn').addEventListener('click',function(){
    var next=currentTheme()==='dark'?'light':'dark';
    root.setAttribute('data-theme',next);localStorage.setItem('pd-theme',next);
    renderMermaid();
  });

  // progress + back-to-top
  var topBtn=document.getElementById('top-btn');
  window.addEventListener('scroll',function(){
    var h=document.documentElement;
    var p=h.scrollTop/(h.scrollHeight-h.clientHeight)*100;
    document.getElementById('progress').style.width=p+'%';
    topBtn.style.display=h.scrollTop>600?'block':'none';
  },{passive:true});
  topBtn.addEventListener('click',function(){window.scrollTo({top:0,behavior:'smooth'})});

  // mobile sidebar
  var sb=document.getElementById('sidebar');
  document.getElementById('menu-btn').addEventListener('click',function(e){
    e.stopPropagation();sb.classList.toggle('open');
  });
  document.addEventListener('click',function(e){
    if(window.innerWidth<=900&&!sb.contains(e.target)){sb.classList.remove('open')}
  });
  sb.addEventListener('click',function(e){
    if(e.target.tagName==='A'&&window.innerWidth<=900){sb.classList.remove('open')}
  });

  // copy buttons
  document.querySelectorAll('pre').forEach(function(pre){
    if(pre.classList.contains('mermaid'))return;
    var btn=document.createElement('button');btn.className='copy';btn.textContent='复制';
    btn.addEventListener('click',function(){
      var code=pre.querySelector('code');
      navigator.clipboard.writeText(code?code.textContent:pre.textContent).then(function(){
        btn.textContent='已复制 ✓';setTimeout(function(){btn.textContent='复制'},1500);
      });
    });
    pre.appendChild(btn);
  });

  // scroll spy
  var tocLinks=Array.prototype.slice.call(document.querySelectorAll('nav.toc a'));
  var targets=tocLinks.map(function(a){return document.getElementById(a.getAttribute('href').slice(1))}).filter(Boolean);
  var spy=new IntersectionObserver(function(entries){
    entries.forEach(function(en){
      if(en.isIntersecting){
        tocLinks.forEach(function(a){a.classList.remove('active')});
        var link=document.querySelector('nav.toc a[href="#'+en.target.id+'"]');
        if(link){link.classList.add('active')}
      }
    });
  },{rootMargin:'-10% 0px -70% 0px'});
  targets.forEach(function(t){spy.observe(t)});

  // search
  var index=[];
  document.querySelectorAll('section.doc').forEach(function(sec){
    var docTitle=(sec.querySelector('h1')||{}).textContent||'';
    sec.querySelectorAll('h1,h2,h3,p,li').forEach(function(el){
      var anchor=el.closest('[id]')||sec;
      index.push({doc:docTitle,text:el.textContent||'',id:anchor.id,
        heading:/^H[1-3]$/.test(el.tagName)});
    });
  });
  var input=document.getElementById('search'),results=document.getElementById('search-results');
  input.addEventListener('input',function(){
    var q=input.value.trim().toLowerCase();results.innerHTML='';
    if(q.length<1)return;
    var seen={},count=0;
    for(var i=0;i<index.length&&count<12;i++){
      var it=index[i];
      if(it.text.toLowerCase().indexOf(q)===-1)continue;
      var key=it.id+'|'+(it.heading?it.text:it.doc);
      if(seen[key])continue;seen[key]=1;count++;
      var li=document.createElement('li'),a=document.createElement('a');
      a.href='#'+it.id;
      var snippet=it.text.length>42?it.text.slice(0,42)+'…':it.text;
      a.innerHTML='<span class="sr-doc">'+it.doc+'</span>'+snippet.replace(/</g,'&lt;');
      a.addEventListener('click',function(){results.innerHTML='';input.value=''});
      li.appendChild(a);results.appendChild(li);
    }
  });
})();
</script>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# build
# ---------------------------------------------------------------------------

def collect_docs(docs_dir):
    docs = []
    for p in sorted(docs_dir.glob("*.md")):
        if p.name.startswith("_"):
            continue
        meta, body = parse_frontmatter(p.read_text(encoding="utf-8"))
        try:
            order = float(meta.get("order", 10_000))
        except ValueError:
            order = 10_000
        docs.append({
            "path": p,
            "order": order,
            "title": meta.get("title") or p.stem,
            "icon": meta.get("icon", "📄"),
            "summary": meta.get("summary", ""),
            "body": body,
        })
    docs.sort(key=lambda d: (d["order"], d["path"].name))
    return docs


def build(docs_dir, output, title=None, mermaid="auto"):
    docs_dir = Path(docs_dir)
    if not docs_dir.is_dir():
        sys.exit(f"[build_html] docs dir not found: {docs_dir}")

    stats = {}
    stats_file = docs_dir / "stats.json"
    if stats_file.exists():
        try:
            stats = json.loads(stats_file.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"[build_html] ignoring bad stats.json: {e}", file=sys.stderr)

    docs = collect_docs(docs_dir)
    if not docs:
        sys.exit(f"[build_html] no markdown files in {docs_dir}")

    page_title = title or stats.get("项目名") or stats.get("name") or docs_dir.resolve().parent.name
    subtitle = stats.get("subtitle") or stats.get("描述") or "新手快速接手项目 · 业务与架构一页看懂"

    nav_parts, card_parts, content_parts = [], [], []
    for idx, doc in enumerate(docs, start=1):
        sec_id = slugify(f"doc-{doc['path'].stem}")
        body_html, headings = render_markdown(doc["body"])
        # drop a leading duplicate h1 (section header renders the title)
        nav_parts.append(f'<a href="#{sec_id}">{doc["icon"]} {html.escape(doc["title"])}</a>')
        for level, text, hid in headings:
            if level == 2:
                nav_parts.append(f'<a class="h2" href="#{hid}">{html.escape(text)}</a>')
        card_parts.append(
            f'<a class="card" href="#{sec_id}"><span class="idx">{idx:02d}</span>'
            f'<span class="ic">{doc["icon"]}</span>'
            f'<h3>{html.escape(doc["title"])}</h3>'
            f'<p>{html.escape(doc["summary"])}</p></a>'
        )
        content_parts.append(
            f'<section class="doc" id="{sec_id}">'
            f'<h1>{doc["icon"]} {html.escape(doc["title"])}</h1>'
            f"{body_html}</section>"
        )

    badges = stats.get("badges") or {}
    badge_html = "".join(
        f'<span class="badge">{html.escape(str(k))} · {html.escape(str(v))}</span>'
        for k, v in badges.items()
    )

    page = (
        PAGE
        .replace("__TITLE__", html.escape(str(page_title)))
        .replace("__SUBTITLE__", html.escape(str(subtitle)))
        .replace("__BADGES__", badge_html)
        .replace("__NAV__", "\n".join(nav_parts))
        .replace("__CARDS__", "\n".join(card_parts))
        .replace("__CONTENT__", "\n".join(content_parts))
        .replace("__GENERATED__", datetime.now().strftime("%Y-%m-%d %H:%M"))
        .replace("__MERMAID_LOADER__", mermaid_snippet(mermaid))
    )

    out = Path(output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page, encoding="utf-8")
    size_kb = out.stat().st_size / 1024
    print(f"[build_html] wrote {out}  ({size_kb:.0f} KB, {len(docs)} docs)")
    return out


def main():
    ap = argparse.ArgumentParser(description="Render onboarding md docs into one offline HTML page")
    ap.add_argument("docs_dir", help="directory containing the generated *.md docs")
    ap.add_argument("-o", "--output", default=None, help="output HTML path (default: <docs_dir>/index.html)")
    ap.add_argument("--title", default=None, help="page title (default: stats.json 项目名 or parent dir name)")
    ap.add_argument("--mermaid", choices=["auto", "cdn", "inline", "none"], default="auto",
                    help="auto: inline cached/downloaded mermaid.js, fallback CDN; cdn: script tag; "
                         "inline: force inline; none: show diagram source only")
    args = ap.parse_args()
    output = args.output or str(Path(args.docs_dir) / "index.html")
    build(args.docs_dir, output, title=args.title, mermaid=args.mermaid)


if __name__ == "__main__":
    main()
