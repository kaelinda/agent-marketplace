---
name: preference-memory
description: 偏好记忆管理 — 管理用户偏好设置（编码风格、工具偏好、输出格式等）。
category: memory-type
---

# preference-memory — 偏好记忆

## 触发条件
- 用户表达偏好（"我喜欢用vim"、"默认用中文回复"）
- Agent 需要个性化设置时查询
- 偏好变更时更新

## 用法
```bash
ov-memory pref list
ov-memory pref set --key "editor" --value "vim"
ov-memory pref get --key "editor"
ov-memory pref delete --key "editor"
```

## 存储格式
键值对形式，支持嵌套：
```json
{"key": "coding.style", "value": "functional", "scope": "user"}
```

## 内部接口
```python
from skills.preference_memory.scripts.preference_memory import run_pref
run_pref(config, action="set", key="language", value="中文")
result = run_pref(config, action="get", key="language")
```

## 命名空间
`{user_scope}/preferences/`
