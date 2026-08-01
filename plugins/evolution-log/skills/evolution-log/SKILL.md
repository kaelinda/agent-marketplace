---
name: evolution-log
description: 记录与查询项目演进史(方案变更、需求变更、架构迁移、技术决策)。当用户说"记录一下这次变更"、"方案A改成B了"、"记一笔"、提到要留档某个决策,或询问"为什么当初…"、"是谁牵头/决定的"、"从X到Y是什么原因"、"这块的演进历史"时,务必使用本 skill。首次在项目里启用(用户说"初始化演进日志"、"给这个项目开演进记录")也走本 skill。在完成重大重构、迁移或方案切换类任务后,也应主动使用本 skill 提议记录。收到 [evolution-log hook] 补录指令时同样遵循本 skill。
---

# Evolution Log — 项目演进记录

维护一份随代码库流转的项目演进日志:每条记录回答"从什么变成什么、为什么、谁牵头"。
记录文件是唯一事实来源,索引(INDEX.md / records.json)永远可以由脚本重建。

## 脚本路径解析(执行任何脚本前先确定)

本 skill 的脚本在插件目录 `${CLAUDE_PLUGIN_ROOT}/scripts/` 下:
`evolog-init.py`(初始化)、`evolog-index.py`(索引重建)、`evolog-check.py`(Stop hook 判定,由插件自动调用,不需要你手动跑)。

调用时优先用 `${CLAUDE_PLUGIN_ROOT}/scripts/<name>.py`。若运行时不提供该变量
(如 Codex 兼容模式),退回项目内副本 `.claude/hooks/evolog-index.py`;两者都不存在时,
先走**工作流零**完成初始化。

## 存储位置解析(所有记录/查询工作流的第一步)

按以下优先级确定存储目录 `$STORAGE`,任何时候不要硬编码路径:

1. 环境变量 `EVOLOG_DIR`(若非空)
2. 项目 `.claude/evolution-log.json` 中的 `storage_dir` 字段
3. 默认 `docs/evolution/`(相对项目根)

记录位于 `$STORAGE/records/*.md`,索引为 `$STORAGE/INDEX.md` 与 `$STORAGE/.cache/records.json`。

## 工作流零:初始化项目

触发:用户要求"在这个项目启用演进日志";或执行记录/查询时发现
`.claude/evolution-log.json` 与 `$STORAGE` 都不存在。

1. 先跑一次预演,把将要发生的写入念给用户听:
   `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/evolog-init.py" --dry-run`
2. 询问两件事:存储目录(默认 `docs/evolution`)、是否需要 `--standalone`
   (团队成员不都装插件时选它:把 hook 脚本落进仓库,clone 即生效;Codex 用户加 `--codex`)。
3. 用户确认后执行(按需附加 `--storage-dir` / `--standalone` / `--codex`),
   把脚本打印的"已处理 / 跳过"清单原样反馈给用户。
4. 提醒两条团队约定:`.claude/`、`.codex/` 目录的变更建议配 CODEOWNERS 审批;
   首次触发 hook 时 Claude Code 会请求信任,让用户先读一遍 `evolog-check.py` 再确认。

脚本幂等,已存在的文件一律不覆盖(除非用户明确要求 `--force`)。

## 工作流一:记录变更

触发:用户明确要求记录;或收到 [evolution-log hook] 的补录指令。

1. **提取七要素**:从当前会话、代码 diff、用户描述中提取
   type(solution_change / requirement_change / migration / decision)、
   from、to、变更原因、owner(牵头人)、participants、date(决策发生日,非今天,除非就是今天)。
2. **追问缺失的必填项**:owner 与变更原因绝不允许留空猜测——提取不到就问用户,
   一次把所有缺失项问完,不要分多轮。可选项(participants、tags、commits)缺失则跳过。
3. **冲突检查**:读 `$STORAGE/.cache/records.json`(不存在则读 INDEX.md),
   检查是否已有语义相近的记录(相似的 from/to)。若有,询问用户:
   更新旧记录,还是新建记录并将旧记录标记为被取代(supersedes)?
4. **落盘**:复制本 skill 的 `templates/record.md` 为
   `$STORAGE/records/YYYY-MM-DD-<slug>.md`(slug:从标题生成的英文或拼音短语,
   ≤40 字符,小写连字符;同名冲突追加 `-2`),填入全部字段与正文各章节。
   - 用户在对话中确认过内容 → `status: confirmed`、`source: manual`
   - 由 hook 触发的自动补录 → `status: draft`、`source: auto_hook`
   - 若本记录 supersedes 了旧记录:同时把旧记录文件的 `status` 改为 `superseded`
5. **重建索引**:运行 `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/evolog-index.py"`,
   然后向用户展示写入记录的摘要(id、变更、owner、状态)。

正文写作要求:重点写"变更原因"和"被否掉的备选方案"——后者是最容易丢失、
未来最有价值的信息;宁可短而准确,不要长而空洞。

## 工作流二:查询演进史

触发:用户问"为什么当初…"、"谁牵头/决定的"、"从X到Y是什么原因"、"演进历史"。

按三跳漏斗执行,控制上下文开销:

1. **第一跳(结构化过滤)**:解析问题中的维度(人?时间段?from/to?类型?专题),
   读 `$STORAGE/.cache/records.json`(不存在则读 INDEX.md,再不存在则告知用户暂无记录),
   用宽松的语义匹配筛出候选——宁可多召回,交给下一跳精判。
2. **第二跳(读正文)**:最多打开 3 个候选记录文件,读"变更原因/被否掉的备选方案/
   决策过程"章节提取答案。候选超过 3 个时先向用户澄清缩小范围。
3. **第三跳(沿链扩展)**:若问题涉及完整演进史,沿 `supersedes` 链回溯、
   结合 `related` 扩展,按时间排序输出演进路径。

回答时注明信息来源的记录 id;`status: draft` 的记录要向用户说明"此条为自动草稿,
尚未经人确认"。查不到就直说查不到,不要编造。

## 工作流三:主动提醒

在你自己刚完成一次重大重构、技术栈替换、架构迁移或方案切换类任务后,
主动问一句:"这次变更要不要记入演进日志?"用户同意则走工作流一。
普通编码、修 bug、小改动不要提,避免打扰。

## 草稿确认

用户说"确认某条记录"时:打开该记录,向用户复述关键字段请其核对,
把 `status: draft` 改为 `confirmed`,重建索引。

## 记录门槛(判断该不该记)

满足任一即应记录:改变了对外行为或接口;推翻了此前的技术选型;
影响多个模块/团队;回滚成本高。普通编码与修 bug 不记。
