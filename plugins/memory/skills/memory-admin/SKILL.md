---
name: memory-admin
description: >
  当用户需要对记忆库做"运维级"操作时使用。具体场景：
  (1) 备份 / 恢复 (backup, restore)；
  (2) 看记忆总量 / 类型分布 (stats)；
  (3) 去重 (dedupe) — 同 type+title 保留最新版本，旧的硬删；
  (4) 清理过时记忆 (prune --status / --older-than)；
  (5) 安全审计 (audit) — 扫描已存记忆里是否含密码/API key 等敏感数据。
  注意：dedupe 与 prune 都是不可逆操作（默认会真删），跑前要让用户确认 scope。
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
from lib.skill_loader import load_skill_module
run_admin = load_skill_module("memory-admin", "admin").run_admin
run_admin(config, action="stats", scope="user")
run_admin(config, action="prune", older_than="180d")
run_admin(config, action="backup", output="/tmp/backup.json")
```

## 注意事项
- `prune` / `dedupe` 默认走硬删（adapter.delete），不再像 v0.1 那样
  打 `status="deleted"` 墓碑——后者会污染 browse / search 结果且无人清理
- `backup` 是当前 scope 的全量导出，按时间戳生成默认文件名
- `restore` 不修改入参 dict（旧版本用 `pop("id")` 会破坏备份原文件）
- `dedupe` 保留同 type+title 中 updated_at / created_at 最新的那条
