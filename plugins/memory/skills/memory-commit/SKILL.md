---
name: memory-commit
description: >
  当一段会话结束、需要把"这次对话学到的东西"沉淀进长期记忆时使用。
  具体场景：
  (1) 用户说"保存这次对话的要点" / "把刚才的经验记下来" / "commit memory"；
  (2) 长会话结束前定期 / 自动 checkpoint，从 session 中抽长期价值的事实；
  (3) Agent 自身在重要决策 / 排障收尾后主动沉淀经验。
  默认输出"候选预览"供用户确认；加 --apply 才真正写入（避免污染记忆库）。
category: memory-foundation
---

# memory-commit — 会话记忆提取

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
from lib.skill_loader import load_skill_module
run_commit = load_skill_module("memory-commit", "commit").run_commit
result = run_commit(config, session_data=session_dict, apply=True)
```

## 注意事项
- 预览模式不会写入任何数据
- 已有相似记忆时不会重复存储
- 候选记忆经过完整敏感检测流程
