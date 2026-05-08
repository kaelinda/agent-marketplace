---
description: 跑一次 memory plugin 的诊断检查（配置 / 后端可达性 / 命名空间）
argument-hint: [quick|standard|full]
---

请使用 memory plugin 的 `memory-doctor` skill，对当前 memory 配置和后端做一次诊断检查。

执行流程：

1. 把参数 `$1` 当 mode；接受 `quick|standard|full`，缺省时按 `standard` 处理。
2. 调用：
   ```bash
   bash "<skill_dir>/../../scripts/memory-cli" doctor --mode "${1:-standard}"
   ```
3. 把命令输出原样展示给用户，包含：
   - 总体结果（PASS / PASS_WITH_WARNINGS / FAIL）
   - 各检查项 (✅ pass / ⚠️ warn / ❌ fail)
   - warnings / errors 列表
4. 如果结果是 **FAIL**：从 errors 列表里提取第一条作为根因，给出修复建议（最常见：未设置 `OV_USER_ID` / `OV_AGENT_ID`，需要导出环境变量或在 config.json 里改 identity；或者 `safety.allow_default_identity=true` 显式 opt-in）。
5. 如果是 **PASS_WITH_WARNINGS**：把 warnings 简要列出，让用户判断是否要处理。

模式对照：

| 模式 | 检查项 | 典型耗时 |
|---|---|---|
| `quick` | 配置加载 + API key + identity 安全 | < 100ms |
| `standard` | quick + 后端 ping + MCP 工具 + scope 配置 | 1–3s |
| `full` | standard + write→search→read→delete 端到端闭环（写入 doctor scope） | 5–15s |
