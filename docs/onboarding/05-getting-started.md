---
title: 快速上手
order: 5
icon: 🚀
summary: 环境、启动、测试与第一个练手任务
---

## 环境要求

- **Python 3.8+**（macOS/Linux 自带即可 —— 所有脚本零 pip 依赖）
- **git** 与 **Claude Code CLI**（体验插件安装链路时需要）
- 无数据库、无 Node、无构建步骤 —— clone 下来就是全部

## 跑起来

这个仓库没有"启动服务"的概念，跑起来 = 把市场装进本地 Claude Code：

```bash
git clone git@github.com:kaelinda/agent-marketplace.git
cd agent-marketplace
```

在 Claude Code 对话里执行（用本地路径便于边改边试）：

```text
/plugin marketplace add /path/to/agent-marketplace
/plugin install playground@manji
```

然后说一句"测一下我的 MBTI"验证 skill 能被触发。

## 跑测试

各 skill 的测试都离线可跑，逐个执行即可：

```bash
python3 plugins/project-docs/skills/project-docs/tests/test_build_html.py
python3 plugins/playground/skills/mbti-test/tests/test_mbti_test.py
```

预期输出末尾均为 `OK`。改动 `marketplace.json` 后校验 JSON：

```bash
python3 -m json.tool .claude-plugin/marketplace.json > /dev/null && echo "json ok"
```

## 常用命令速查

| 命令 | 作用 |
|------|------|
| `/plugin marketplace add <路径或 owner/repo>` | 添加市场 |
| `/plugin install <name>@manji` | 安装某插件 |
| `/plugin marketplace update manji` | 拉取市场最新内容 |
| `python3 plugins/*/skills/*/tests/test_*.py` | 跑某个 skill 的离线测试 |
| `bash scripts/version-check.sh` | 手动跑一次市场版本检查 |
| `git log --format= --name-only \| sort \| uniq -c \| sort -rn \| head` | 看热点文件 |

## 第一个练手任务

二选一，都能在 30 分钟内完成：

1. **给本套文档重建 HTML**：随便改一处 `docs/onboarding/*.md`（比如给术语表加一个词条），然后运行
   `python3 plugins/project-docs/skills/project-docs/scripts/build_html.py docs/onboarding`，
   打开 `docs/onboarding/index.html` 确认改动出现在页面里。你会顺路理解 frontmatter → 侧边栏/卡片的映射。
2. **本地装一个插件跑通闭环**：用上面"跑起来"的本地路径方式安装 `playground`，触发 mbti-test，
   再读一遍它的 `SKILL.md`，对照理解"description 触发 → 手册执行"这条主链路（见 04 流程二）。

## 卡住了怎么办

- 插件装了但 skill 不触发 → 十有八九是 `SKILL.md` frontmatter 的 `description` 触发词不够具体，对照 `plugins/playground/skills/mbti-test/SKILL.md` 的写法。
- `marketplace.json` 改完 Claude Code 不生效 → 跑 `/plugin marketplace update manji`（本地路径市场也要 update 才重读）。
- mermaid 图不渲染 → 首次构建需联网下载 mermaid.js（之后缓存于 `~/.cache/manji-project-docs/`）；节点文字里的 `(` `)` `"` 会导致解析失败。
- 规范类问题 → `CONTRIBUTING.md` 有完整的目录布局、manifest 规范和 PR checklist。
