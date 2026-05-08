---
name: memory-recall
description: >
  当用户请求查找/回顾长期记忆时使用。具体场景：
  (1) 用户问"之前关于 X 的记录" / "上次怎么处理的"；
  (2) Agent 启动新任务前需要从长期记忆里拉项目上下文 / 用户偏好 / 历史故障案例；
  (3) 任何包含 recall / remember / 之前 / 上次 / previously / what did 等触发词的请求。
  返回的记忆按相关度排序，以结构化块形式直接注入上下文。
category: memory-foundation
---

# memory-recall — 记忆召回

## 触发条件
- Agent 启动新任务时，自动召回相关记忆
- 用户询问"之前关于X的记录"
- 任务规划阶段需要参考历史经验

## 用法
```bash
ov-memory recall <query> [--type TYPE] [--limit N]
```

### 参数
| 参数 | 说明 | 默认值 |
|------|------|--------|
| `query` | 搜索查询文本 | 必填 |
| `--type` | 按记忆类型过滤（逗号分隔） | 全部类型 |
| `--limit` | 最大返回条数 | 6 |

## 检索策略
1. 按记忆类型优先级顺序检索（配置决定）
2. 过滤低于 `recall_min_score` 的结果
3. 冲突检测：发现矛盾记忆时标注警告
4. 格式化为结构化注入块

## 内部接口
```python
from lib.skill_loader import load_skill_module
run_recall = load_skill_module("memory-recall", "recall").run_recall
memories = run_recall(config, query="nginx配置", memory_type="environment", limit=6)
```

## 注入格式
```
[Relevant OpenViking Memory]
- Project: User is designing an OpenViking Memory Skill Suite...
- Environment: CentOS 8, Nginx path /www/server/nginx...
- Preference: User prefers Chinese explanations...
[/Relevant OpenViking Memory]
```

## 注意事项
- 最大返回数受 `recall.max_limit` 配置限制（默认 12）
- agent_reflection 类型会尝试 agent scope 检索
- 结果按相关度评分降序排列
