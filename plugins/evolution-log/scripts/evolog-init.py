#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Evolution Log — 项目初始化(幂等)
在目标项目里落地演进日志系统所需的最小骨架:配置、存储目录、索引、
Git 协作约定(gitattributes / gitignore / post-merge),以及可选的
standalone 模式(不装插件也能用的 Stop hook 注册)。

用法:
  python3 evolog-init.py [--project-dir <path>] [--storage-dir docs/evolution]
                         [--standalone] [--codex] [--force] [--dry-run]

模式:
  默认(插件模式)  Stop hook 由已安装的 evolution-log 插件提供,本脚本只写
                  配置 / 存储 / Git 约定,并把 evolog-index.py 复制到项目
                  .claude/hooks/(git post-merge 在 Claude Code 之外运行,
                  必须有一份项目内副本才能重建索引)。
  --standalone    额外把 evolog-check.py 复制进项目并把 Stop hook 注册进
                  .claude/settings.json —— 适合不装插件、或需要让整个团队
                  clone 后即刻生效的场景。
  --codex         额外写入 .codex/hooks.json(与 Claude 共用同一脚本)。

安全约定:不覆盖任何已存在的文件(除非 --force);所有写操作在结束时逐条打印。
仅依赖 Python 3 标准库。
"""
import argparse
import json
import os
import shutil
import stat
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

DEFAULT_CONFIG = {
    "storage_dir": "docs/evolution",
    "sensitive_paths": [],
    "extra_keywords": [],
    "llm_gate": True,
    "auto_hook": True,
}

GITATTRIBUTES_LINES = [
    "# Evolution Log: INDEX.md 是全量生成物,合并冲突时任选一边,合并后自动重建",
    "{storage}/INDEX.md merge=ours",
]

POST_MERGE = """#!/usr/bin/env bash
# Evolution Log: 合并后重建 INDEX(幂等,失败不阻塞)
root="$(git rev-parse --show-toplevel)"
python3 "$root/.claude/hooks/evolog-index.py" --project-dir "$root" || true
"""

EMPTY_INDEX = """# 项目演进时间线

> 本文件由 evolog-index.py 自动全量生成,请勿手工编辑;冲突时任选一边,合并后重跑脚本即可恢复。

