# Product Plugin

产品 / 商业 / 技术 / 设计分析工具集。核心是一个可交付咨询报告的产品拆解工作流，加上三个可独立
调用的深挖 skill：

```text
product-teardown          ← 主 skill：4 层 15 问 MECE 框架 + 双语 HTML 报告
├── competitor-landscape  ← 独立可调用：竞品矩阵 + 2D 定位图（§8 的深挖版）
├── ai-architecture-review ← 独立可调用：AI/Agent 技术栈拆解（§10 的深挖版）
└── copy-ui-style         ← 独立可调用：UI 风格逆向 → 设计系统 + AI 编码规则（§5 的深挖版）
```

## Skills

### product-teardown

Principal-PM 级产品拆解。把任意产品（Linear、Notion、Cursor、竞品……）当成一个*系统*来逆向
分析，而不是"我喜欢这个 App 的 5 个地方"式的评测。

框架分 **4 层、15 个固定问题**，每一节只回答一个问题（MECE）：

| 层 | 解决什么 | 包含章节 |
|---|---|---|
| ① Product | 是什么、为什么有人用、为什么持续用 | 快照 · JTBD · **核心循环** · 手艺信号 · 体验质量 |
| ② Business | 为什么赚钱、为什么增长 | 商业模式 · 竞品格局 · 增长策略 |
| ③ Technology | 为什么能建成、为什么能扩展、AI 放在哪 | 架构与技术栈 · AI/Agent 就绪度 |
| ④ Strategy | 接下来该去哪 | 指标 · 摩擦 · 风险矩阵 · 机会 · 终局判断 |

其中 **核心循环（Core Loop）** 是全篇的骨架，占分析精力的约 30% —— 其他一切都是循环的下游。
先在对话里产出完整的 15 问分析，再渲染成双语（EN + ZH，互相跳转）、可打印的单文件 HTML 报告，
带 6 张产品截图画廊。

**快速开始：**

```bash
# 1. 在对话中按 4 层 15 问框架产出完整拆解
# 2. 把内容整理成一份 JSON（结构见 references/example-data.json），然后渲染双语报告
python3 ${CLAUDE_PLUGIN_ROOT}/skills/product-teardown/scripts/render_teardown.py \
  --data ./teardown-<slug>.json --out-dir ./output
```

**依赖：** 纯 Python 标准库，无需安装第三方包。

渲染脚本会先校验再落盘：EN / ZH 任一份有未填充占位符、或 AI 三档没有恰好一档为 `active`、
或体验条不是 0–100 的整数，都会非零退出且**一个文件都不写**，避免出半份或带 `{{...}}` 的报告。
改过模板后跑一下测试（会检查两份模板的占位符集合是否仍然一致）：

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/product-teardown/tests/test_render_teardown.py
```

详情请见 [product-teardown 技能文档](skills/product-teardown/SKILL.md)。

### competitor-landscape

独立的竞品深挖 —— 不需要跑完整个 15 问框架，只要竞争格局这一件事时用它。3–6 个真实对手、
4–6 个真正有战略张力的维度矩阵，外加一张 2D 定位图（文字描述形式）。

详情请见 [competitor-landscape 技能文档](skills/competitor-landscape/SKILL.md)。

### ai-architecture-review

独立的 AI/Agent 技术架构深挖 —— 把"这个产品有 AI 功能"这句话拆成
`Model → Tool → Memory → Planning → Agent → Workflow → Evaluation` 七层管线来逆向分析，
而不是停在 UI 层面的 Assistive/Embedded/Autonomous 标签。

详情请见 [ai-architecture-review 技能文档](skills/ai-architecture-review/SKILL.md)。

### copy-ui-style

把一个产品的 **视觉语言** 逆向成可复用的设计系统 —— 输入截图 / URL / 前端代码仓库，输出一份
`ui-style/` 产物包：

```text
Collect（拿到真实像素与真实取值）
  → Analyze（先定性格，再谈数值）
  → Extract（color / typography / spacing / radius / shadow / motion tokens）
  → Components（Button / Card / Input / ListRow / Nav / Modal）
  → Generate（一份 JSON → 校验通过才落盘）
