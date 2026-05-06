---
name: case-memory
description: 案例记忆管理 — 记录问题排查过程和解决方案，形成知识库。
category: memory-type
---

# case-memory — 案例记忆

## 触发条件
- 解决了一个疑难问题后记录
- 遇到类似问题时搜索历史案例
- 问题复盘时回顾

## 用法
```bash
ov-memory case list
ov-memory case create --title "标题" --problem "问题描述" --solution "解决方案"
ov-memory case recall [--query "关键词"]
```

## 记忆结构
每条案例记忆包含：
- `title` — 案例标题
- `problem` — 问题描述
- `solution` — 解决方案
- `tags` — 标签（自动提取）

## 内部接口
```python
from skills.case_memory.scripts.case_memory import run_case
result = run_case(config, action="create", title="OOM排查",
                  problem="容器OOM killed", solution="增加memory limit到2Gi")
```

## 命名空间
`{user_scope}/cases/`
