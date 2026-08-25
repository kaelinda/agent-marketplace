# Fireworks ELI5 Plugin

把 API、系统架构、Agent、数据流和代码概念解释成零基础读者能看懂的离线图解。

`fireworks-eli5` 把两个工作流合成一个交付物：

- **ELI5**：一句话结论、3–5 个短步骤、少术语、具体比喻。
- **Fireworks Tech Graph**：按语义选择图类型和节点，生成带箭头语义、路由校验的 SVG，并导出 PNG。
- **离线 HTML**：CSS 和 SVG/PNG 内嵌，打开文件即可阅读，不上传主题或产物。

## 使用

安装本地市场后，直接描述主题或使用命令：

```text
/plugin marketplace add /path/to/agent-marketplace
/plugin install fireworks-eli5@manji
/fireworks-eli5 how does a vector database find similar text?
```

也可以直接说：

```text
用小白能懂的方式解释 Agent 的记忆读取流程，并生成一张离线图解。
```

默认输出到当前目录下的 `fireworks-eli5/<topic-slug>/`：

```text
<topic-slug>.html  # 自包含 HTML artifact
<topic-slug>.svg   # 原始矢量图
<topic-slug>.png   # 2x 或指定宽度的导出图
```

## 依赖

- Python 3（生成器和 XML 校验）。
- PNG 导出优先使用 `cairosvg`；没有时可使用 `rsvg-convert`。
- SVG 生成、校验和模板均已随插件分发，不依赖 `~/.agents` 或 `~/.claude` 私有路径。

缺少可用 PNG 渲染器时，skill 会如实报告安装提示，不会声称导出成功。

## 目录

```text
skills/fireworks-eli5/
├── SKILL.md                    # 合并后的唯一入口
├── scripts/                    # SVG 生成、验证、PNG 导出
├── templates/                  # architecture / flowchart / sequence 等模板
├── references/                 # 7 种风格、图标和布局规则
├── fixtures/                   # 回归输入
└── vendor/fireworks-tech-graph-LICENSE
```

运行时资产来自 MIT 许可的 `fireworks-tech-graph`，其版权声明保存在 `vendor/fireworks-tech-graph-LICENSE`。
