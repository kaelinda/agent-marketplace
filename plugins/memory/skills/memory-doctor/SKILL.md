---
name: doctor
description: OpenViking 记忆系统诊断检查。检测后端连接、命名空间、策略配置、MCP 适配器状态。
category: memory-foundation
---

# doctor — 记忆系统诊断

## 触发条件
- 用户要求检查记忆系统状态
- 首次部署后验证配置
- 记忆操作异常时排查问题

## 用法
```bash
ov-memory doctor [--mode quick|standard|full]
```

### 模式说明
| 模式 | 检查项 |
|------|--------|
| `quick` | 配置加载 + API key + 身份标识警告 |
| `standard` (默认) | quick + 服务可达性(ping) + MCP 工具配置 + 命名空间可读 |
| `full` | standard + write→search→read→delete 完整循环测试 |

## 输出格式
返回结构化诊断字典，包含：
- `result` — 总体结果：`PASS` / `PASS_WITH_WARNINGS` / `FAIL`
- `meta` — 运行元信息（mode, endpoint, tenant, user, agent）
- `checks` — 每项检查的 `pass`/`warn`/`fail`/`skip` 状态
- `warnings` — 警告列表
- `errors` — 错误列表

## 内部接口
```python
from skills.doctor.scripts.doctor import run_doctor
result = run_doctor(config, mode="standard")
```

## 注意事项
- `quick` 模式不测试网络连通，仅检查本地配置
- `standard` 模式会 ping OpenViking 服务
- `full` 模式会创建并删除一条测试记忆，需服务在线
- 诊断结果不写入记忆库（测试记忆会被清理）
