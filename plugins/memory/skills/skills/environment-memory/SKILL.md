---
name: environment-memory
description: 环境记忆管理 — 记录操作系统、Nginx、部署路径等环境配置信息。
category: memory-type
---

# environment-memory — 环境记忆

## 触发条件
- 查询服务器环境配置
- 记录新的环境配置信息
- 环境变更后更新记忆

## 用法
```bash
ov-memory env list
ov-memory env capture --name "prod-server" [--os "Ubuntu 22.04"] [--nginx-path "/etc/nginx"] [--content "详情"]
ov-memory env update --name "prod-server" --content "更新内容"
```

### 参数
| 参数 | 说明 |
|------|------|
| `--name` | 环境名称标识 |
| `--os` | 操作系统信息（如 Ubuntu 22.04） |
| `--nginx-path` | Nginx 配置路径 |
| `--content` | 补充说明（capture 时至少需提供一个参数；update 时必填） |

## 记忆类型
存储在 `environment` scope 下，包含：
- 操作系统版本和特性
- Nginx/Apache 配置路径
- 部署目录结构
- 系统服务配置
- 包管理器和版本

## 内部接口
```python
from skills.environment_memory.scripts.environment_memory import run_env
result = run_env(config, action="capture", name="prod", os_name="Ubuntu 22.04", nginx_path="/etc/nginx")
result = run_env(config, action="update", name="prod", content="新增 Redis 缓存配置")
```

## 命名空间
`{user_scope}/environments/`
