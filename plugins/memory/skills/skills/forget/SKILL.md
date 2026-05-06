---
name: forget
description: 遗忘记忆 — 支持按 ID、搜索查询或范围删除/标记过时/隐藏。
category: memory-foundation
---

# forget — 记忆遗忘

## 触发条件
- 用户要求删除某条记忆
- 定期清理过时记忆
- 用户要求"忘掉关于X的所有记录"

## 用法
```bash
ov-memory forget --memory-id ID [--mode soft|obsolete|hard]
ov-memory forget --query "关键词" [--mode soft|obsolete|hard]
ov-memory forget --scope SCOPE [--mode soft|obsolete|hard]
```

### 遗忘模式
| 模式 | 效果 |
|------|------|
| `soft` (默认) | 标记为已删除，可恢复 |
| `obsolete` | 标记为过时，召回时降权 |
| `hard` | 永久删除，不可恢复 |

### 目标选择（三选一）
| 参数 | 说明 |
|------|------|
| `--memory-id` | 指定记忆 ID |
| `--query` | 搜索匹配的记忆 |
| `--scope` | 删除指定命名空间下所有记忆 |

## 内部接口
```python
from skills.forget.scripts.forget import run_forget
result = run_forget(config, memory_id="abc123", mode="soft")
result = run_forget(config, query="旧项目", mode="obsolete")
```

## 注意事项
- `hard` 模式不可逆，执行前无确认（CLI 层面自行确认）
- `soft` 删除的记忆仍可通过 admin restore 恢复
- 按 scope 批量删除受 `policy.max_batch_forget` 限制
