---
name: memory-share
description: >
  当用户希望把一条已有记忆共享 / 取消共享给另一个 agent / user / team，或想列出
  已共享给自己的记忆时使用。具体场景：
  (1) 用户说"把这条记忆分享给 X agent" / "share memory <id> with <ident>"；
  (2) 用户说"取消 / 撤销分享" / "unshare from"；
  (3) 用户问"我能看到哪些别人共享过来的记忆" / "what memories are shared with me"；
  (4) Agent 完成任务后想把成果记录共享给团队（写到 team scope 或显式 shared_with）。
  覆盖 read / write 两档权限；目标身份必须匹配 ^(user|agent|team):.+$，不合规直接
  reject 不发到 backend。HTTP / MCP 后端走 read-modify-write 兼容路径，mem0 后端
  原生通过 metadata filter 实现。
category: memory-sharing
---

# memory-share — 跨 Agent 记忆共享

## 触发条件

- 用户明确说"把记忆分享给 X" / "解除共享" / "看看共享给我的"
- Agent 工作流末尾要把结果共享给团队
- 评估当前调用方对一条记忆有没有 read/write 权限

## 用法

```bash
# 授权 read（默认）
memory-cli share <memory-id> --to <kind>:<id>
# 授权 write
memory-cli share <memory-id> --to agent:devbot --permission write

# 撤销
memory-cli unshare <memory-id> --to <kind>:<id>

# 列出"已共享给我"的所有记忆（合并 user / agent / 所有 team_ids）
memory-cli subscribed
```

### 参数

| 参数 | 说明 |
|------|------|
| `<memory-id>` | 必填，要共享 / 取消共享的记忆 ID |
| `--to` | 必填，目标身份串 `<kind>:<id>`，kind ∈ {user, agent, team} |
| `--permission` | `read` (默认) 或 `write` |

## 后端能力

| Backend | share / unshare | list_subscribed |
|---|---|---|
| `mem0` | ✅ 原生（metadata.shared_with） | ✅ metadata filter |
| `openviking` (HTTP) | ⚠️ 客户端 read-modify-write | ❌ 不支持 (Phase 4) |
| `openviking-mcp` | ⚠️ 客户端 read-modify-write | ❌ 不支持 (Phase 4) |

OpenViking 服务端 ACL 端点在 Phase 4 落地前，HTTP/MCP 的 `subscribed` 子命令会回 `ok=False`
+ 引导文案。`share` / `unshare` 通过客户端 update 兼容写入。

## 内部接口

```python
from lib import SharingManager, get_adapter, load_config
config = load_config()
adapter = get_adapter(config)
sm = SharingManager(adapter, config)

sm.share("mem_abc", "team:platform", permission="read")
sm.unshare("mem_abc", "team:platform")
sm.list_my_subscriptions()               # → {ok, data: [memory dicts]}
sm.can_access(memory_dict, op="read")    # → bool
```

## 安全注意

- 默认 `safety.auto_include_subscribed=false`：recall 不自动把 team scope 折进结果，
  必须 `--include-subscribed` 或 config 显式打开。这样不会因为加了 team 就把
  Agent 之前的工作流污染。
- ACL 在 SharingManager.can_access 评估，是 recall 之外的二道闸 —— 即使后端
  ACL 没生效，这里也会过滤掉调用方不该读到的记忆。
- 目标身份串校验先于 backend 调用，typo 不会消耗 round-trip 也不会产生奇怪的
  写入。
