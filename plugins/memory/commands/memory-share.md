---
description: 把一条记忆共享给另一个 agent / user / team，或撤销共享，或列出已共享给我的记忆
argument-hint: share <memory-id> <target> | unshare <memory-id> <target> | subscribed
---

请使用 memory plugin 的 `memory-share` skill，根据用户输入决定走 share / unshare / subscribed 三个动作之一。

调度规则：

1. **解析参数 `$1`**
   - 关键字 `share` 或缺省 → 走授权
   - 关键字 `unshare` / `revoke` → 走撤销
   - 关键字 `subscribed` / `mine` / `shared-with-me` → 走"列出共享给我的"
   - 都不匹配 → 返回 usage：`/memory-share share <id> <target>`、`/memory-share unshare <id> <target>`、`/memory-share subscribed`

2. **执行命令**
   ```bash
   bash "<skill_dir>/../../scripts/memory-cli" share "$2" --to "$3" [--permission write]
   ```
   或者：
   ```bash
   bash "<skill_dir>/../../scripts/memory-cli" unshare "$2" --to "$3"
   ```
   或者：
   ```bash
   bash "<skill_dir>/../../scripts/memory-cli" subscribed
   ```

3. **目标身份串校验**：`<target>` 必须形如 `<kind>:<id>`，其中 kind ∈ {user, agent, team}。如果用户给的是裸名字（例如只写 `devbot` 而不是 `agent:devbot`），先反问澄清是 agent / user / team 哪种身份，再带上前缀重发命令。

4. **结果展示**：成功时把 backend 返回的 `target` / `permission` 字段告诉用户；失败时把 `error` 字段原样输出（多数错误是"backend 不支持 list_subscribed"或"target 格式错误"等可操作信息）。

5. **不要并行调用** `share` 与 `recall`：share 写入 + recall 召回不在同一事务里，召回前先 sleep 0.3s 让 backend 索引追上（Phase 4 加同步等待）。

模式对照：

| 子命令 | 触发词 | 何时用 |
|---|---|---|
| `share` | "share with" / "把这条分享给" | 显式授权另一个身份读 / 写 |
| `unshare` | "unshare" / "revoke" / "撤销" | 收回访问权 |
| `subscribed` | "shared with me" / "subscribed" / "共享给我的" | 看队友共享了哪些记忆给我 |