```

产物里真正起作用的是 `AGENTS.md`：聊天记录里的风格分析下个会话就没人看了，
`ui-style/AGENTS.md` + `ui-style/tokens.css` 会被 Claude Code / Codex 真正读到并遵守。

**快速开始：**

```bash
# 1. 先在对话里完成风格分析（性格 → 视觉刻度 → signature moves → tokens → 组件）
# 2. 生成骨架 JSON 并填写（完整示例见 references/example-style.json）
python3 ${CLAUDE_PLUGIN_ROOT}/skills/copy-ui-style/scripts/generate_ui_style.py \
  --init ./ui-style-<slug>.json

# 3. 渲染整包产物
python3 ${CLAUDE_PLUGIN_ROOT}/skills/copy-ui-style/scripts/generate_ui_style.py \
  --data ./ui-style-<slug>.json --out-dir ./ui-style
```

输出：`DESIGN.md`（人读）、`AGENTS.md`（AI 编码规则）、`components.md`、`tokens.json`、
`tokens.css`、`style-dna.json`。

脚本先校验后落盘：缺必需色彩角色、颜色不是合法 hex/rgb、间距少单位、视觉刻度不在 0–1、
组件缺 `style` 字段，都会非零退出且**一个文件都不写**。同时会按 WCAG 2.1 真实计算
`text_primary` / `text_secondary` 对 `background` 的对比度，低于 4.5:1 给警告，`--strict`
下直接失败。改过模板或脚本后跑测试：

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/copy-ui-style/tests/test_generate_ui_style.py
```

**依赖：** 纯 Python 标准库。浏览器工具（Playwright / chrome-devtools MCP）是可选项，
只在输入是 URL 时帮忙截图和读 computed style；没有就退回用户提供的截图或 `curl` + CSS grep。

详情请见 [copy-ui-style 技能文档](skills/copy-ui-style/SKILL.md)。

## 为什么不是 20 个微型 skill

有过一版设计建议把这个能力拆成约 20 个原子 skill（jtbd、core-loop、pricing、moat、
code-review、observability……各一个）。这里刻意没有这么做：Claude Code 的 skill 是按
触发短语匹配来选择的，不是可编程串联的子程序 —— 20 个高度相似的"分析一下这个产品的 X"
触发词大概率互相冲突、拖累可发现性，而不是换来真正的可组合性。所以选择保留一个内聚的
`product-teardown` 主工作流（承载上面深化后的 4 层内容），只把两个**确实可能被单独调用**
的子话题拆成了真正独立的 skill。而通用工程评审类能力（代码评审 / 性能 / 安全 / 可观测性）
故意没有放进这个插件 —— 它们和"产品"无关，且本环境里已有对应 skill，重复造轮子不是可组合性，
是范围蔓延。

## 关键 Pitfalls

1. **占位符缺失会显式失败**：`render_teardown.py` 非零退出并列出所有未填充的 `{{KEY}}`，
   不要手工改渲染后的 HTML 掩盖遗漏 —— 改 JSON 重新渲染。
2. **EN / ZH 占位符集合必须完全一致**：只给一种语言加占位符是"静默失败"的典型场景——
   改了任一模板的结构后跑 `tests/test_render_teardown.py`，它会直接把差集打出来。
   新增一个字段是**三处**改动：两份模板 + `references/example-data.json`。
3. **不要编造硬数字**：任何非直接可观察的数字都要标 `[inferred]` / `[推断]`，或者标
   `[需用户补充]`。
4. **截图必须能被热链接**：需要登录或禁止跨站引用的图片会在画廊里显示为坏图。
5. **UI 风格不要凭记忆提取**：“它是 Stripe，所以紫色渐变”产出的是刻板印象，不是这个产品的
   系统。密度和字号刻度要从密集的产品界面上量，不要从 marketing 页量。
6. **`ui-style/` 下的文件是生成物**：不要手改，改 JSON 重新渲染，否则下次生成会静默覆盖。
7. **Opportunity 不能退化成功能列表**：每条建议都要能说清楚"服务哪个 JTBD / 强化哪个循环
   步骤 / 拉动哪个指标"，说不清楚就还没想完。
