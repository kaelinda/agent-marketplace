# `memory-cli` 完整参考

`memory-cli` 是 plugin 的唯一可执行入口。Skills / commands 都最终调它。所有命令都接受顶层 `--config <path>`，覆盖默认的 [config 搜索路径](configuration.md#搜索路径)。

> 兼容性：`scripts/ov-memory` 是 `memory-cli` 的 shell-shim alias，v0.3.0 删除。新代码一律用 `memory-cli`。

## 全局参数

| 参数 | 说明 |
|---|---|
| `--config PATH` | 显式指定 config.json，绕过搜索路径与 `OV_MEMORY_CONFIG` |

## 命令一览

| 命令 | 用途 |
|---|---|
| `doctor`     | 体检：配置 + 后端 + 端到端闭环 |
| `recall`     | 召回相关记忆 |
| `capture`    | 写入一条新记忆 |
| `merge`      | 把新内容并入已有记忆 |
| `forget`     | 删除 / 标记 obsolete |
| `commit`     | 从会话文件抽候选写入 |
| `browse`     | 按 scope 浏览 |
| `read`       | 按 ID 读 |
| `project`    | 项目记忆子命令组 |
| `env`        | 环境记忆子命令组 |
| `case`       | 故障案例子命令组 |
| `pref`       | 偏好子命令组 |
| `reflection` | Agent 反思子命令组 |
| `admin`      | 治理：stats / backup / restore / dedupe / prune / audit |

`memory-cli --help` 始终是最新的；下文按调用频度排序。

---

## doctor

```bash
memory-cli doctor [--mode quick|standard|full]
```

| `--mode` | 检查项 | 大致耗时 |
|---|---|---|
| `quick`    | 配置加载 + API key + identity safety | < 100ms |
| `standard` (默认) | quick + ping + MCP tool + scope 可读 | 1–3 s |
| `full`     | standard + write→search→read→delete 端到端 | 5–15 s |

**退出码**：`result != FAIL` → 0；`FAIL` → 1。CI 里直接判 `$?` 就行。

## recall

```bash
memory-cli recall <query> [--type TYPE[,TYPE...]] [--limit N]
```

| 参数 | 默认 | 说明 |
|---|---|---|
| `query` | (必填) | 查询字符串，位置参数 |
| `--type` | 全部 | 逗号分隔的类型过滤 |
| `--limit` | 6 | 上限受 `recall.max_limit` 限制（默认 12） |

输出：要么 `[Relevant OpenViking Memory] ... [/Relevant OpenViking Memory]` 块，要么 `(no relevant memories found)`。

## capture

```bash
memory-cli capture --content TEXT [--type TYPE] [--title TITLE] [--scope SCOPE] [--auto-classify]
```

| 参数 | 说明 |
|---|---|
| `--content`        | 记忆内容（必填） |
| `--type`           | 类型；不传 / 加 `--auto-classify` → 自动推断 |
| `--title`          | 默认取 `content[:80]` |
| `--scope`          | 强制写入指定 scope（默认按 type 路由） |
| `--auto-classify`  | 强制自动分类并打印 confidence |

写入失败会原样把后端错误抛回（exit 1），不会静默丢。

## merge

```bash
memory-cli merge --memory-id ID --new TEXT
```

把 `--new` 的内容合并到 ID 指定的记忆里。语义上是"补充信息"，不是"替换"——具体合并策略看 `lib/policy.py` + 后端实现。

## forget

```bash
memory-cli forget (--memory-id ID | --query TEXT | --scope SCOPE)
                   [--mode soft|obsolete|hard]
```

三种识别方式互斥。`--mode` 默认 `soft`（保留可恢复）；`obsolete` 标记过时（仍存）；`hard` 真删。

## commit

```bash
memory-cli commit --session-file FILE [--apply]
```

读 session JSON 文件，预览（默认）或落盘（`--apply`）。文件格式：

```json
{"messages": [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]}
```

## browse

```bash
memory-cli browse [--scope SCOPE] [--limit N]
```

按 scope 列出记忆。`--scope` 缺省 → 当前 `user_scope`。

## read

```bash
memory-cli read <memory-id>
```

按 ID 读一条完整记忆。

## 类型化子命令组

下面这五个 group 是"针对特定类型的便捷封装"，底层依然走 capture / recall / write。能直接用 `capture --type X` 替代，但这几个保留是因为它们的字段更结构化。

### `project`

```bash
memory-cli project list
memory-cli project create <name> --content TEXT
memory-cli project recall <name> --query TEXT
memory-cli project update <name> --content TEXT
```

### `env`

```bash
memory-cli env list
memory-cli env capture --name NAME --os OS [--nginx-path PATH] [--content TEXT]
memory-cli env update --name NAME [--os OS] [--nginx-path PATH] [--content TEXT]
```

### `case`

```bash
memory-cli case list
memory-cli case create --title T --problem P --solution S
memory-cli case recall --query Q
```

### `pref`

```bash
memory-cli pref list
memory-cli pref set --key K --value V
memory-cli pref get --key K
memory-cli pref delete --key K
```

### `reflection`

```bash
memory-cli reflection list
memory-cli reflection add --title T --content C
memory-cli reflection recall --query Q
```

reflection 默认走 agent scope（区别于 user scope），用于 agent 对自己工作的复盘。

## admin

```bash
memory-cli admin stats   [--scope SCOPE]
memory-cli admin backup  [--output FILE] [--scope SCOPE]
memory-cli admin restore  --file FILE
memory-cli admin dedupe  [--scope SCOPE]
memory-cli admin prune   [--status STATUS] [--older-than 180d] [--type TYPE]
memory-cli admin audit   [--scope SCOPE]
```

⚠️ `dedupe` 和 `prune` 是真删。**先 `backup`**。详见 [skills.md#memory-admin](skills.md#memory-admin)。

## 退出码约定

| 退出码 | 含义 |
|---|---|
| `0` | 成功（或 doctor 是 PASS / PASS_WITH_WARNINGS） |
| `1` | 命令运行失败 / doctor FAIL / 必需参数缺失 |
| 其它 | argparse / Python 异常透传 |

CI / 自动化脚本直接 `set -e` 用就行。
