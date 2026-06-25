# Playground Plugin

趣味 / 实验性技能集合 —— 拿来玩的工具，不承担严肃生产职责。

## Skills

### mbti-test

根据本机 **Claude Code**（`~/.claude/projects`）和 **Codex**（`~/.codex/sessions`）的
会话历史，分析你**亲手输入的提示词**，从四个维度（E/I、S/N、T/F、J/P）推断一个娱乐向的
MBTI 类型。

- **纯本地**：只读取本机文件，只分析你自己的文字（助手回复、工具输出、子代理转录、
  超长粘贴都会被过滤），**全程不联网、不上传任何数据**。
- **透明可解释**：评分基于中英文关键词词率 + 结构信号（路径密度、礼貌用语、计划/探索
  词等），`-v` 可查看每个维度命中的关键词证据。打分细节见
  [`scoring.md`](skills/mbti-test/references/scoring.md)。

**快速开始：**

```bash
SCRIPT=plugins/playground/skills/mbti-test/scripts/mbti_test.py

python3 $SCRIPT analyze            # 综合两个工具、全部历史，输出人格卡片
python3 $SCRIPT analyze -v         # 附带每个维度的关键词证据
python3 $SCRIPT analyze --source codex --days 30   # 只看 Codex、最近 30 天
python3 $SCRIPT sources            # 看看会分析哪些会话文件
```

**依赖：** 仅 Python 3 标准库，无需安装任何包。

**运行测试：**

```bash
python3 plugins/playground/skills/mbti-test/tests/test_mbti_test.py
```

> ⚠️ 娱乐向工具，反映的是你在 AI 编码会话里的**表达习惯**，不是心理诊断。

详情请见 [mbti-test 技能文档](skills/mbti-test/SKILL.md)。
