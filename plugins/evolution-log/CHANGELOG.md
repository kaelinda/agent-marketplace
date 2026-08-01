# evolution-log 变更日志

遵循 [语义化版本](https://semver.org/lang/zh-CN/)。`schema_version` 独立于插件版本,
描述 `.claude/evolution-log.json` 与 `.cache/records.json` 的结构;它变化时本文件会写明迁移方式。

## 0.2.0

当前 `schema_version: 1`。

### 安全

- 索引脚本拒绝跟随符号链接:输出路径及其每一级父目录逐级检查,合入仓库的
  `INDEX.md` / `records.json` symlink 不再能让 `post-merge` 覆盖任意可写文件
- 仓库外存储需要独立开关:仅由仓库内 `.claude/evolution-log.json` 指定的仓库外路径
  一律拒绝,需 `EVOLOG_DIR` 或 `--allow-external-storage` /
  `EVOLOG_ALLOW_EXTERNAL_STORAGE=1` 显式放行
- 索引写入改为原子操作(同目录临时文件 → `fsync` → `os.replace`),异常不再留下
  截断的 `INDEX.md` 或 `records.json`

### 集成

- skill 自包含:三个脚本移入 `skills/evolution-log/scripts/`,整个 skill 目录可独立
  分发,不再依赖项目根下的 `.claude/` 文件
- Codex 支持可用:`--codex` 把 skill 安装到 Codex 的仓库级发现目录
  `.agents/skills/evolution-log/`;`.codex/hooks.json` 的命令改为运行时解析
  `git rev-parse --show-toplevel`,修复从仓库子目录启动时 hook 找不到脚本的问题
- `.codex/hooks.json` 与 `.claude/settings.json` 一样走合并写入,保留已有 hook 注册

### 稳定性

- `evolog-init` 现在会执行 `git config merge.ours.driver true` —— 此前
  `.gitattributes` 里的 `merge=ours` 声明没有对应 driver,`INDEX.md` 照样报冲突
- 并发重建:拿不到锁的一方留下 `rebuild.pending` 标记,持锁方收尾时补跑一次,
  避免后到的记录长期不进索引
- frontmatter 校验:`date` 非法拒绝入索引;`type` / `status` 未知、关系字段写成标量、
  `id` 重复均打印告警但不丢记录
- 配置类型校验:数组项写成字符串时回落默认值并记录到 `error.log`
  (此前 `keywords` 写成字符串会退化为逐字符匹配,几乎每轮误报阻断)
- 已存在的 `post-merge` 不覆盖,并明确提示需要手工补哪一行

### 其他

- 配置与 `records.json` 加入 `schema_version`;`records.json` 结构由裸数组改为
  `{schema_version, generated_by, count, records}`
- 自测从 34 项扩到 71 项,新增 symlink 防护、仓库外存储策略、并发重建、Codex 子目录
  启动、merge driver 端到端、打包结构自包含等用例

### 升级说明（0.1.0 → 0.2.0）

- 读过 `.cache/records.json` 的自定义脚本需改为读取其中的 `records` 字段;
  或直接删掉该文件重跑 `evolog-index.py` 重建
- 已初始化的项目建议重跑一次 `evolog-init.py`,以补上 merge driver 配置
  与 `schema_version` 字段(幂等,不会覆盖已有文件)

## 0.1.0

首个版本:evolution-log skill(初始化 / 记录 / 查询 / 草稿确认)、Stop hook 自动兜底
(规则快筛 + 模型自评二级判定,opt-in、fail-open、零外发)、幂等索引重建、Git 内
结构化 Markdown 存储。
