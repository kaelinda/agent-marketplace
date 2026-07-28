# Design Plugin

设计工具集。目前收录一个 skill：把「帮我画个 App 图标」从一句 Prompt 变成一套可复用、
可评审、会积累的设计工作流。

```text
apple-icon-studio     ← 10 层 Apple 级图标设计工作流
├── references/       ← 11 份设计知识库 + 10 个行业 Icon DNA
├── examples/         ← 5 个完整拆解案例（含被淘汰的方案和淘汰理由）
├── templates/        ← 双语可打印 HTML 简报（单模板 + 双语言字符串表）
└── scripts/          ← 简报渲染 + 1024 母版一键出图标集
```

## Skills

### apple-icon-studio

大多数图标 Prompt 的问题是**一上来就开始画**。这个 skill 到第 8 层才开始写 Prompt。

前提是：好图标不是插画问题，是**一个最后落在画面上的定位问题**。Apple 自己的图标几乎从不画产品
—— AirDrop 不是 Wi-Fi 示意图，是放射的同心圆；Shortcuts 不是流程图，是分层的菱形。要做到这一点，
必须先决定*这个产品意味着什么*，再决定*画什么*。

**10 层工作流：**

| 层 | 做什么 | 关键约束 |
|---|---|---|
| 1 产品分析 | 五问 → 压缩成一句 **Brand Essence** | 换到竞品身上没人看得出来 = 还不算内核 |
| 2 隐喻生成 | 五个维度各出 2 个，共 **10 个** | **必须淘汰 7 个，并写下每一个的淘汰理由** |
| 3 形态语言 | 剪影先于细节 | 黑色剪影 40px 下认不出来 = 不往下走 |
| 4 材质指导 | 主材质 / 辅材质 / 反射 / 透明度 / 边缘 / 表面 | **最多两种材质** |
| 5 构图指导 | 8 种构图模式 + 重量 / 负空间 / 焦点分析 | 主体占 60–70%，圆角遮罩区不放内容 |
| 6 色彩指导 | 品类 → 竞品 → 定位 → 情绪 → 配色 | 最多 3 个色相，60/30/10 层级 |
| 7 **Apple 评审** | 11 条标准否决 + 6 维加权评分 | **低于 85 分不发**，回第 2 层或第 4 层 |
| 8 出图 Prompt | 13 个槽位，每个都能溯源到 1–6 层 | 槽位没有上游决策 = 分析有洞 |
| 9 Icon Composer | Glass / Blur / Refraction / Specular… 参数 | AI 出的图不是成品图标 |
| 10 图标演进 | 对照 iOS 7 → 26 做时效校验 | 「2026 年 Apple 会怎么改」要写成具体 diff |

第 7 层是这个 skill 的价值所在：它不生成，它挑刺。11 条否决（太像 ChatGPT / 太复杂 /
桌面上很脏 / 40px 看不清 / 颜色没层级 / 材质混乱 / 不像 Apple / 边缘太锐 / 光照方向错 /
18 个月内会过时 / 单色模式下失效）逐条给结论——**包括通过的那些**，因为「查过了，通过」是信息，
沉默不是。

**评分公式**（辨识度和缩放存活加权 1.5×，因为它们决定图标能不能*用*，其余决定它*好不好*）：

```
Final = (辨识度×1.5 + 缩放存活×1.5 + Apple感 + 材质 + 记忆度 + 情绪) / 7
```

**快速开始：**

```bash
# 1. 在对话里跑完 10 层（skill 会按需加载 references/ 下的知识库）
# 2. 整理成 JSON（结构见 references/example-brief.json），渲染双语简报
python3 ${CLAUDE_PLUGIN_ROOT}/skills/apple-icon-studio/scripts/render_icon_brief.py \
  --data ./brief-<slug>.json --out-dir ./output

# 3. 图定稿后，从 1024 母版生成各平台图标集
python3 ${CLAUDE_PLUGIN_ROOT}/skills/apple-icon-studio/scripts/make_icon_set.py \
  --input ./master-1024.png --out-dir ./icons --targets ios,macos,web
```

**依赖：** 简报渲染是纯 Python 标准库。出图标集用 macOS 自带的 `sips` / `iconutil`，
不在 macOS 时自动回退到 Pillow（`pip install Pillow`），两者都没有会直接报错说明怎么装。

详情请见 [apple-icon-studio 技能文档](skills/apple-icon-studio/SKILL.md)。

## Icon DNA —— 会积累的那部分

`references/icon-dna/` 下 10 个行业文件（ai / productivity / developer / media / finance /
education / health / social / utilities / games），每个都预先消化了这个品类的用户心智、
已被用尽的隐喻、还开放的隐喻、推荐形态 / 材质 / 配色（含**撞车对照表**：哪个色相已经属于哪家）、
典型陷阱，以及可直接粘进 Prompt 的片段。

第 1 层确定品类后就该读对应文件，这样第 2 层是从行业现状开始，而不是从零开始。

跑完一次之后，把学到的**品类级**结论写回去——这个库是唯一会随使用变强的部分。具体某个产品的
决策记录属于 `examples/`，不属于这里。

## 校验与测试

渲染脚本**先校验、全过了才落盘**。任一语言不通过就一个文件都不写——磁盘上留一份带
`{{PLACEHOLDER}}` 的简报，比没有简报更危险，因为它太容易被误发出去。

校验的不只是占位符，还有这套方法论本身的约束：

- 6 个维度分数必须是 0–100 整数
- 声明的 Final 必须和加权公式一致（差值 > 0.5 直接失败）
- Final < 85 拒绝出简报 —— 门槛写在文档里但脚本不查，等于没有门槛
- 隐喻至少 10 个、恰好 3 个标 `kept`、每行 TOTAL 必须等于四项之和
- 11 条否决必须全部记录（通过的也要写）
- 配色 2–3 个、HEX 格式合法

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/apple-icon-studio/tests/test_apple_icon_studio.py
# 70 checks
```

## 关键 Pitfalls

1. **静态文案只有一份模板。** UI 标签抽到了 `templates/strings-{en,zh}.json`，HTML 模板只有一个。
   这是刻意和同市场的 `product-teardown`（两份模板）不同的做法——两份模板意味着改结构时要改两处，
   漏一处就是一种语言静默渲染出洞。现在这类漂移在构造上不可能发生，剩下的「某语言缺标签」由脚本
   和测试直接拦截。
2. **新增一个字段是四处改动**：模板 + 两份 strings（如果是 UI 标签）+ `references/example-brief.json`
   + 测试里的期望值。少改一处测试就会红。
3. **别跳过淘汰步骤。** 只生成 3 个隐喻然后"保留 3 个"是自欺——前两个想法几乎总是品类默认答案
   （见 `examples/note-app.md`：得分最低的两个正是最先想到的两个）。
4. **必须真的缩到 40px 看，不要估。** 以及真的转成灰度看（单色模式）。
   `examples/ai-chat.md` 里灰度校验抓出了一个彩色下完全正常、明度差只有 21% 的真实问题。
5. **负向 Prompt 要跟模型的品类先验对着干。** 图像模型对「AI app icon = 紫色」「天气 = 蓝色渐变」
   的先验极强，不在负向里写死就会自己长回来。
6. **1024 母版不接受非正方形，也不接受放大。** `make_icon_set.py` 会直接报错而不是给你一张糊的
   App Store 图标。
