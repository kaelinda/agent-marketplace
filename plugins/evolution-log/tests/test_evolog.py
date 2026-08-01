#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Evolution Log 自测 — stdlib unittest,无网络、无第三方依赖。

覆盖三个脚本:evolog-check(Stop hook 判定)、evolog-index(索引重建)、
evolog-init(项目初始化)。check 走子进程,顺便验证真实的 exit code 语义。
"""
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

SCRIPTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, "scripts")
SCRIPTS = os.path.normpath(SCRIPTS)
CHECK = os.path.join(SCRIPTS, "evolog-check.py")
INIT = os.path.join(SCRIPTS, "evolog-init.py")


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


evolog_index = load("evolog_index", os.path.join(SCRIPTS, "evolog-index.py"))
evolog_check = load("evolog_check", CHECK)


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def read_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def run_check(payload, cwd, env=None):
    e = dict(os.environ)
    e.pop("EVOLOG_DIR", None)
    e.pop("CLAUDE_PLUGIN_ROOT", None)
    e.update(env or {})
    p = subprocess.run([sys.executable, CHECK], input=json.dumps(payload),
                       capture_output=True, text=True, cwd=cwd, env=e)
    return p.returncode, p.stderr


def run_init(args, cwd):
    e = dict(os.environ)
    e.pop("EVOLOG_DIR", None)
    p = subprocess.run([sys.executable, INIT] + args, capture_output=True,
                       text=True, cwd=cwd, env=e)
    return p.returncode, p.stdout + p.stderr


class TempProject(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="evolog-test-")
        self.addCleanup(shutil.rmtree, self.dir, True)

    def path(self, *parts):
        return os.path.join(self.dir, *parts)

    def enable(self, **cfg):
        """写入配置 = 项目已 opt-in。"""
        os.makedirs(self.path(".claude"), exist_ok=True)
        with open(self.path(".claude", "evolution-log.json"), "w", encoding="utf-8") as f:
            json.dump(cfg, f)

    def transcript(self, text):
        p = self.path("transcript.jsonl")
        with open(p, "w", encoding="utf-8") as f:
            f.write(text)
        return p


# --------------------------------------------------------------------------- check

class TestCheckGate(TempProject):
    def test_未初始化的项目直接放行(self):
        code, _ = run_check(
            {"cwd": self.dir, "transcript_path": self.transcript("我们把认证重构了")}, self.dir)
        self.assertEqual(code, 0)

    def test_初始化后命中关键词才阻断(self):
        self.enable()
        code, err = run_check(
            {"cwd": self.dir, "session_id": "s1",
             "transcript_path": self.transcript("我们把认证方案重构了")}, self.dir)
        self.assertEqual(code, 2)
        self.assertIn("[evolution-log hook]", err)

    def test_未命中关键词放行(self):
        self.enable()
        code, _ = run_check(
            {"cwd": self.dir, "session_id": "s1",
             "transcript_path": self.transcript("修了一个空指针,加了单测")}, self.dir)
        self.assertEqual(code, 0)

    def test_stop_hook_active_防循环(self):
        self.enable()
        code, _ = run_check(
            {"cwd": self.dir, "session_id": "s1", "stop_hook_active": True,
             "transcript_path": self.transcript("重构")}, self.dir)
        self.assertEqual(code, 0)

    def test_单会话只阻断一次(self):
        self.enable()
        t = self.transcript("这次是架构迁移")
        first, _ = run_check({"cwd": self.dir, "session_id": "s1", "transcript_path": t}, self.dir)
        second, _ = run_check({"cwd": self.dir, "session_id": "s1", "transcript_path": t}, self.dir)
        third, _ = run_check({"cwd": self.dir, "session_id": "s2", "transcript_path": t}, self.dir)
        self.assertEqual((first, second, third), (2, 0, 2))

    def test_auto_hook_false_关闭兜底(self):
        self.enable(auto_hook=False)
        code, _ = run_check(
            {"cwd": self.dir, "session_id": "s1",
             "transcript_path": self.transcript("重构")}, self.dir)
        self.assertEqual(code, 0)

    def test_EVOLOG_DIR_也算已启用(self):
        code, _ = run_check(
            {"cwd": self.dir, "session_id": "s1",
             "transcript_path": self.transcript("migrate to v2")}, self.dir,
            env={"EVOLOG_DIR": self.path("kb")})
        self.assertEqual(code, 2)

    def test_项目自带副本时插件让位(self):
        self.enable()
        os.makedirs(self.path(".claude", "hooks"))
        open(self.path(".claude", "hooks", "evolog-check.py"), "w").close()
        code, _ = run_check(
            {"cwd": self.dir, "session_id": "s1",
             "transcript_path": self.transcript("重构")}, self.dir,
            env={"CLAUDE_PLUGIN_ROOT": SCRIPTS})
        self.assertEqual(code, 0)

    def test_坏配置不影响放行判定(self):
        os.makedirs(self.path(".claude"))
        with open(self.path(".claude", "evolution-log.json"), "w") as f:
            f.write("{ not json")
        code, _ = run_check(
            {"cwd": self.dir, "session_id": "s1",
             "transcript_path": self.transcript("重构")}, self.dir)
        self.assertEqual(code, 2)          # 配置损坏 → 按默认值走,不报错

    def test_坏输入_fail_open(self):
        p = subprocess.run([sys.executable, CHECK], input="not json at all",
                           capture_output=True, text=True, cwd=self.dir)
        self.assertEqual(p.returncode, 0)

    def test_transcript_缺失或为符号链接时放行(self):
        self.enable()
        link = self.path("link.jsonl")
        os.symlink(self.transcript("重构"), link)
        self.assertEqual(run_check({"cwd": self.dir, "session_id": "a",
                                    "transcript_path": link}, self.dir)[0], 0)
        self.assertEqual(run_check({"cwd": self.dir, "session_id": "b",
                                    "transcript_path": self.path("nope")}, self.dir)[0], 0)


class TestCheckScreen(unittest.TestCase):
    def test_敏感路径命中(self):
        cfg = {"keywords": [], "sensitive_paths": ["src/core/"]}
        self.assertTrue(evolog_check.fast_screen("edited src/core/auth.py", cfg))

    def test_英文关键词大小写不敏感(self):
        cfg = {"keywords": ["migrate"], "sensitive_paths": []}
        self.assertTrue(evolog_check.fast_screen("We MIGRATEd the DB", cfg))

    def test_空文本不命中(self):
        self.assertFalse(evolog_check.fast_screen("", {"keywords": ["x"], "sensitive_paths": []}))

    def test_extra_keywords_叠加而非覆盖(self):
        d = tempfile.mkdtemp(prefix="evolog-cfg-")
        self.addCleanup(shutil.rmtree, d, True)
        os.makedirs(os.path.join(d, ".claude"))
        with open(os.path.join(d, ".claude", "evolution-log.json"), "w", encoding="utf-8") as f:
            json.dump({"extra_keywords": ["灰度"]}, f)
        cfg = evolog_check.load_config(d)
        self.assertIn("灰度", cfg["keywords"])
        self.assertIn("迁移", cfg["keywords"])


# --------------------------------------------------------------------------- index

RECORD = """---
id: 2026-08-01-jwt-to-oauth2
date: 2026-08-01
type: solution_change        # 行内注释应被忽略
title: 认证方案迁移
from: 自签 JWT
to: OAuth2
owner: 张三
status: confirmed
tags: [auth, security]
---

