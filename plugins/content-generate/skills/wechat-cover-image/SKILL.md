---
name: wechat-cover-image
description: "Use when generating a 公众号 (WeChat) cover image WITHOUT an external AI image service. Pillow-based pipeline supporting BOTH 9x16 (900x1260, legacy vertical) and 20x9 (1200x540, 公众号官方封面比例) ratios. Title, subtitle, brand mark, source link, and visual centerpiece. Triggers: 公众号封面, WeChat cover, no FAL_KEY, image_generate unavailable, fallback cover image, 20:9 封面."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [wechat, cover, image, pillow, publishing, fallback]
    related_skills:
      - tech-content-writer
      - parenting-content-writer
      - ali-oss
---

# 公众号封面图：Pillow 零依赖方案

## Overview

当 `image_generate` 工具不可用（缺 `FAL_KEY`、未配置后端、网络不可达），公众号文章仍需要封面图。本 skill 提供一个**纯 Pillow、零外部依赖、零 API 费用**的回退方案：

- **20:9 横向 1200x540**（**公众号官方封面比例**，2026-06-14 用户反馈：列表卡片图、推荐位都用 20:9 裁剪）
- **9x16 竖版 900x1260**（向后兼容旧版公众号）

## When to Use

触发词：
- 「image_generate 不可用，回退 Pillow 画封面」
- 「生成公众号封面（无 AI 生图）」
- 「给这篇文章画个能用的封面」
- 「公众号封面 20:9」「公众号封面 20×9」「公众号官方封面」

依赖检查：
- Pillow（`PIL.Image`、`PIL.ImageDraw`、`PIL.ImageFont`）
- 至少一个中文字体（macOS 自带 PingFang/STHeiti，Linux 用 Noto Sans CJK）
- conda Python 通常自带，pip 也行

**比例选择：**
- **默认且推荐 20:9**（用户 2026-06-14 反馈：公众号新版本封面要求 20:9 横向，会被裁成列表卡片图）
- 9x16 仅在旧版公众号或特殊场景使用

## Quick Start

### 20:9 横向（公众号官方比例，推荐）

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/wechat-cover-image/scripts/gen_cover.py \
  --ratio 20x9 \
  --title-line1 "Google 不再卷 AGI 了，" \
  --title-line2 "他们在画 ASI 的地图" \
  --subtitle "从 AGI 到 ASI：四条路径与一个测深线" \
  --top-label "DEEPMIND · FROM AGI TO ASI" \
  --brand "AICoder · 技术洞察" \
  --right-source "arXiv:2606.12683 · deepmind.google" \
  --visual neural-network,formula-paper \
  --formula "E=mc" \
  --formula-qmark \
  --output /tmp/cover.png
```

### 9x16 竖版（兼容旧版公众号）

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/wechat-cover-image/scripts/gen_cover.py \
  --ratio 9x16 \
  --title-line1 "Google 不再卷 AGI 了，" \
  --title-line2 "他们在画 ASI 的地图" \
  --subtitle "从 AGI 到 ASI：四条路径与一个测深线" \
  --top-label "DEEPMIND · FROM AGI TO ASI" \
  --brand "AICoder · 技术洞察" \
  --visual neural-network,formula-paper \
  --formula "E=mc" \
  --output /tmp/cover.png
```

## 视觉模式（`--visual`）

| 模式 | 用途 | 实现 |
|---|---|---|
| `neural-network` | AI/ML 文章 | 中央放射节点 + 连线，模拟神经网络 |
| `formula-paper` | 物理/数学/学术 | 草稿纸 + 公式 + 问号，模拟 1900 年爱因斯坦测试 |
| `blueprint` | 架构/工程 | 同心圆 + 网格，模拟技术蓝图 |
| `code-snippet` | 编程/工具 | 终端窗口 + 代码块，模拟 IDE |
| `clean` | 通用 | 极简：顶部细线 + 中央大标题，无装饰 |

可叠加：脚本支持 `--visual neural-network,formula-paper`（逗号分隔多视觉元素）。

## 字号与布局

### 20:9 横向 1200x540（公众号官方比例）

| 区域 | 位置 | 内容 |
|---|---|---|
| 顶部副品牌 | y=30 左对齐 18pt | 论文 / 来源标识 |
| 装饰线 | y=65 | 横贯全宽 1px 蓝线 |
| 右侧视觉 | cx=900, cy=270, R=180 | 神经网络节点 + 连线（被标题隔开在右侧） |
| 草稿纸 | x=60, y=370, 200x110 | E=mc² 公式 + 上标 + 问号（点缀） |
| 主标题 | x=60, y=110~220 左对齐 48pt | 两行 |
| 副标题 | x=60, y=250 左对齐 22pt | 一行 |
| 底部分隔线 | y=H-60 | 横贯全宽 1px 蓝线 |
| 左下品牌 | x=60, y=H-42 左对齐 20pt | 「AICoder · 技术洞察」 |
| 右下 source | x=W-60, y=H-38 右对齐 16pt | 论文来源，如 arXiv 编号 |

**20:9 避坑**：
- ❌ 标题左对齐但 x < 60（被画布边切）
- ❌ 视觉元素 cx 放正中（W/2=600）——会和左对齐的标题重叠
- ✅ 视觉 cx ≥ 850，与左侧文字区留 ≥ 200px 间距
- ✅ 草稿纸在左下角，避开主标题区

