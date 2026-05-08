---
name: memory-doctor
description: >
  当 memory 操作出错或要验证 memory plugin 配置时使用。具体场景：
  (1) 用户报告"记忆操作失败" / "recall 没结果" / "capture 报错"；
  (2) 首次部署或切换后端 (HTTP / MCP / mem0) 后验证连通性；
  (3) 怀疑 identity / API key / scope 配置有问题；
  (4) 用户主动说 "doctor" / "检查记忆系统" / "memory health check"。
  会跑配置检查 + 后端 ping + 默认 identity 安全断言；--mode full 还会做
  写→搜→读→删的端到端闭环测试。
category: memory-foundation
---

# memory-doctor — 记忆系统诊断

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
from lib.skill_loader import load_skill_module
run_doctor = load_skill_module("memory-doctor", "doctor").run_doctor
result = run_doctor(config, mode="standard")
```

## 注意事项
- `quick` 模式不测试网络连通，仅检查本地配置
- `standard` 模式会 ping OpenViking 服务
- `full` 模式会创建并删除一条测试记忆，需服务在线
- 诊断结果不写入记忆库（测试记忆会被清理）
