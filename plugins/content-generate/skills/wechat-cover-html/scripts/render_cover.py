#!/usr/bin/env python3
"""WeChat 20:9 cover renderer — HTML + Playwright + optional OSS upload + Feishu post.

Usage:
    python3 render_cover.py --html /tmp/cover.html --output /tmp/cover.png
    python3 render_cover.py --html /tmp/cover.html --output /tmp/cover.png --upload --slug foo-20260623
    python3 render_cover.py --html /tmp/cover.html --output /tmp/cover.png --upload --slug foo --feishu-chat-id oc_xxx --title "..." --summary "..."
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


# ---------- OSS config (env-driven; only required when --upload is used) ----------
OSS_AK = os.environ.get("OSS_AK")
OSS_SK = os.environ.get("OSS_SK")
OSS_BUCKET = os.environ.get("OSS_BUCKET", "kaelblog")
OSS_ENDPOINT = os.environ.get("OSS_ENDPOINT", "https://oss-cn-beijing.aliyuncs.com")
OSS_BASE_URL = f"https://{OSS_BUCKET}.{OSS_ENDPOINT.replace('https://', '')}"


def render(html_path: str, output_path: str, width: int = 1200, height: int = 540, scale: int = 2) -> str:
    """Render an HTML file to a PNG via Playwright. Returns absolute output path."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        sys.exit("playwright not installed. pip install playwright && playwright install chromium")

    abs_html = os.path.abspath(html_path)
    if not os.path.isfile(abs_html):
        sys.exit(f"HTML not found: {abs_html}")

    abs_output = os.path.abspath(output_path)
    Path(abs_output).parent.mkdir(parents=True, exist_ok=True)

    file_url = f"file://{abs_html}"
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(
            viewport={"width": width, "height": height},
            device_scale_factor=scale,
        )
        page.goto(file_url, wait_until="networkidle")
        # Extra wait for Google Fonts CDN to settle
        page.wait_for_timeout(2000)
        page.screenshot(path=abs_output, type="png")
        browser.close()

    size_kb = os.path.getsize(abs_output) / 1024
    print(f"✓ Rendered: {abs_output} ({size_kb:.1f} KB, {width*scale}x{height*scale})")
    return abs_output


def upload_to_oss(png_path: str, slug: str) -> str:
    """Upload PNG to the OSS bucket. Returns public URL."""
    if not OSS_AK or not OSS_SK:
        sys.exit("--upload 需要环境变量 OSS_AK 和 OSS_SK（bucket/endpoint 可用 OSS_BUCKET / OSS_ENDPOINT 覆盖）")
    try:
        import oss2
    except ImportError:
        sys.exit("oss2 not installed. Run: pip install oss2")

    auth = oss2.Auth(OSS_AK, OSS_SK)
    bucket = oss2.Bucket(auth, OSS_ENDPOINT, OSS_BUCKET)
    object_key = f"wechat/{slug}.png"
    with open(png_path, "rb") as f:
        bucket.put_object(
            object_key,
            f,
            headers={"Content-Type": "image/png", "Cache-Control": "max-age=86400"},
        )
    url = f"{OSS_BASE_URL}/{object_key}"
    print(f"✓ Uploaded: {url}")
    return url


def send_feishu_post(chat_id: str, title: str, summary: str, cover_url: str) -> bool:
    """Send a post message to Feishu with title + summary + cover URL."""
    post_content = {
        "zh_cn": {
            "title": "公众号文章发布请求",
            "content": [
                [{"tag": "text", "text": "请帮忙发布公众号文章\n\n"}],
                [{"tag": "text", "text": f"标题：{title}\n\n"}],
                [{"tag": "text", "text": f"摘要：{summary}\n\n"}],
                [{"tag": "text", "text": f"封面图：{cover_url}\n\n"}],
                [{"tag": "text", "text": "完整文案见下方消息。"}],
            ],
        }
    }
    content_str = json.dumps(post_content, ensure_ascii=False)
    try:
        result = subprocess.run(
            [
                "lark-cli", "im", "+messages-send",
                "--chat-id", chat_id,
                "--as", "user",
                "--msg-type", "post",
                "--content", content_str,
            ],
            capture_output=True, text=True, timeout=30,
        )
        ok = '"ok": true' in result.stdout or '"code": 0' in result.stdout
        if ok:
            print(f"✓ Feishu post sent to {chat_id}")
            return True
        else:
            print(f"❌ Feishu post failed: {result.stdout[:200]}")
            return False
    except Exception as exc:
        print(f"❌ Feishu post error: {exc}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Render WeChat cover from HTML and optionally upload + send.")
    parser.add_argument("--html", required=True, help="Input HTML file path")
    parser.add_argument("--output", required=True, help="Output PNG file path")
    parser.add_argument("--width", type=int, default=1200, help="Viewport width (default 1200)")
    parser.add_argument("--height", type=int, default=540, help="Viewport height (default 540)")
    parser.add_argument("--scale", type=int, default=2, help="device_scale_factor (default 2 = retina)")
    parser.add_argument("--upload", action="store_true", help="Upload to OSS kaelblog bucket")
    parser.add_argument("--slug", help="OSS object key slug (e.g. swiftui-skill-20260623)")
    parser.add_argument("--feishu-chat-id", help="If set, send post message to this Feishu chat")
    parser.add_argument("--title", help="Title for Feishu post")
    parser.add_argument("--summary", help="Summary for Feishu post")
    args = parser.parse_args()

    if not os.path.isfile(args.html):
        sys.exit(f"HTML file not found: {args.html}")

    # 1. Render
    render(args.html, args.output, args.width, args.height, args.scale)

    # 2. Upload (if requested)
    cover_url = None
    if args.upload:
        if not args.slug:
            # Auto-generate slug from output filename + today's date
            from datetime import datetime
            stem = Path(args.output).stem
            slug = f"{stem}-{datetime.now().strftime('%Y%m%d')}"
        else:
            slug = args.slug
        cover_url = upload_to_oss(args.output, slug)

    # 3. Send Feishu post (if requested)
    if args.feishu_chat_id:
        if not (args.title and args.summary and cover_url):
            sys.exit("--title, --summary required when using --feishu-chat-id; cover URL needs --upload --slug")
        send_feishu_post(args.feishu_chat_id, args.title, args.summary, cover_url)


if __name__ == "__main__":
    main()