| 日期 | 类型 | 变更 | 牵头人 | 状态 | 记录 |
|---|---|---|---|---|---|
| — | — | (暂无记录) | — | — | — |
"""

CODEX_HOOKS = {
    "hooks": {
        "Stop": [
            {"hooks": [{"type": "command",
                        "command": "python3 .claude/hooks/evolog-check.py"}]}
        ]
    }
}


class Report(object):
    def __init__(self, dry_run):
        self.dry_run = dry_run
        self.done = []
        self.skipped = []

    def did(self, msg):
        self.done.append(msg)

    def skip(self, msg):
        self.skipped.append(msg)

    def render(self):
        head = "evolog-init: 预演(--dry-run,未写入任何文件)" if self.dry_run else "evolog-init: 初始化完成"
        out = [head, ""]
        if self.done:
            out.append("已处理:")
            out += ["  ✓ %s" % m for m in self.done]
        if self.skipped:
            out.append("跳过(已存在或不适用,未改动):")
            out += ["  · %s" % m for m in self.skipped]
        return "\n".join(out)


def write_file(path, content, rep, label, force=False, mode=None):
    if os.path.exists(path) and not force:
        rep.skip("%s(%s)" % (label, path))
        return False
    if not rep.dry_run:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        if mode is not None:
            os.chmod(path, mode)
    rep.did("%s(%s)" % (label, path))
    return True


def append_lines(path, lines, rep, label):
    """幂等追加:逐行判断,已存在的行不重复写。"""
    existing = ""
    if os.path.isfile(path):
        with open(path, "r", encoding="utf-8") as f:
            existing = f.read()
    missing = [ln for ln in lines if ln.strip() and ln not in existing.splitlines()]
    if not missing:
        rep.skip("%s(%s,内容已存在)" % (label, path))
        return False
    if not rep.dry_run:
        prefix = "" if (not existing or existing.endswith("\n")) else "\n"
        with open(path, "a", encoding="utf-8") as f:
            f.write(prefix + "\n".join(missing) + "\n")
    rep.did("%s(%s,追加 %d 行)" % (label, path, len(missing)))
    return True


def copy_script(name, project_dir, rep, force):
    src = os.path.join(SCRIPT_DIR, name)
    dst = os.path.join(project_dir, ".claude", "hooks", name)
    if os.path.exists(dst) and not force:
        rep.skip("复制 %s(%s)" % (name, dst))
        return
    if not rep.dry_run:
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copyfile(src, dst)
        os.chmod(dst, 0o755)
    rep.did("复制 %s → %s" % (name, dst))


def register_claude_settings(project_dir, rep, force):
    """把 Stop hook 合并进 .claude/settings.json,保留其他配置。"""
    path = os.path.join(project_dir, ".claude", "settings.json")
    entry = {
        "hooks": [{"type": "command",
                   "command": "python3 \"$CLAUDE_PROJECT_DIR/.claude/hooks/evolog-check.py\"",
                   "timeout": 10}]
    }
    data = {}
    if os.path.isfile(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            rep.skip("注册 Stop hook(%s 解析失败:%r,请手工合并)" % (path, e))
            return
    stop = data.setdefault("hooks", {}).setdefault("Stop", [])
    if any("evolog-check" in json.dumps(item, ensure_ascii=False) for item in stop):
        rep.skip("注册 Stop hook(%s,已注册)" % path)
        return
    stop.append(entry)
    if not rep.dry_run:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write("\n")
    rep.did("注册 Stop hook → %s" % path)


def install_post_merge(project_dir, rep, force):
    git_dir = os.path.join(project_dir, ".git")
    if not os.path.exists(git_dir):
        rep.skip("安装 post-merge(非 git 仓库)")
        return
    # 支持 worktree / submodule:.git 可能是指向真实 gitdir 的文件
    if os.path.isfile(git_dir):
        try:
            with open(git_dir, "r", encoding="utf-8") as f:
                line = f.read().strip()
            if line.startswith("gitdir:"):
                git_dir = os.path.normpath(
                    os.path.join(project_dir, line.split(":", 1)[1].strip()))
        except Exception as e:
            rep.skip("安装 post-merge(解析 .git 失败:%r)" % (e,))
            return
    hook = os.path.join(git_dir, "hooks", "post-merge")
    if os.path.exists(hook) and not force:
        rep.skip("安装 post-merge(%s 已存在,请手工合并重建索引那一行)" % hook)
        return
    write_file(hook, POST_MERGE, rep, "安装 post-merge", force=True,
               mode=stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)


def main():
    ap = argparse.ArgumentParser(description="Evolution Log 项目初始化(幂等)")
    ap.add_argument("--project-dir", default=os.getcwd())
    ap.add_argument("--storage-dir", default=None,
                    help="演进日志存储目录,默认 docs/evolution;支持仓库外绝对路径")
    ap.add_argument("--standalone", action="store_true",
                    help="不依赖插件:把 check 脚本复制进项目并注册 .claude/settings.json")
    ap.add_argument("--codex", action="store_true", help="额外写入 .codex/hooks.json")
    ap.add_argument("--force", action="store_true", help="覆盖已存在的文件")
    ap.add_argument("--dry-run", action="store_true", help="只打印将要做什么,不写入")
    args = ap.parse_args()

    project_dir = os.path.abspath(os.path.expanduser(args.project_dir))
    if not os.path.isdir(project_dir):
        sys.stderr.write("evolog-init: 项目目录不存在 %s\n" % project_dir)
        return 1
    rep = Report(args.dry_run)

    # ① 配置文件(已存在则读出其中的 storage_dir,保证后续步骤与现状一致)
    cfg_path = os.path.join(project_dir, ".claude", "evolution-log.json")
    cfg = dict(DEFAULT_CONFIG)
    if os.path.isfile(cfg_path) and not args.force:
        try:
            with open(cfg_path, "r", encoding="utf-8") as f:
                cfg.update(json.load(f))
        except Exception as e:
            rep.skip("读取既有配置失败(%r),按默认值继续" % (e,))
    if args.storage_dir:
        cfg["storage_dir"] = args.storage_dir
    write_file(cfg_path, json.dumps(cfg, ensure_ascii=False, indent=2) + "\n",
               rep, "写入配置", force=args.force)

    # ② 存储骨架
    raw = os.path.expanduser(cfg["storage_dir"])
    storage = raw if os.path.isabs(raw) else os.path.join(project_dir, raw)
    storage = os.path.normpath(storage)
    in_repo = not os.path.isabs(raw)
    if not args.dry_run:
        os.makedirs(os.path.join(storage, "records"), exist_ok=True)
        os.makedirs(os.path.join(storage, ".cache"), exist_ok=True)
    rep.did("创建存储目录(%s)" % storage)
    write_file(os.path.join(storage, "records", ".gitkeep"), "", rep, "占位 records/.gitkeep")
    write_file(os.path.join(storage, "INDEX.md"), EMPTY_INDEX, rep, "初始化 INDEX.md")
    write_file(os.path.join(storage, ".cache", "records.json"), "[]\n", rep, "初始化 records.json")

    # ③ Git 协作约定(仅当存储在仓库内才有意义)
    if in_repo:
        append_lines(os.path.join(project_dir, ".gitattributes"),
                     [ln.format(storage=raw.rstrip("/")) for ln in GITATTRIBUTES_LINES],
                     rep, "配置 .gitattributes")
        append_lines(os.path.join(project_dir, ".gitignore"),
                     ["# Evolution Log 本地缓存(可随时由脚本重建)",
                      "%s/.cache/" % raw.rstrip("/"),
                      ".claude/cache/"],
                     rep, "配置 .gitignore")
    else:
        rep.skip("Git 协作约定(存储在仓库外:%s,PR 流转与 CI 校验不可用)" % storage)

    # ④ 脚本副本:index 始终需要(git hook 在 Claude Code 之外运行)
    copy_script("evolog-index.py", project_dir, rep, args.force)
    install_post_merge(project_dir, rep, args.force)

    # ⑤ standalone / codex
    if args.standalone:
        copy_script("evolog-check.py", project_dir, rep, args.force)
        register_claude_settings(project_dir, rep, args.force)
    if args.codex:
        copy_script("evolog-check.py", project_dir, rep, args.force)
        write_file(os.path.join(project_dir, ".codex", "hooks.json"),
                   json.dumps(CODEX_HOOKS, ensure_ascii=False, indent=2) + "\n",
                   rep, "写入 Codex hook 注册", force=args.force)

    print(rep.render())
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception as e:
        sys.stderr.write("evolog-init 失败: %r\n" % (e,))
        sys.exit(1)
