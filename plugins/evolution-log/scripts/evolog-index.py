#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Evolution Log — 索引重建脚本(幂等)
从 records/*.md 的 frontmatter 全量重建 INDEX.md 与 .cache/records.json。
records/ 是唯一事实来源;本脚本可在任何时刻重跑,结果一致。

存储位置解析优先级:
  EVOLOG_DIR 环境变量 > .claude/evolution-log.json 的 storage_dir > docs/evolution
并发:mkdir 原子锁,拿不到锁直接跳过(重建幂等,由后到者覆盖即可)。
仅依赖 Python 3 标准库(frontmatter 用内置极简解析器,不依赖 PyYAML)。

用法:python3 evolog-index.py [--project-dir <path>]
"""
import json
import os
import re
import sys
import time

TYPE_LABELS = {
    "solution_change": "方案变更",
    "requirement_change": "需求变更",
    "migration": "架构迁移",
    "decision": "决策",
}
STATUS_ICONS = {"confirmed": "✅", "draft": "📝", "superseded": "🗄️"}
LOCK_STALE_SECONDS = 60


def resolve_storage_dir(project_dir):
    env = os.environ.get("EVOLOG_DIR", "").strip()
    if env:
        raw = env
    else:
        raw = "docs/evolution"
        cfg_path = os.path.join(project_dir, ".claude", "evolution-log.json")
        try:
            if os.path.isfile(cfg_path):
                with open(cfg_path, "r", encoding="utf-8") as f:
                    raw = json.load(f).get("storage_dir", raw) or raw
        except Exception:
            pass
    raw = os.path.expanduser(raw)
    if not os.path.isabs(raw):
        raw = os.path.join(project_dir, raw)
    return os.path.normpath(raw)


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


def collect(storage_dir):
    records_dir = os.path.join(storage_dir, "records")
    items, skipped = [], []
    if not os.path.isdir(records_dir):
        return items, skipped
    for name in sorted(os.listdir(records_dir)):
        if not name.endswith(".md") or name.startswith("_"):
            continue
        path = os.path.join(records_dir, name)
        try:
            meta = parse_frontmatter(path)
        except Exception as e:
            skipped.append("%s (读取失败: %r)" % (name, e))
            continue
        if not meta or not meta.get("date"):
            skipped.append("%s (frontmatter 缺失或无 date)" % name)
            continue
        meta.setdefault("id", name[:-3])
        meta["_file"] = name
        items.append(meta)
    items.sort(key=lambda m: (m.get("date", ""), m.get("id", "")), reverse=True)
    return items, skipped


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


def acquire_lock(cache_dir):
    lock = os.path.join(cache_dir, "index.lock")
    try:
        # 清理陈旧锁(持有进程可能已崩溃)
        if os.path.isdir(lock) and time.time() - os.path.getmtime(lock) > LOCK_STALE_SECONDS:
            os.rmdir(lock)
        os.makedirs(cache_dir, exist_ok=True)
        os.mkdir(lock)          # 原子操作
        return lock
    except FileExistsError:
        return None


def main():
    project_dir = os.getcwd()
    if "--project-dir" in sys.argv:
        project_dir = sys.argv[sys.argv.index("--project-dir") + 1]
    storage = resolve_storage_dir(project_dir)
    cache_dir = os.path.join(storage, ".cache")

    lock = acquire_lock(cache_dir)
    if lock is None:
        print("evolog-index: 另一个重建正在进行,跳过(幂等,稍后重跑即可)")
        return 0
    try:
        items, skipped = collect(storage)
        os.makedirs(storage, exist_ok=True)
        with open(os.path.join(storage, "INDEX.md"), "w", encoding="utf-8") as f:
            f.write(build_index_md(items))
        public = [{k: v for k, v in m.items() if not k.startswith("_")} for m in items]
        with open(os.path.join(cache_dir, "records.json"), "w", encoding="utf-8") as f:
            json.dump(public, f, ensure_ascii=False, indent=1)
        print("evolog-index: 重建完成,共 %d 条记录 → %s" % (len(items), storage))
        for s in skipped:
            print("  ⚠ 跳过 %s" % s)
        return 0
    finally:
        try:
            os.rmdir(lock)
        except Exception:
            pass


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception as e:
        sys.stderr.write("evolog-index 失败(不影响记录文件本身): %r\n" % (e,))
        sys.exit(1)
