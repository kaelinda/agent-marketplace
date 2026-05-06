---
name: memory-admin
description: 记忆管理后台 — 统计、备份、去重、清理、审计等管理操作。
category: memory-governance
---

# memory-admin — 记忆管理

## 触发条件
- 定期维护（去重、清理过时记忆）
- 备份/恢复记忆数据
- 审计记忆健康状况

## 用法
```bash
ov-memory admin stats [--scope SCOPE]
ov-memory admin backup [--output FILE] [--scope SCOPE]
ov-memory admin restore --file FILE
ov-memory admin dedupe [--scope SCOPE]
ov-memory admin prune [--status STATUS]
ov-memory admin audit [--scope SCOPE]
```

### 子命令
| 命令 | 说明 |
|------|------|
| `stats` | 显示记忆统计（总数、类型分布、状态分布） |
| `backup` | 导出记忆为 JSON 文件（默认自动生成带时间戳的文件名） |
| `restore` | 从备份文件恢复记忆，报告成功/失败数 |
| `dedupe` | 按 type+title 检测并保留最新版本，标记旧版为 deleted |
| `prune` | 清理已删除/过时记忆（默认 status=deleted+obsolete，可用 --status 指定） |
| `audit` | 敏感数据扫描，报告含密码/密钥/Token 的记忆 |

### 参数
| 参数 | 适用命令 | 说明 |
|------|----------|------|
| `--scope` | stats/backup/dedupe/prune/audit | 指定命名空间（默认 user_scope） |
| `--output` | backup | 输出文件路径 |
| `--file` | restore | 备份文件路径 |
| `--status` | prune | 只清理指定状态的记忆（默认 deleted+obsolete） |

## 内部接口
```python
from skills.memory_admin.scripts.admin import run_admin
result = run_admin(config, action="stats", scope="user")
result = run_admin(config, action="prune", older_than="180d")
result = run_admin(config, action="backup", output="/tmp/backup.json")
```

## 注意事项
- `prune` 使用 soft delete，可通过 restore 恢复
- `dedupe` 保留最新的记忆版本
- `backup`/`restore` 操作记录审计日志