## 背景
"""


class TestIndex(TempProject):
    def records(self, name, text):
        d = self.path("docs", "evolution", "records")
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, name), "w", encoding="utf-8") as f:
            f.write(text)

    def test_frontmatter_解析(self):
        self.records("a.md", RECORD)
        meta = evolog_index.parse_frontmatter(self.path("docs", "evolution", "records", "a.md"))
        self.assertEqual(meta["owner"], "张三")
        self.assertEqual(meta["type"], "solution_change")
        self.assertEqual(meta["tags"], ["auth", "security"])

    def test_无闭合分隔符视为无效(self):
        self.records("bad.md", "---\ndate: 2026-01-01\n还没闭合")
        self.assertIsNone(
            evolog_index.parse_frontmatter(self.path("docs", "evolution", "records", "bad.md")))

    def test_collect_按日期倒序并跳过无效记录(self):
        self.records("old.md", RECORD.replace("2026-08-01", "2025-01-01"))
        self.records("new.md", RECORD)
        self.records("broken.md", "没有 frontmatter")
        self.records("_draft.md", RECORD)       # 下划线开头应被忽略
        items, skipped = evolog_index.collect(self.path("docs", "evolution"))
        self.assertEqual([i["_file"] for i in items], ["new.md", "old.md"])
        self.assertEqual(len(skipped), 1)

    def test_重建幂等且生成两份索引(self):
        self.records("a.md", RECORD)
        for _ in range(2):
            sys.argv = ["evolog-index.py", "--project-dir", self.dir]
            self.assertEqual(evolog_index.main(), 0)
        index = read(self.path("docs", "evolution", "INDEX.md"))
        self.assertIn("自签 JWT → OAuth2", index)
        self.assertIn("✅", index)
        cached = read_json(self.path("docs", "evolution", ".cache", "records.json"))
        self.assertEqual(cached[0]["owner"], "张三")
        self.assertNotIn("_file", cached[0])    # 内部字段不外泄

    def test_空目录也能生成占位索引(self):
        sys.argv = ["evolog-index.py", "--project-dir", self.dir]
        evolog_index.main()
        self.assertIn("(暂无记录)",
                      read(self.path("docs", "evolution", "INDEX.md")))

    def test_表格中的竖线被转义(self):
        self.records("a.md", RECORD.replace("to: OAuth2", "to: A|B"))
        items, _ = evolog_index.collect(self.path("docs", "evolution"))
        self.assertIn("\\|", evolog_index.build_index_md(items))

    def test_存储位置优先级(self):
        os.makedirs(self.path(".claude"))
        with open(self.path(".claude", "evolution-log.json"), "w", encoding="utf-8") as f:
            json.dump({"storage_dir": "custom/evo"}, f)
        self.assertEqual(evolog_index.resolve_storage_dir(self.dir), self.path("custom", "evo"))
        os.environ["EVOLOG_DIR"] = self.path("kb")
        try:
            self.assertEqual(evolog_index.resolve_storage_dir(self.dir), self.path("kb"))
        finally:
            del os.environ["EVOLOG_DIR"]

    def test_持有锁时跳过重建(self):
        cache = self.path("docs", "evolution", ".cache")
        os.makedirs(os.path.join(cache, "index.lock"))
        sys.argv = ["evolog-index.py", "--project-dir", self.dir]
        self.assertEqual(evolog_index.main(), 0)
        self.assertFalse(os.path.exists(self.path("docs", "evolution", "INDEX.md")))


# --------------------------------------------------------------------------- init

class TestInit(TempProject):
    def test_dry_run_不写任何文件(self):
        code, out = run_init(["--project-dir", self.dir, "--dry-run"], self.dir)
        self.assertEqual(code, 0)
        self.assertIn("预演", out)
        self.assertEqual(os.listdir(self.dir), [])

    def test_默认初始化产出完整骨架(self):
        code, _ = run_init(["--project-dir", self.dir], self.dir)
        self.assertEqual(code, 0)
        for rel in [(".claude", "evolution-log.json"),
                    (".claude", "hooks", "evolog-index.py"),
                    ("docs", "evolution", "INDEX.md"),
                    ("docs", "evolution", "records", ".gitkeep"),
                    ("docs", "evolution", ".cache", "records.json"),
                    (".gitattributes",), (".gitignore",)]:
            self.assertTrue(os.path.exists(self.path(*rel)), rel)
        # 插件模式不把 check 脚本塞进项目
        self.assertFalse(os.path.exists(self.path(".claude", "hooks", "evolog-check.py")))

    def test_重复执行幂等_不追加重复行(self):
        run_init(["--project-dir", self.dir], self.dir)
        before = read(self.path(".gitattributes"))
        code, out = run_init(["--project-dir", self.dir], self.dir)
        self.assertEqual(code, 0)
        self.assertIn("跳过", out)
        self.assertEqual(before, read(self.path(".gitattributes")))

    def test_不覆盖已有配置(self):
        os.makedirs(self.path(".claude"))
        with open(self.path(".claude", "evolution-log.json"), "w", encoding="utf-8") as f:
            json.dump({"storage_dir": "docs/evo", "llm_gate": False}, f)
        run_init(["--project-dir", self.dir], self.dir)
        cfg = read_json(self.path(".claude", "evolution-log.json"))
        self.assertEqual(cfg["storage_dir"], "docs/evo")
        self.assertFalse(cfg["llm_gate"])
        self.assertTrue(os.path.isdir(self.path("docs", "evo", "records")))  # 沿用既有配置

    def test_standalone_合并进已有_settings(self):
        os.makedirs(self.path(".claude"))
        with open(self.path(".claude", "settings.json"), "w", encoding="utf-8") as f:
            json.dump({"permissions": {"allow": ["Bash"]},
                       "hooks": {"Stop": [{"hooks": [{"type": "command",
                                                      "command": "echo hi"}]}]}}, f)
        run_init(["--project-dir", self.dir, "--standalone"], self.dir)
        data = read_json(self.path(".claude", "settings.json"))
        self.assertEqual(data["permissions"]["allow"], ["Bash"])       # 原配置保留
        self.assertEqual(len(data["hooks"]["Stop"]), 2)                # 追加而非覆盖
        self.assertTrue(os.path.exists(self.path(".claude", "hooks", "evolog-check.py")))
        # 再跑一次不应重复注册
        run_init(["--project-dir", self.dir, "--standalone"], self.dir)
        data = read_json(self.path(".claude", "settings.json"))
        self.assertEqual(len(data["hooks"]["Stop"]), 2)

    def test_codex_写入注册文件(self):
        run_init(["--project-dir", self.dir, "--codex"], self.dir)
        data = read_json(self.path(".codex", "hooks.json"))
        self.assertIn("evolog-check.py", json.dumps(data))

    def test_自定义存储目录写进配置与_gitattributes(self):
        run_init(["--project-dir", self.dir, "--storage-dir", "docs/history"], self.dir)
        cfg = read_json(self.path(".claude", "evolution-log.json"))
        self.assertEqual(cfg["storage_dir"], "docs/history")
        self.assertIn("docs/history/INDEX.md merge=ours",
                      read(self.path(".gitattributes")))

    def test_仓库外存储跳过_git_约定(self):
        out_dir = os.path.join(self.dir, "outside")
        code, out = run_init(["--project-dir", self.dir, "--storage-dir", out_dir], self.dir)
        self.assertEqual(code, 0)
        self.assertFalse(os.path.exists(self.path(".gitattributes")))
        self.assertIn("仓库外", out)

    def test_非_git_仓库不装_post_merge(self):
        code, out = run_init(["--project-dir", self.dir], self.dir)
        self.assertEqual(code, 0)
        self.assertIn("非 git 仓库", out)

    def test_git_仓库安装_post_merge_且不覆盖已有(self):
        subprocess.run(["git", "init", "-q", self.dir], check=True, capture_output=True)
        run_init(["--project-dir", self.dir], self.dir)
        hook = self.path(".git", "hooks", "post-merge")
        self.assertTrue(os.path.exists(hook))
        self.assertTrue(os.access(hook, os.X_OK))
        with open(hook, "w", encoding="utf-8") as f:
            f.write("#!/bin/sh\necho custom\n")
        run_init(["--project-dir", self.dir], self.dir)
        self.assertIn("custom", read(hook))

    def test_初始化后_check_立即生效(self):
        run_init(["--project-dir", self.dir], self.dir)
        code, _ = run_check({"cwd": self.dir, "session_id": "s1",
                             "transcript_path": self.transcript("我们决定重构掉旧模块")}, self.dir)
        self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
