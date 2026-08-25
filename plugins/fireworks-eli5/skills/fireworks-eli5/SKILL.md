---
name: fireworks-eli5
description: >-
  当用户要求用小白能懂的方式解释技术主题、画一张解释图、生成可分享的
  HTML 图解，或输入 /fireworks-eli5 <topic> 时使用。适用于 API、代码流程、
  系统架构、数据流、Agent、记忆和抽象概念；输出少文字、大图、离线 HTML，
  并用 Fireworks Tech Graph 生成经过 SVG 校验的 SVG + PNG。
---

# Fireworks ELI5

Topic: `$ARGUMENTS`

把复杂主题讲给完全不了解它的人，同时交付一张可检查、可离线打开的图。不要把
长篇技术文档缩短成同样难懂的术语列表；先建立直觉，再补最少的准确细节。

## 1. 先确定解释目标

1. 如果主题为空，先从用户最近一句话提取主题；仍然不明确时，询问一个最小澄清问题。
2. 写出一个读者看完后应该记住的单句结论，避免缩写和内部名词。
3. 把系统拆成「输入 → 发生了什么 → 输出」的 3–5 步；每步只保留一个动作。
4. 为抽象概念选择一个不误导的日常比喻，并在必要时明确比喻的边界。
5. 只有在不影响直觉时才加入实现细节；无法由上下文确认的事实标记为 `[需确认]`，不要编造。

## 2. 规划 Fireworks 图

先分类，再画图：

- 架构/服务关系 → `architecture` 或 `agent`。
- 数据如何变换 → `data-flow`。
- 逐步决策 → `flowchart`。
- 时间顺序/请求往返 → `sequence`。
- 生命周期 → `state-machine`。
- 数据表关系 → `er-diagram`。
- 多方案比较 → `comparison`。
- 概念层级 → `mind-map`。

提取节点、分层、边和语义分组；布局优先保证留白和阅读顺序。默认使用 Flat Icon
style 1，用户要求或主题需要时选择 style 2–7，并读取对应的本地 reference。

节点形状要表达含义：用户/人、Agent/Orchestrator、LLM、短期记忆、持久存储、工具、
API、队列、文档和外部服务使用语义形状，不要把所有东西画成同一种矩形。

箭头必须表达含义：主数据流用蓝色，控制触发用橙色，memory read/write 用绿色，
异步事件用灰色，变换/反馈用紫色。使用两个或以上箭头语义时必须有 legend。箭头
从节点边缘出发，优先使用正交路径；标签旁放不透明背景；避免穿过节点。不可避免的
交叉使用 jump-over arc。

## 3. 生成和校验 SVG + PNG

先创建结构化 JSON，再调用本插件内的脚本。`${CLAUDE_PLUGIN_ROOT}` 可用时：

```bash
SKILL_DIR="${CLAUDE_PLUGIN_ROOT}/skills/fireworks-eli5"
```

在不支持该变量的运行时，使用当前插件的真实绝对路径替代 `SKILL_DIR`；不要引用
宿主机上其它 skill 的私有安装路径。

用模板生成 SVG。先固定本次 artifact 的目录，后续 HTML、SVG 和 PNG 都必须使用这两个变量：

```bash
OUT_DIR="./fireworks-eli5/<topic-slug>"
SVG_PATH="$OUT_DIR/<topic-slug>.svg"
mkdir -p "$OUT_DIR"

python3 "$SKILL_DIR/scripts/generate-from-template.py" \
  <template-type> "$SVG_PATH" <<'JSON'
{
  "style": 1,
  "title": "Topic",
  "subtitle": "One-line explanation",
  "nodes": [],
  "arrows": []
}
JSON
```

把完整的节点和箭头 JSON 放进 heredoc；不要把用户文本直接拼进 shell 单引号参数。
heredoc 会把包含单引号或 shell 字符的标签作为普通 JSON 文本传给生成器。

生成器支持 `source`/`target` 节点 ID、`flow`、`source_port`、`target_port`、
`route_points`、`corridor_x` 和 `corridor_y`。复杂图优先让生成器路由，只有必要时才
提供正交 `route_points`。

校验并导出 PNG：

```bash
"$SKILL_DIR/scripts/validate-svg.sh" "$SVG_PATH"
"$SKILL_DIR/scripts/generate-diagram.sh" \
  -t <template-type> -s <style> -o "$SVG_PATH"
```

`generate-diagram.sh` 只在 SVG 已存在时做验证和导出。PNG 优先用 `cairosvg`，其次
使用 `rsvg-convert`；两者都不可用时必须停止并报告安装方式。额外运行：

```bash
python3 - "$SVG_PATH" <<'PY'
import sys
import xml.etree.ElementTree as ET

ET.parse(sys.argv[1])
PY
```

SVG 文本不要放 emoji，因为 CairoSVG 可能把它们渲染成空方框。完成后，如果环境能读
图像，检查节点、标签、箭头、legend 和边界是否实际清楚；发现碰撞就只调整 JSON 的
箭头路由后重新渲染，不要手改生成的 SVG。

## 4. 产出 ELI5 HTML artifact

在 `./fireworks-eli5/<topic-slug>/` 写入一个自包含、完全离线的 HTML 文件，并把 SVG/PNG 放在
同目录。HTML 至少包含：

```html
<title>主题 — ELI5</title>
<main>
  <h1>一个普通人会问的问题</h1>
  <p class="takeaway">一句话结论</p>
  <figure aria-labelledby="diagram-caption">
    <!-- inline SVG 或 PNG data URI -->
    <figcaption id="diagram-caption">这张图表达的输入、过程和输出</figcaption>
  </figure>
  <ol><li>短步骤 1</li><li>短步骤 2</li><li>短步骤 3</li></ol>
  <section>可选：为什么重要、迷你词汇表</section>
</main>
```

CSS 和 SVG 必须内嵌，或将 PNG 编成 data URI；禁止外部网络请求。页面要响应式、可读、
有正确的标题层级和图注，正文避免堆叠卡片和大段说明。图中文字可以简短，关键解释放
在 HTML 文本中；HTML 不得把“如何使用这个 skill”当成用户可见说明。

## 5. 依赖、写入和失败边界

- 生成前检查 Python、脚本文件和至少一个 PNG renderer；缺失时给出清晰安装提示。
- 只写用户请求范围内的 artifact；不要上传主题、图片或 HTML，不要修改 git 状态。
- 如果目标文件已存在，先告知并选择新路径或得到覆盖确认。
- 任何校验或导出失败都要报告真实错误和已完成的文件，不要伪造“已生成”。
- 最终回复列出 `.html`、`.svg`、`.png` 的绝对路径，以及实际运行过的验证命令。
