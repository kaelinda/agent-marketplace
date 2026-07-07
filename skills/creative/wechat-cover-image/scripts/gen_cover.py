"""公众号封面图生成器（Pillow 版）。

支持两种比例：
- 9x16 竖版 900x1260（公众号正文封面默认，过去用得多）
- 20x9 横向 1200x540（公众号**官方封面比例**，用户 2026-06-14 反馈，
  新版公众号封面要求 20:9 横向，会被裁成列表卡片图）

用法（9x16 竖版，向后兼容）:
    python3 gen_cover.py \
        --title-line1 "Google 不再卷 AGI 了，" \
        --title-line2 "他们在画 ASI 的地图" \
        --subtitle "从 AGI 到 ASI：四条路径与一个测深线" \
        --top-label "DEEPMIND · FROM AGI TO ASI" \
        --brand "AICoder · 技术洞察" \
        --visual neural-network,formula-paper \
        --formula "E=mc" \
        --output /tmp/cover.png

用法（20x9 横向，公众号官方要求）:
    python3 gen_cover.py \
        --ratio 20x9 \
        --title-line1 "Google 不再卷 AGI 了，" \
        --title-line2 "他们在画 ASI 的地图" \
        --subtitle "从 AGI 到 ASI：四条路径与一个测深线" \
        --top-label "DEEPMIND · FROM AGI TO ASI" \
        --brand "AICoder · 技术洞察" \
        --visual neural-network,formula-paper \
        --formula "E=mc" \
        --right-source "arXiv:2606.12683 · deepmind.google" \
        --output /tmp/cover.png
"""
import argparse
import math
import os
import random
import sys

# 兼容 conda Python
sys.path.insert(0, "/Users/nowcoder/miniconda3/lib/python3.9/site-packages")

from PIL import Image, ImageDraw, ImageFont


# ========== 字体回退 ==========
def find_font(size):
    """macOS / Linux 字体回退链。"""
    candidates = [
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/Hiragino Sans GB.ttc",
        "/System/Library/Fonts/STHeiti Medium.ttc",
        "/System/Library/Fonts/STHeiti Light.ttc",
    ]
    for c in candidates:
        if os.path.exists(c):
            return ImageFont.truetype(c, size)
    linux = [
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    ]
    for c in linux:
        if os.path.exists(c):
            return ImageFont.truetype(c, size)
    return ImageFont.load_default()


# ========== 视觉元素 ==========
def draw_neural_network(overlay, cx, cy, R, n_nodes=80, seed=7):
    """中央神经网络节点 + 连线。"""
    odraw = ImageDraw.Draw(overlay)
    random.seed(seed)
    nodes = []
    for _ in range(n_nodes):
        a = random.uniform(0, 2 * math.pi)
        r = random.uniform(0, R)
        nodes.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    # 连线
    for i, (x1, y1) in enumerate(nodes):
        for x2, y2 in nodes[i + 1:i + 6]:
            d = math.hypot(x2 - x1, y2 - y1)
            if d < 100:
                odraw.line(
                    [(x1, y1), (x2, y2)],
                    fill=(80, 160, 255, max(0, int(120 - d))),
                    width=1,
                )
    # 节点
    for x, y in nodes:
        odraw.ellipse([x - 2, y - 2, x + 2, y + 2], fill=(180, 220, 255, 220))
    # 外圈光晕
    for r in range(R + 20, R - 50, -2):
        alpha = max(0, 30 - abs(r - R))
        odraw.ellipse(
            [cx - r, cy - r, cx + r, cy + r],
            outline=(90, 150, 230, alpha),
            width=1,
        )


