---
name: project-memory
description: 项目记忆管理 — 创建、查询、更新项目级别的长期记忆。
category: memory-type
---

# project-memory — 项目记忆

## 触发条件
- 创建/查询/更新项目配置、架构决策、技术栈信息
- 项目切换时加载对应上下文

## 用法
```bash
ov-memory project list
ov-memory project create <name> [--content "内容"]
ov-memory project recall [--query "关键词"]
ov-memory project update <name> [--content "新内容"]
```

## 记忆类型
存储在 `project` scope 下，包含：
- 技术栈选型及理由
- 架构决策记录（ADR）
- 项目配置信息
- 构建/部署流程

## 内部接口
```python
from skills.project_memory.scripts.project_memory import run_project
result = run_project(config, action="create", name="my-api", content="FastAPI + PostgreSQL")
```

## 命名空间
`{user_scope}/projects/{project_name}/`
