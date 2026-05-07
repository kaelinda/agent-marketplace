---
name: version-update
description: >
  版本检测与自动更新。触发场景：
  (1) 每次使用 manji 市场中的任意 skill 时自动触发检查
  (2) 用户手动询问"检查更新"、"有没有新版本"、"update check"
  (3) 用户要求升级 manji 市场
---

# Manji 版本检测与更新

在执行任何 skill 之前，先检查 manji 市场是否有新版本可用。

## 前置检查流程

**每次 skill 激活时**，执行以下检查（静默执行，无输出则跳过）：

```bash
bash "<skill_dir>/../../../scripts/version-check.sh" 2>/dev/null
```

脚本输出解读：
- `UPGRADE_AVAILABLE <local> <remote>` — 有新版本，进入交互流程
- `UP_TO_DATE` 或无输出 — 已是最新，继续执行 skill

## 交互流程

当检测到 `UPGRADE_AVAILABLE` 时，使用 AskUserQuestion 向用户展示以下选项：

### 选项 1: "立即更新"
执行更新：
```bash
bash "<skill_dir>/../../../scripts/manji-upgrade.sh"
```
更新成功后继续执行原 skill。

### 选项 2: "自动保持最新"
写入配置开启自动更新：
```bash
mkdir -p ~/.manji
python3 -c "
import json, os
cfg_path = os.path.expanduser('~/.manji/config.json')
cfg = {}
if os.path.exists(cfg_path):
    cfg = json.load(open(cfg_path))
cfg['auto_upgrade'] = True
json.dump(cfg, open(cfg_path, 'w'), indent=2)
"
```
然后执行更新脚本。告知用户：今后将自动更新，可通过 `~/.manji/config.json` 关闭。

### 选项 3: "稍后提醒"
写入 snooze 状态（递增推迟：24h → 48h → 7d）：
```bash
bash "<skill_dir>/../../../scripts/version-check.sh"  # 脚本内部处理 snooze
```
告知用户下次提醒时间，继续执行原 skill。

### 选项 4: "不再检查"
写入配置禁用更新检查：
```bash
mkdir -p ~/.manji
python3 -c "
import json, os
cfg_path = os.path.expanduser('~/.manji/config.json')
cfg = {}
if os.path.exists(cfg_path):
    cfg = json.load(open(cfg_path))
cfg['update_check_disabled'] = True
json.dump(cfg, open(cfg_path, 'w'), indent=2)
"
```
告知用户：已禁用更新检查，可通过编辑 `~/.manji/config.json` 重新启用。

## 自动更新模式

当 `~/.manji/config.json` 中 `auto_upgrade` 为 `true` 时：
1. 检测到新版本后直接执行更新，不询问用户
2. 更新失败时回退并警告用户
3. 更新成功后静默继续执行原 skill

## 配置文件

`~/.manji/config.json` 结构：
```json
{
  "auto_upgrade": false,
  "update_check_disabled": false
}
```

## 缓存与频率控制

版本检查结果缓存在 `~/.manji/last-update-check`：
- 已是最新：缓存 60 分钟
- 有新版本：缓存 12 小时

用户选择"稍后提醒"后，推迟记录在 `~/.manji/update-snoozed`：
- 第 1 次：24 小时
- 第 2 次：48 小时
- 第 3 次及以后：7 天（上限）

检测到新版本（与已推迟版本不同）时重置推迟计时。

## 升级机制

更新脚本自动检测安装方式：
- **Git 安装**：`git fetch` + `git reset --hard origin/main`
- **Vendored 安装**：浅克隆最新版本，替换当前目录，保留备份

升级完成后写入 `~/.manji/just-upgraded-from` 标记，下次检查时会显示升级成功信息。

## 注意事项

- 版本检查使用 5 秒超时，网络异常时静默跳过，不影响原 skill 执行
- 仅检查 GitHub main 分支的 VERSION 文件，不做完整下载
- 所有用户交互通过 AskUserQuestion 进行，不直接执行写操作