### 9x16 竖版 900x1260（兼容旧版）

| 区域 | Y 范围 | 内容 |
|---|---|---|
| 顶部品牌 | 60-120 | 副品牌 / 论文 / 来源标识 |
| 中央视觉 | 180-700 | 视觉元素（神经网络 / 公式 / 蓝图） |
| 草稿纸（可选） | 730-1000 | 公式 / 引文区 |
| 主标题 | 1020-1180 | 两行主标题（每行 54pt） |
| 副标题 | 1200-1230 | 28pt 副标题 |
| 底部品牌 | 1230-1260 | 「XX · 公众号名」 |

**9x16 避坑**：
- ❌ 不要把品牌行和副标题都放 y=1100-1200 区间——会撞
- ✅ 留 ≥40px 间距
- ✅ 用 `draw_text_centered()` 计算 y 累加，不手写固定 y

## 字体坑（macOS 必看）

PingFang.ttc 对部分 Unicode 字符**渲染失败**（豆腐方块）：

| 字符 | 问题 | 解决方案 |
|---|---|---|
| ²（上标 2） | 显示为 ⊠ | 拆成 "E = mc" + 单独画小号 "2" 偏上 |
| ³（上标 3） | 同上 | 同上 |
| ℃ | 偶发失败 | 用 "C" 替代 |
| emoji 😀 | 不会画 | 不要在封面用 emoji |

**字号选择**：
- 9x16 竖版：标题 54pt / 副标题 28pt / 品牌 22pt / 上标 36pt
- 20x9 横向：标题 48pt / 副标题 22pt / 品牌 20pt / 上标 22pt / source 16pt

**多行文本换行**：手动按字符累加宽度，超 `max_w` 切行，不要假设 `textwrap` 能处理中文。

## Pitfalls

1. **顶部放射光/装饰线容易和文字重叠**：装饰区放 y < 100，文字区放 y > 1000，中间隔着大留白是 OK 的，但中间不要塞满。
2. **中文字体回退顺序**：先 PingFang → STHeiti → Hiragino → Noto → 兜底 `load_default()`。`load_default()` 不能画中文，会出豆腐。
3. **`alpha_composite` 后要 `convert('RGB')`**：否则保存 JPEG 报错；保存 PNG 时保留 RGBA 也行。
4. **深度学习模型的 ² 上标是 Unicode 0x00B2**，PingFang 里没这个字形。**必须拆开画**。
5. **不要用 `textsize()`**（Pillow 10+ 已废弃），改用 `font.getbbox(text)[2]`。
6. **草稿纸的 `paper_y + 95` 公式垂直居中**：先算 paper 中心，再下移 5px 留视觉平衡。
7. **`--formula "E=mc"` 不带 ²**（避免 Unicode 坑），脚本自动画上标 2 + 问号。
8. **视觉自检**：脚本生成后**必须**用 `vision_analyze` 看一眼，确认没有文字撞车和豆腐。
9. **❗ 公众号封面比例错**（用户 2026-06-14 反馈）：旧 skill 只支持 9x16 竖版，但新版公众号**官方要求 20:9 横向**。发布前先确认目标公众号的封面比例，默认用 `--ratio 20x9`。
10. **20:9 视觉元素 cx 偏右**：神经网络圆心默认 cx=900（不是 W/2=600），否则会和左对齐的主标题重叠。
11. **`draw.textsize` 在新版 Pillow 已弃用**，统一用 `font.getbbox(text)[2]`。
12. **lark-cli 命令语法是 `lark-cli im +messages-send`**，**不是** `lark-cli +im +messages-send`（后者会报 `unknown command "+im"`）。完整命令：`lark-cli im +messages-send --chat-id <oc_xxx> --as user --markdown "<text>"`。

## 与其他 skill 的关系

- `tech-content-writer` / `parenting-content-writer` 写完文章后，本 skill 出封面
- `ali-oss` 把封面图传到 OSS，拿到公开 URL
- wechat-publisher 类 skill 把封面 URL 作为「📎 封面图：」文字发到飞书

## Verification Checklist

- [ ] 脚本能一次跑通，不报字体错误
- [ ] `vision_analyze` 看到：标题完整、副标题与品牌行不重叠、无豆腐字
- [ ] 草稿纸公式上标正常
- [ ] 整体深色风格统一（不要半张图浅色半张深色）
- [ ] 文件大小 50-200KB（PNG 压缩合理）
- [ ] **比例正确**：发布到公众号前确认用 `--ratio 20x9`（默认）或 `--ratio 9x16`
- [ ] 20x9 模式：标题在左、视觉在右、草稿纸在左下、底部分隔线 + 品牌行不重叠
- [ ] 9x16 模式：主标题在底部、副标题 + 品牌行留 ≥ 40px 间距

## Future Improvements

- 支持横版 16:9 公众号次图（参考 Open Graph 1280x640）
- 支持浅色背景（科技/学术/工具类文章常用白底）
- 集成 ImageMagick 把 PNG 转 JPG（部分场景需要更小文件）
- 模板化：保存 .json 配方，下次换标题/视觉一键复用
