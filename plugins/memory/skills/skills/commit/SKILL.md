---
name: commit
description: 从会话记录中提取值得持久化的记忆候选，支持预览和批量提交。
category: memory-foundation
---

# commit — 会话记忆提取

## 触发条件
- 会话结束时提取有价值的记忆
- 用户要求"保存这次对话的要点"
- 周期性自动提取（配合定时任务）

## 用法
```bash
ov-memory commit --session-file FILE [--apply]
```

### 参数
| 参数 | 说明 |
|------|------|
| `--session-file` | 会话 JSON 文件路径（必填） |
| `--apply` | 直接存储候选记忆（默认仅预览） |

## 提取流程
1. 解析会话消息列表
2. 跳过短内容（< 30字符）和敏感内容
3. 用 `STORE_WORTHY_INDICATORS` 筛选值得存储的内容
4. 自动分类每条候选记忆
5. 预览模式：显示候选列表；`--apply` 模式：批量写入

## 会话文件格式
```json
{
  "messages": [
    {"role": "user", "content": "..."},
    {"role": "assistant", "content": "..."}
  ]
}
```

## 内部接口
```python
from skills.commit.scripts.commit import run_commit
result = run_commit(config, session_data=session_dict, apply=True)
```

## 注意事项
- 预览模式不会写入任何数据
- 已有相似记忆时不会重复存储
- 候选记忆经过完整敏感检测流程
