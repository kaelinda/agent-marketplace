#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Evolution Log — 索引重建脚本(幂等)
从 records/*.md 的 frontmatter 全量重建 INDEX.md 与 .cache/records.json。
records/ 是唯一事实来源;本脚本可在任何时刻重跑,结果一致。

存储位置解析优先级:
  EVOLOG_DIR 环境变量 > .claude/evolution-log.json 的 storage_dir > docs/evolution

安全约束(本脚本会被 git post-merge 自动调用,合入的仓库内容不可信):
  - 仓库外存储必须由 EVOLOG_DIR 或显式开关启用;仓库内配置单独指定仓库外路径会被拒绝
  - 所有输出路径及其父目录逐级拒绝符号链接,防止被仓库内 symlink 劫持覆盖任意文件
  - 写入一律走「同目录临时文件 + fsync + os.replace」,失败不会留下截断的索引

并发:mkdir 原子锁 + pending 标记,拿不到锁的一方不会让索引长期陈旧。
仅依赖 Python 3 标准库(frontmatter 用内置极简解析器,不依赖 PyYAML)。

用法:python3 evolog-index.py [--project-dir <path>] [--allow-external-storage]
"""
import json
import os
import re
import sys
import time

SCHEMA_VERSION = 1

TYPE_LABELS = {
    "solution_change": "方案变更",
    "requirement_change": "需求变更",
    "migration": "架构迁移",
    "decision": "决策",
}
STATUS_ICONS = {"confirmed": "✅", "draft": "📝", "superseded": "🗄️"}
VALID_STATUS = set(STATUS_ICONS)
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

LOCK_STALE_SECONDS = 60
LOCK_RETRIES = 10
LOCK_RETRY_SLEEP = 0.2


class UnsafePath(Exception):
    """输出路径不可信(符号链接 / 越权到仓库外),拒绝写入。"""


# ------------------------------------------------------------------ 路径与安全

def _norm(path):
    return os.path.normpath(os.path.abspath(path))


def _is_within(child, parent):
    """child 是否位于 parent 之内(按 realpath 比较,兼容 macOS 的 /var → /private/var)。"""
    child = os.path.realpath(child)
    parent = os.path.realpath(parent)
    return child == parent or child.startswith(parent + os.sep)


def external_storage_allowed(argv=None):
    """仓库外存储的显式开关:命令行参数或环境变量,均不受仓库内配置控制。"""
    argv = sys.argv if argv is None else argv
    if "--allow-external-storage" in argv:
        return True
    return os.environ.get("EVOLOG_ALLOW_EXTERNAL_STORAGE", "").strip().lower() in (
        "1", "true", "yes", "on")


def resolve_storage_dir(project_dir, argv=None):
    """解析存储目录。

    仓库外路径只在两种情况下放行:
      1) 由 EVOLOG_DIR 环境变量指定(用户在仓库之外的显式动作)
      2) 显式开关 --allow-external-storage / EVOLOG_ALLOW_EXTERNAL_STORAGE=1
    仅由仓库内 .claude/evolution-log.json 指定的仓库外路径一律拒绝 —— 否则一个被
    合入的恶意配置就能让 post-merge 自动往仓库外写文件。
    """
    project_dir = _norm(project_dir)
    env = os.environ.get("EVOLOG_DIR", "").strip()
    from_env = bool(env)
    if from_env:
        raw = env
    else:
        raw = "docs/evolution"
        cfg_path = os.path.join(project_dir, ".claude", "evolution-log.json")
        try:
            if os.path.isfile(cfg_path):
                with open(cfg_path, "r", encoding="utf-8") as f:
                    value = json.load(f).get("storage_dir")
                if isinstance(value, str) and value.strip():
                    raw = value.strip()
        except Exception:
            pass
    raw = os.path.expanduser(raw)
    if not os.path.isabs(raw):
        raw = os.path.join(project_dir, raw)
    storage = _norm(raw)

    if not _is_within(storage, project_dir) and not from_env \
            and not external_storage_allowed(argv):
        raise UnsafePath(
            "配置把存储目录指到了仓库外(%s)。仓库内配置不能单独决定仓库外写入;"
            "确需如此请设置 EVOLOG_DIR,或显式加 --allow-external-storage "
            "/ EVOLOG_ALLOW_EXTERNAL_STORAGE=1。" % storage)
    return storage


def assert_no_symlink(path, stop_at=None):
    """逐级检查 path 及其祖先目录都不是符号链接。

    stop_at 之上的目录不再检查(项目根之外的路径由用户自己负责)。
    """
    path = _norm(path)
    stop_at = _norm(stop_at) if stop_at else None
    cur = path
    while True:
        if os.path.islink(cur):
            raise UnsafePath("拒绝写入:路径中存在符号链接 %s" % cur)
        if stop_at and cur == stop_at:
            break
        parent = os.path.dirname(cur)
        if parent == cur:
            break
        cur = parent


def safe_makedirs(path, stop_at=None):
    """创建目录,过程中拒绝符号链接。"""
    path = _norm(path)
    if not os.path.isdir(path):
        os.makedirs(path, exist_ok=True)
    assert_no_symlink(path, stop_at=stop_at)


def atomic_write(path, content, stop_at=None):
    """原子写入:拒绝 symlink → 同目录临时文件 → fsync → os.replace。

    异常时不会留下截断的目标文件;目标是 symlink 时直接拒绝而不是跟随写入。
    """
    path = _norm(path)
    directory = os.path.dirname(path)
    safe_makedirs(directory, stop_at=stop_at)
    if os.path.lexists(path):
        if os.path.islink(path):
            raise UnsafePath("拒绝写入:目标是符号链接 %s" % path)
        if not os.path.isfile(path):
            raise UnsafePath("拒绝写入:目标不是常规文件 %s" % path)
    tmp = os.path.join(directory, ".%s.tmp-%d" % (os.path.basename(path), os.getpid()))
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            try:
                os.remove(tmp)
            except OSError:
                pass


# ------------------------------------------------------------------ 记录解析

def parse_frontmatter(path):
    """极简 frontmatter 解析:支持 `key: value` 与 `key: [a, b]` 两种形式。"""
    with open(path, "r", encoding="utf-8") as f:
        lines = f.read().splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    meta = {}
    for line in lines[1:]:
        if line.strip() == "---":
            return meta
        line = line.split("  #", 1)[0]           # 去掉行内注释
        m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*:\s*(.*)$", line)
        if not m:
            continue
        key, val = m.group(1), m.group(2).strip()
        if val.startswith("[") and val.endswith("]"):
            inner = val[1:-1].strip()
            meta[key] = [x.strip().strip("'\"") for x in inner.split(",") if x.strip()]
        else:
            meta[key] = val.strip("'\"")
    return None  # 没有闭合的 --- 视为无效


def validate(meta, name):
    """校验单条记录的 frontmatter,返回 (是否可入索引, 问题描述列表)。

    date 非法即拒绝入索引(排序依赖它);其余字段只警告不阻断 —— 记录文件本身才是
    事实来源,索引不该因为一个拼错的 type 就整体失败。
    """
    problems, fatal = [], False
    date = meta.get("date")
    if not isinstance(date, str) or not DATE_RE.match(date):
        problems.append("date 非法(需 YYYY-MM-DD,实际 %r)" % (date,))
        fatal = True
    rtype = meta.get("type")
    if rtype is not None and rtype not in TYPE_LABELS:
        problems.append("type 未知(%r,可选 %s)" % (rtype, "/".join(sorted(TYPE_LABELS))))
    status = meta.get("status")
    if status is not None and status not in VALID_STATUS:
        problems.append("status 未知(%r,可选 %s)" % (status, "/".join(sorted(VALID_STATUS))))
    for key in ("supersedes", "related", "tags", "participants", "commits"):
        if key in meta and not isinstance(meta[key], list):
            problems.append("%s 应为列表(如 [a, b]),实际 %r" % (key, meta[key]))
    return (not fatal), ["%s: %s" % (name, p) for p in problems]


def collect(storage_dir):
    records_dir = os.path.join(storage_dir, "records")
    items, warnings = [], []
    if not os.path.isdir(records_dir):
        return items, warnings
    seen_ids = {}
    for name in sorted(os.listdir(records_dir)):
        if not name.endswith(".md") or name.startswith("_"):
            continue
        path = os.path.join(records_dir, name)
        try:
            meta = parse_frontmatter(path)
        except Exception as e:
            warnings.append("%s (读取失败: %r)" % (name, e))
            continue
        if not meta:
            warnings.append("%s (frontmatter 缺失或未闭合)" % name)
            continue
        ok, problems = validate(meta, name)
        warnings.extend(problems)
        if not ok:
            continue
        meta.setdefault("id", name[:-3])
        rid = meta["id"]
        if rid in seen_ids:
            warnings.append("%s: id 与 %s 重复(两条都已入索引,建议改掉其中一条)"
                            % (name, seen_ids[rid]))
        else:
            seen_ids[rid] = name
        meta["_file"] = name
        items.append(meta)
    items.sort(key=lambda m: (m.get("date", ""), m.get("id", "")), reverse=True)
    return items, warnings


def build_index_md(items):
    out = [
        "# 项目演进时间线",
        "",
        "> 本文件由 evolog-index.py 自动全量生成,请勿手工编辑;"
        "冲突时任选一边,合并后重跑脚本即可恢复。",
        "",
        "| 日期 | 类型 | 变更 | 牵头人 | 状态 | 记录 |",
        "|---|---|---|---|---|---|",
    ]
    for m in items:
        change = "%s → %s" % (m.get("from", "?"), m.get("to", "?"))
        row = "| %s | %s | %s | %s | %s | [详情](records/%s) |" % (
            m.get("date", ""),
            TYPE_LABELS.get(m.get("type", ""), m.get("type", "?")),
            change.replace("|", "\\|"),
            m.get("owner", "?"),
            STATUS_ICONS.get(m.get("status", ""), m.get("status", "?")),
            m["_file"],
        )
        out.append(row)
    if not items:
        out.append("| — | — | (暂无记录) | — | — | — |")
    out.append("")
    return "\n".join(out)


# ------------------------------------------------------------------ 并发控制

def acquire_lock(cache_dir, retries=None, sleep=None):
    """mkdir 原子锁,带重试。拿不到返回 None。"""
    retries = LOCK_RETRIES if retries is None else retries
    sleep = LOCK_RETRY_SLEEP if sleep is None else sleep
    lock = os.path.join(cache_dir, "index.lock")
    for attempt in range(max(1, retries)):
        try:
            # 清理陈旧锁(持有进程可能已崩溃)
            if os.path.isdir(lock) and time.time() - os.path.getmtime(lock) > LOCK_STALE_SECONDS:
                os.rmdir(lock)
            os.makedirs(cache_dir, exist_ok=True)
            os.mkdir(lock)          # 原子操作
            return lock
        except FileExistsError:
            if attempt < retries - 1:
                time.sleep(sleep)
        except OSError:
            return None
    return None


def _pending_path(cache_dir):
    return os.path.join(cache_dir, "rebuild.pending")


def mark_pending(cache_dir):
    """拿不到锁时留下「还有一次重建没做」的标记,由持锁方收尾,避免索引长期陈旧。"""
    try:
        os.makedirs(cache_dir, exist_ok=True)
        with open(_pending_path(cache_dir), "w", encoding="utf-8") as f:
            f.write(str(int(time.time())))
    except OSError:
        pass


def take_pending(cache_dir):
    """消费 pending 标记:存在则删除并返回 True。"""
    path = _pending_path(cache_dir)
    if os.path.exists(path):
        try:
            os.remove(path)
        except OSError:
            pass
        return True
    return False


# ------------------------------------------------------------------ 主流程

def rebuild(storage, cache_dir, project_dir):
    """执行一次全量重建,返回 (记录数, 警告列表)。"""
    items, warnings = collect(storage)
    stop_at = project_dir if _is_within(storage, project_dir) else None
    safe_makedirs(storage, stop_at=stop_at)
    atomic_write(os.path.join(storage, "INDEX.md"), build_index_md(items), stop_at=stop_at)
    public = [{k: v for k, v in m.items() if not k.startswith("_")} for m in items]
    payload = {"schema_version": SCHEMA_VERSION, "generated_by": "evolog-index.py",
               "count": len(public), "records": public}
    atomic_write(os.path.join(cache_dir, "records.json"),
                 json.dumps(payload, ensure_ascii=False, indent=1) + "\n", stop_at=stop_at)
    return len(items), warnings


def main():
    project_dir = os.getcwd()
    if "--project-dir" in sys.argv:
        project_dir = sys.argv[sys.argv.index("--project-dir") + 1]
    project_dir = _norm(project_dir)
    storage = resolve_storage_dir(project_dir)
    cache_dir = os.path.join(storage, ".cache")

    lock = acquire_lock(cache_dir)
    if lock is None:
        mark_pending(cache_dir)
        print("evolog-index: 另一个重建正在进行,已标记待重建(由持锁方收尾)")
        return 0
    try:
        take_pending(cache_dir)      # 本次重建覆盖此前排队的请求
        count, warnings = rebuild(storage, cache_dir, project_dir)
        if take_pending(cache_dir):  # 重建期间又有人排队 → 再跑一次,消除陈旧窗口
            count, warnings = rebuild(storage, cache_dir, project_dir)
        print("evolog-index: 重建完成,共 %d 条记录 → %s" % (count, storage))
        for w in warnings:
            print("  ⚠ %s" % w)
        return 0
    finally:
        try:
            os.rmdir(lock)
        except OSError:
            pass


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except UnsafePath as e:
        sys.stderr.write("evolog-index 拒绝执行(安全策略): %s\n" % e)
        sys.exit(1)
    except Exception as e:
        sys.stderr.write("evolog-index 失败(不影响记录文件本身): %r\n" % (e,))
        sys.exit(1)