def draw_formula_paper(overlay, paper_x, paper_y, paper_w, paper_h):
    """草稿纸（米黄色信纸 + 红色横线）。"""
    odraw = ImageDraw.Draw(overlay)
    odraw.rectangle(
        [paper_x, paper_y, paper_x + paper_w, paper_y + paper_h],
        fill=(245, 235, 210, 245),
    )
    line_gap = max(18, paper_h // 8)
    for y in range(paper_y + 25, paper_y + paper_h - 10, line_gap):
        odraw.line(
            [(paper_x + 15, y), (paper_x + paper_w - 15, y)],
            fill=(220, 130, 130, 180),
            width=1,
        )


def draw_text_left(draw, x, y, text, font, color, shadow=True):
    if shadow:
        draw.text((x + 2, y + 2), text, fill=(0, 0, 0), font=font)
    draw.text((x, y), text, fill=color, font=font)


def draw_text_centered(draw, W, text, y, font, color, line_h=None, shadow=True):
    """水平居中画文字，返回占用行高。"""
    if line_h is None:
        line_h = font.size + 14
    tw = font.getbbox(text)[2]
    x = (W - tw) // 2
    if shadow:
        draw.text((x + 2, y + 2), text, fill=(0, 0, 0), font=font)
    draw.text((x, y), text, fill=color, font=font)
    return line_h


# ========== Layout: 9x16 竖版 ==========
def layout_9x16(args):
    W, H = 900, 1260
    img = Image.new("RGB", (W, H), color=(8, 12, 30))
    draw = ImageDraw.Draw(img)
    visuals = [v.strip() for v in args.visual.split(",") if v.strip()]

    # 1. 顶部副品牌
    if args.top_label:
        top_font = find_font(24)
        tw = top_font.getbbox(args.top_label)[2]
        draw.text(((W - tw) // 2, 70), args.top_label, fill=(130, 160, 220), font=top_font)
        overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        odraw = ImageDraw.Draw(overlay)
        odraw.line([(60, 120), (W - 60, 120)], fill=(80, 130, 220, 120), width=1)
        img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
        draw = ImageDraw.Draw(img)

    # 2. 中央视觉
    if "neural-network" in visuals:
        overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        draw_neural_network(overlay, W // 2, 420, R=230)
        img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
        draw = ImageDraw.Draw(img)

    # 3. 草稿纸 + 公式
    if "formula-paper" in visuals:
        overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        px, py, pw, ph = W // 2 - 200, 760, 400, 240
        draw_formula_paper(overlay, px, py, pw, ph)
        img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
        draw = ImageDraw.Draw(img)

        if args.formula:
            # 居中画公式 + 上标 + 问号
            formula_font = find_font(58)
            text = args.formula
            fw = formula_font.getbbox(text)[2]
            fx = (W - fw) // 2
            fy = py + 95
            draw.text((fx, fy), text, fill=(30, 30, 90), font=formula_font)
            if args.formula_sup:
                sup_font = find_font(36)
                sw = sup_font.getbbox(args.formula_sup)[2]
                draw.text((fx + fw + 2, fy - 2), args.formula_sup,
                          fill=(30, 30, 90), font=sup_font)
            else:
                sw = 0
            if args.formula_qmark:
                qmark_font = find_font(70)
                draw.text((fx + fw + sw + 14, fy - 6), "?",
                          fill=(220, 80, 80), font=qmark_font)

    # 4. 主标题
    title_font = find_font(54)
    sub_font = find_font(28)
    brand_font = find_font(22)

    title_y_start = 1020
    h1 = draw_text_centered(draw, W, args.title_line1, title_y_start, title_font, (255, 255, 255))
    h2 = draw_text_centered(draw, W, args.title_line2, title_y_start + h1, title_font, (130, 200, 255))

    # 5. 副标题
    if args.subtitle:
        sub_y = title_y_start + h1 + h2 + 20
        draw_text_centered(draw, W, args.subtitle, sub_y, sub_font, (190, 210, 240))

    # 6. 底部品牌
    if args.brand:
        overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        odraw = ImageDraw.Draw(overlay)
        odraw.line([(60, H - 60), (W - 60, H - 60)], fill=(80, 130, 220, 120), width=1)
        img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
        draw = ImageDraw.Draw(img)
        draw_text_centered(draw, W, args.brand, H - 38, brand_font, (150, 170, 220))

    return img


# ========== Layout: 20x9 横向（公众号官方封面比例）==========
def layout_20x9(args):
    """20:9 横向 1200×540。

    布局分区（左对齐文字 + 右对齐视觉元素 + 顶部/底部分隔线）:
    | 60px  |  文字区 (主标题 + 副标题)  | 视觉区 (神经网络) | 60px |
    | 顶 30px (top-label 副品牌) + 横线
    | 主标题 48pt 左对齐 (y=110~220)
    | 副标题 22pt 左对齐 (y=250)
    | 草稿纸 200x110 左下角 (y=380)
    | 底 60px 品牌行 + 右下角 source 链接
    """
    W, H = 1200, 540
    img = Image.new("RGB", (W, H), color=(8, 12, 30))
    draw = ImageDraw.Draw(img)
    visuals = [v.strip() for v in args.visual.split(",") if v.strip()]

    # 1. 顶部副品牌 + 装饰线
    if args.top_label:
        top_font = find_font(18)
        draw_text_left(draw, 60, 30, args.top_label, top_font, (130, 160, 220), shadow=False)
        overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        odraw = ImageDraw.Draw(overlay)
        odraw.line([(60, 65), (W - 60, 65)], fill=(80, 130, 220, 140), width=1)
        img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
        draw = ImageDraw.Draw(img)

    # 2. 右侧神经网络（cx ≈ 900, cy ≈ 270, R=180）
    if "neural-network" in visuals:
        overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        draw_neural_network(overlay, cx=900, cy=270, R=180, seed=11)
        img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
        draw = ImageDraw.Draw(img)

    # 3. 草稿纸（仅在公式模式下，左下角 200x110）
    if "formula-paper" in visuals and args.formula:
        overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        draw_formula_paper(overlay, paper_x=60, paper_y=370, paper_w=200, paper_h=110)
        img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
        draw = ImageDraw.Draw(img)

        # 公式在草稿纸内
        formula_font = find_font(34)
        text = args.formula
        fw = formula_font.getbbox(text)[2]
        # 草稿纸内居中，但要为问号预留空间
        paper_x, paper_y, paper_w, paper_h = 60, 370, 200, 110
        fx = paper_x + (paper_w - fw - 50) // 2
        fy = paper_y + 35
        draw.text((fx, fy), text, fill=(30, 30, 90), font=formula_font)
        if args.formula_sup:
            sup_font = find_font(22)
            sw = sup_font.getbbox(args.formula_sup)[2]
            draw.text((fx + fw + 1, fy - 1), args.formula_sup,
                      fill=(30, 30, 90), font=sup_font, )
        else:
            sw = 0
        if args.formula_qmark:
            qmark_font = find_font(40)
            draw.text((fx + fw + sw + 6, fy - 4), "?",
                      fill=(220, 80, 80), font=qmark_font)

    # 4. 主标题（左对齐，两行）
    title_font = find_font(48)
    sub_font = find_font(22)
    brand_font = find_font(20)
    src_font = find_font(16)

    y = 110
    draw_text_left(draw, 60, y, args.title_line1, title_font, (255, 255, 255))
    bbox = draw.textbbox((0, 0), args.title_line1, font=title_font)
    y += (bbox[3] - bbox[1]) + 18
    draw_text_left(draw, 60, y, args.title_line2, title_font, (130, 200, 255))

    # 5. 副标题
    if args.subtitle:
        y += title_font.size + 24
        draw_text_left(draw, 60, y, args.subtitle, sub_font, (190, 210, 240), shadow=False)

    # 6. 底部品牌条（左：AICoder 品牌 + 右：source）
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    odraw = ImageDraw.Draw(overlay)
    odraw.line([(60, H - 60), (W - 60, H - 60)], fill=(80, 130, 220, 140), width=1)
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(img)

    if args.brand:
        draw_text_left(draw, 60, H - 42, args.brand, brand_font, (150, 170, 220), shadow=False)

    if args.right_source:
        sw = src_font.getbbox(args.right_source)[2]
        draw_text_left(draw, W - 60 - sw, H - 38, args.right_source, src_font, (120, 150, 200), shadow=False)

    return img


# ========== Main ==========
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ratio", choices=["9x16", "20x9"], default="9x16",
                    help="封面比例: 9x16 竖版 900x1260 (默认), 20x9 横向 1200x540 (公众号官方)")
    ap.add_argument("--title-line1", required=True)
    ap.add_argument("--title-line2", required=True)
    ap.add_argument("--subtitle", default="")
    ap.add_argument("--top-label", default="")
    ap.add_argument("--brand", default="")
    ap.add_argument("--right-source", default="",
                    help="20x9 模式专用：右下角 source 链接，如 'arXiv:2606.12683'")
    ap.add_argument("--visual", default="neural-network,formula-paper")
    ap.add_argument("--formula", default="")
    ap.add_argument("--formula-sup", default="2")
    ap.add_argument("--formula-qmark", action="store_true")
    ap.add_argument("--output", default="/tmp/cover.png")
    args = ap.parse_args()

    if args.ratio == "20x9":
        img = layout_20x9(args)
    else:
        img = layout_9x16(args)

    img.save(args.output, "PNG")
    print(f"OK: {args.output} ({img.size[0]}x{img.size[1]}, {os.path.getsize(args.output)} bytes)")


if __name__ == "__main__":
    main()
