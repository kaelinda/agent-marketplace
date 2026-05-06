---
name: merge
description: 将新信息合并到已有记忆中，保留历史版本痕迹。
category: memory-foundation
---

# merge — 记忆合并

## 触发条件
- 用户说"更新之前的记录"
- 发现已有记忆需要补充新信息
- 信息变更（如配置路径更新）

## 用法
```bash
ov-memory merge --memory-id ID --new "新内容"
```

## 合并策略
1. 读取原始记忆内容
2. 追加新内容，用 `[Updated]` 标记分隔
3. 更新摘要为新内容前 200 字符
4. 更新 `updated_at` 时间戳
5. 写回存储

## 内部接口
```python
from skills.merge.scripts.merge import run_merge
result = run_merge(config, memory_id="abc123", new_content="路径改为/opt/nginx/")
```

## 输出示例
合并后内容：
```
原始内容...

[Updated] 路径改为/opt/nginx/
```

## 注意事项
- 合并是追加式，不替换原始内容
- 每次合并都更新时间戳
- 频繁合并的记忆建议定期 commit 重建
