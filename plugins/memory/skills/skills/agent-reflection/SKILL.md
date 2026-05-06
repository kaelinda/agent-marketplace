---
name: agent-reflection
description: Agent 自省记忆 — 记录 Agent 的工作反思、错误教训和改进经验。
category: memory-type
---

# agent-reflection — Agent 自省

## 触发条件
- Agent 犯错后记录教训
- 完成复杂任务后总结经验
- 周期性复盘 Agent 表现

## 用法
```bash
ov-memory reflection list
ov-memory reflection add --title "标题" --content "反思内容"
ov-memory reflection recall [--query "关键词"]
```

## 记忆类型
存储在 agent scope 下的 `agent_reflection` 类型：
- 错误教训（哪里做错了、如何避免）
- 成功经验（什么做得好、如何复用）
- 工作模式改进
- 工具使用技巧

## 内部接口
```python
from skills.agent_reflection.scripts.reflection import run_reflection
run_reflection(config, action="add", title="部署失误",
               content="忘记检查端口占用导致部署失败，下次先lsof检查")
```

## 命名空间
`{agent_scope}/reflections/`

## 注意事项
- 存储在 agent scope 而非 user scope
- 召回时优先检查 agent scope
- 反思记忆应简洁具体，避免空泛描述
