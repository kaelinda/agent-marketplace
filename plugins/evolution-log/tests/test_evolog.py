#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Evolution Log 自测 — stdlib unittest,无网络、无第三方依赖。

覆盖三个脚本:evolog-check(Stop hook 判定)、evolog-index(索引重建)、
evolog-init(项目初始化),外加插件打包结构的静态校验。
check / init 走子进程,顺便验证真实的 exit code 语义。
"""
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

PLUGIN = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir))
SKILL = os.path.join(PLUGIN, "skills", "evolution-log")
SCRIPTS = os.path.join(SKILL, "scripts")
CHECK = os.path.join(SCRIPTS, "evolog-check.py")
INIT = os.path.join(SCRIPTS, "evolog-init.py")
INDEX = os.path.join(SCRIPTS, "evolog-index.py")


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


evolog_index = load("evolog_index", INDEX)
evolog_check = load("evolog_check", CHECK)
evolog_init = load("evolog_init", INIT)


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def read_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def clean_env(extra=None):
    e = dict(os.environ)
    for k in ("EVOLOG_DIR", "CLAUDE_PLUGIN_ROOT", "EVOLOG_ALLOW_EXTERNAL_STORAGE"):
        e.pop(k, None)
    e.update(extra or {})
    return e


def run_check(payload, cwd, env=None):
    p = subprocess.run([sys.executable, CHECK], input=json.dumps(payload),
                       capture_output=True, text=True, cwd=cwd, env=clean_env(env))
    return p.returncode, p.stderr


def run_init(args, cwd, env=None):
    p = subprocess.run([sys.executable, INIT] + args, capture_output=True,
                       text=True, cwd=cwd, env=clean_env(env))
    return p.returncode, p.stdout + p.stderr


def run_index(args, cwd, env=None):
    p = subprocess.run([sys.executable, INDEX] + args, capture_output=True,
                       text=True, cwd=cwd, env=clean_env(env))
    return p.returncode, p.stdout + p.stderr


class TempProject(unittest.TestCase):
    def setUp(self):
        self.dir = os.path.realpath(tempfile.mkdtemp(prefix="evolog-test-"))
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

    def test_keywords_写成字符串时不退化为逐字符匹配(self):
        """配置类型写错是最常见的运维事故:按字符串迭代会逐字符匹配,几乎每轮误报。"""
        cfg = {"keywords": "迁移", "sensitive_paths": []}
        self.assertFalse(evolog_check.fast_screen("今天只是修了个拼写", cfg))


class TestCheckConfig(TempProject):
    def cfg(self, raw):
        os.makedirs(self.path(".claude"), exist_ok=True)
        with open(self.path(".claude", "evolution-log.json"), "w", encoding="utf-8") as f:
            f.write(raw if isinstance(raw, str) else json.dumps(raw, ensure_ascii=False))
        return evolog_check.load_config(self.dir)

    def test_extra_keywords_叠加而非覆盖(self):
        cfg = self.cfg({"extra_keywords": ["灰度"]})
        self.assertIn("灰度", cfg["keywords"])
        self.assertIn("迁移", cfg["keywords"])

    def test_keywords_类型错误时回落默认值(self):
        cfg = self.cfg({"keywords": "迁移"})
        self.assertEqual(cfg["keywords"], list(evolog_check.DEFAULT_KEYWORDS))

    def test_sensitive_paths_类型错误时回落空列表(self):
        cfg = self.cfg({"sensitive_paths": "src/core/"})
        self.assertEqual(cfg["sensitive_paths"], [])

    def test_列表中的非字符串项被丢弃(self):
        cfg = self.cfg({"keywords": ["迁移", 42, None, ""]})
        self.assertEqual(cfg["keywords"], ["迁移"])

    def test_布尔项类型错误时回落默认值(self):
        cfg = self.cfg({"auto_hook": "false"})
        self.assertTrue(cfg["auto_hook"])

    def test_根节点不是对象时全部回落默认值(self):
        cfg = self.cfg("[1, 2, 3]")
        self.assertEqual(cfg["keywords"], list(evolog_check.DEFAULT_KEYWORDS))
        self.assertTrue(cfg["auto_hook"])

    def test_配置错误写入错误日志(self):
        self.cfg({"keywords": "迁移"})
        log = self.path(".claude", "cache", "evolog", "error.log")
        self.assertTrue(os.path.isfile(log))
        self.assertIn("keywords", read(log))


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


class IndexBase(TempProject):
    def records(self, name, text):
        d = self.path("docs", "evolution", "records")
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, name), "w", encoding="utf-8") as f:
            f.write(text)

    def build(self):
        sys.argv = ["evolog-index.py", "--project-dir", self.dir]
        return evolog_index.main()


class TestIndex(IndexBase):
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
        items, warnings = evolog_index.collect(self.path("docs", "evolution"))
        self.assertEqual([i["_file"] for i in items], ["new.md", "old.md"])
        self.assertEqual(len(warnings), 1)

    def test_重建幂等且生成两份索引(self):
        self.records("a.md", RECORD)
        for _ in range(2):
            self.assertEqual(self.build(), 0)
        index = read(self.path("docs", "evolution", "INDEX.md"))
        self.assertIn("自签 JWT → OAuth2", index)
        self.assertIn("✅", index)
        cached = read_json(self.path("docs", "evolution", ".cache", "records.json"))
        self.assertEqual(cached["schema_version"], evolog_index.SCHEMA_VERSION)
        self.assertEqual(cached["count"], 1)
        self.assertEqual(cached["records"][0]["owner"], "张三")
        self.assertNotIn("_file", cached["records"][0])    # 内部字段不外泄

    def test_空目录也能生成占位索引(self):
        self.build()
        self.assertIn("(暂无记录)", read(self.path("docs", "evolution", "INDEX.md")))

    def test_表格中的竖线被转义(self):
        self.records("a.md", RECORD.replace("to: OAuth2", "to: A|B"))
        items, _ = evolog_index.collect(self.path("docs", "evolution"))
        self.assertIn("\\|", evolog_index.build_index_md(items))

    def test_不留临时文件(self):
        self.records("a.md", RECORD)
        self.build()
        leftovers = [n for n in os.listdir(self.path("docs", "evolution")) if ".tmp-" in n]
        self.assertEqual(leftovers, [])


class TestIndexValidation(IndexBase):
    def test_日期格式非法的记录被拒绝入索引(self):
        self.records("bad-date.md", RECORD.replace("date: 2026-08-01", "date: 2026/08/01"))
        items, warnings = evolog_index.collect(self.path("docs", "evolution"))
        self.assertEqual(items, [])
        self.assertTrue(any("date 非法" in w for w in warnings))

    def test_未知_type_只告警不丢记录(self):
        self.records("a.md", RECORD.replace("type: solution_change", "type: whatever"))
        items, warnings = evolog_index.collect(self.path("docs", "evolution"))
        self.assertEqual(len(items), 1)
        self.assertTrue(any("type 未知" in w for w in warnings))

    def test_未知_status_只告警不丢记录(self):
        self.records("a.md", RECORD.replace("status: confirmed", "status: done"))
        items, warnings = evolog_index.collect(self.path("docs", "evolution"))
        self.assertEqual(len(items), 1)
        self.assertTrue(any("status 未知" in w for w in warnings))

    def test_id_重复被告警(self):
        self.records("a.md", RECORD)
        self.records("b.md", RECORD)            # 同一个 id
        items, warnings = evolog_index.collect(self.path("docs", "evolution"))
        self.assertEqual(len(items), 2)
        self.assertTrue(any("id 与" in w for w in warnings))

    def test_关系字段写成标量被告警(self):
        self.records("a.md", RECORD.replace("tags: [auth, security]", "tags: auth"))
        _, warnings = evolog_index.collect(self.path("docs", "evolution"))
        self.assertTrue(any("tags 应为列表" in w for w in warnings))


class TestIndexSecurity(IndexBase):
    def victim(self):
        p = self.path("victim.txt")
        with open(p, "w", encoding="utf-8") as f:
            f.write("PRECIOUS")
        return p

    def test_INDEX_是符号链接时拒绝写入(self):
        """核心攻防:仓库里合入一个指向任意文件的 symlink,post-merge 不能跟随它写。"""
        victim = self.victim()
        os.makedirs(self.path("docs", "evolution"))
        os.symlink(victim, self.path("docs", "evolution", "INDEX.md"))
        self.records("a.md", RECORD)
        code, out = run_index(["--project-dir", self.dir], self.dir)
        self.assertEqual(code, 1)
        self.assertIn("符号链接", out)
        self.assertEqual(read(victim), "PRECIOUS")

    def test_records_json_是符号链接时拒绝写入(self):
        victim = self.victim()
        os.makedirs(self.path("docs", "evolution", ".cache"))
        os.symlink(victim, self.path("docs", "evolution", ".cache", "records.json"))
        code, out = run_index(["--project-dir", self.dir], self.dir)
        self.assertEqual(code, 1)
        self.assertEqual(read(victim), "PRECIOUS")

    def test_父目录是符号链接时拒绝写入(self):
        outside = os.path.realpath(tempfile.mkdtemp(prefix="evolog-outside-"))
        self.addCleanup(shutil.rmtree, outside, True)
        os.makedirs(self.path("docs"))
        os.symlink(outside, self.path("docs", "evolution"))
        code, out = run_index(["--project-dir", self.dir], self.dir)
        self.assertEqual(code, 1)
        # 两道防线都会拦下它:symlink 检查,或 realpath 落在仓库外的越权检查
        self.assertTrue("符号链接" in out or "仓库外" in out, out)
        self.assertFalse(os.path.exists(os.path.join(outside, "INDEX.md")))

    def test_仓库内的符号链接目录同样被拒绝(self):
        """越权检查过得去(仍在仓库内),这时要靠逐级 symlink 检查兜住。"""
        os.makedirs(self.path("real", "cache"))
        os.makedirs(self.path("docs", "evolution"))
        os.symlink(self.path("real", "cache"), self.path("docs", "evolution", ".cache"))
        code, out = run_index(["--project-dir", self.dir], self.dir)
        self.assertEqual(code, 1)
        self.assertIn("符号链接", out)
        self.assertFalse(os.path.exists(self.path("real", "cache", "records.json")))

    def test_仓库内配置指向仓库外被拒绝(self):
        outside = os.path.realpath(tempfile.mkdtemp(prefix="evolog-outside-"))
        self.addCleanup(shutil.rmtree, outside, True)
        self.enable(storage_dir=outside)
        code, out = run_index(["--project-dir", self.dir], self.dir)
        self.assertEqual(code, 1)
        self.assertIn("仓库外", out)
        self.assertFalse(os.path.exists(os.path.join(outside, "INDEX.md")))

    def test_显式开关放行仓库外存储(self):
        outside = os.path.realpath(tempfile.mkdtemp(prefix="evolog-outside-"))
        self.addCleanup(shutil.rmtree, outside, True)
        self.enable(storage_dir=outside)
        code, _ = run_index(["--project-dir", self.dir, "--allow-external-storage"], self.dir)
        self.assertEqual(code, 0)
        self.assertTrue(os.path.exists(os.path.join(outside, "INDEX.md")))

    def test_环境变量放行仓库外存储(self):
        outside = os.path.realpath(tempfile.mkdtemp(prefix="evolog-outside-"))
        self.addCleanup(shutil.rmtree, outside, True)
        self.enable(storage_dir=outside)
        code, _ = run_index(["--project-dir", self.dir], self.dir,
                            env={"EVOLOG_ALLOW_EXTERNAL_STORAGE": "1"})
        self.assertEqual(code, 0)
        self.assertTrue(os.path.exists(os.path.join(outside, "INDEX.md")))

    def test_EVOLOG_DIR_指向仓库外无需额外开关(self):
        outside = os.path.realpath(tempfile.mkdtemp(prefix="evolog-outside-"))
        self.addCleanup(shutil.rmtree, outside, True)
        code, _ = run_index(["--project-dir", self.dir], self.dir,
                            env={"EVOLOG_DIR": outside})
        self.assertEqual(code, 0)
        self.assertTrue(os.path.exists(os.path.join(outside, "INDEX.md")))

    def test_存储位置优先级(self):
        self.enable(storage_dir="custom/evo")
        self.assertEqual(evolog_index.resolve_storage_dir(self.dir), self.path("custom", "evo"))
        os.environ["EVOLOG_DIR"] = self.path("kb")
        try:
            self.assertEqual(evolog_index.resolve_storage_dir(self.dir), self.path("kb"))
        finally:
            del os.environ["EVOLOG_DIR"]


class TestIndexConcurrency(IndexBase):
    def test_持有锁时留下待重建标记(self):
        cache = self.path("docs", "evolution", ".cache")
        os.makedirs(os.path.join(cache, "index.lock"))
        evolog_index.LOCK_RETRIES = 1           # 别让测试等重试
        try:
            self.assertEqual(self.build(), 0)
        finally:
            evolog_index.LOCK_RETRIES = 10
        self.assertFalse(os.path.exists(self.path("docs", "evolution", "INDEX.md")))
        self.assertTrue(os.path.exists(os.path.join(cache, "rebuild.pending")))

    def test_待重建标记在下次重建时被消费(self):
        cache = self.path("docs", "evolution", ".cache")
        os.makedirs(cache)
        open(os.path.join(cache, "rebuild.pending"), "w").close()
        self.records("a.md", RECORD)
        self.assertEqual(self.build(), 0)
        self.assertFalse(os.path.exists(os.path.join(cache, "rebuild.pending")))
        self.assertIn("OAuth2", read(self.path("docs", "evolution", "INDEX.md")))

    def test_并发重建后索引不陈旧(self):
        """两个进程同时重建:后到者排队,持锁者收尾,最终索引包含最新记录。"""
        self.records("a.md", RECORD)
        procs = [subprocess.Popen([sys.executable, INDEX, "--project-dir", self.dir],
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                  cwd=self.dir, env=clean_env()) for _ in range(3)]
        for p in procs:
            self.assertEqual(p.wait(), 0)
        cache = self.path("docs", "evolution", ".cache")
        self.assertFalse(os.path.exists(os.path.join(cache, "rebuild.pending")))
        self.assertIn("OAuth2", read(self.path("docs", "evolution", "INDEX.md")))
        self.assertEqual(read_json(os.path.join(cache, "records.json"))["count"], 1)


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

    def test_配置带_schema_version(self):
        run_init(["--project-dir", self.dir], self.dir)
        cfg = read_json(self.path(".claude", "evolution-log.json"))
        self.assertEqual(cfg["schema_version"], evolog_init.SCHEMA_VERSION)

    def test_初始_records_json_与索引脚本同结构(self):
        run_init(["--project-dir", self.dir], self.dir)
        data = read_json(self.path("docs", "evolution", ".cache", "records.json"))
        self.assertEqual(data["schema_version"], evolog_index.SCHEMA_VERSION)
        self.assertEqual(data["records"], [])

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

    def test_坏配置不致命(self):
        os.makedirs(self.path(".claude"))
        with open(self.path(".claude", "evolution-log.json"), "w") as f:
            f.write("{ not json")
        code, out = run_init(["--project-dir", self.dir], self.dir)
        self.assertEqual(code, 0)
        self.assertIn("读取既有配置失败", out)

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

    def test_自定义存储目录写进配置与_gitattributes(self):
        run_init(["--project-dir", self.dir, "--storage-dir", "docs/history"], self.dir)
        cfg = read_json(self.path(".claude", "evolution-log.json"))
        self.assertEqual(cfg["storage_dir"], "docs/history")
        self.assertIn("docs/history/INDEX.md merge=ours",
                      read(self.path(".gitattributes")))

    def test_仓库外存储跳过_git_约定并提示开关(self):
        out_dir = os.path.realpath(tempfile.mkdtemp(prefix="evolog-outside-"))
        self.addCleanup(shutil.rmtree, out_dir, True)
        code, out = run_init(["--project-dir", self.dir, "--storage-dir", out_dir], self.dir)
        self.assertEqual(code, 0)
        self.assertFalse(os.path.exists(self.path(".gitattributes")))
        self.assertIn("仓库外", out)
        self.assertIn("EVOLOG_ALLOW_EXTERNAL_STORAGE", out)

    def test_非_git_仓库不装_post_merge(self):
        code, out = run_init(["--project-dir", self.dir], self.dir)
        self.assertEqual(code, 0)
        self.assertIn("非 git 仓库", out)


class TestInitGit(TempProject):
    def setUp(self):
        super(TestInitGit, self).setUp()
        subprocess.run(["git", "init", "-q", self.dir], check=True, capture_output=True)

    def git(self, *args):
        return subprocess.run(["git"] + list(args), cwd=self.dir,
                              capture_output=True, text=True).stdout.strip()

    def test_安装_post_merge_且不覆盖已有(self):
        run_init(["--project-dir", self.dir], self.dir)
        hook = self.path(".git", "hooks", "post-merge")
        self.assertTrue(os.path.exists(hook))
        self.assertTrue(os.access(hook, os.X_OK))
        with open(hook, "w", encoding="utf-8") as f:
            f.write("#!/bin/sh\necho custom\n")
        code, out = run_init(["--project-dir", self.dir], self.dir)
        self.assertIn("custom", read(hook))                 # 已有 hook 不被覆盖
        self.assertIn("请手工追加一行", out)                  # 且明确告诉用户要补什么

    def test_配置_merge_driver(self):
        """merge=ours 声明单独不生效,driver 必须落到本地 git config。"""
        run_init(["--project-dir", self.dir], self.dir)
        self.assertEqual(self.git("config", "--get", "merge.ours.driver"), "true")

    def test_merge_driver_真的消除_INDEX_冲突(self):
        """端到端:双分支各改一次 INDEX.md,合并不应产生冲突。"""
        run_init(["--project-dir", self.dir], self.dir)
        self.git("config", "user.email", "t@example.com")
        self.git("config", "user.name", "t")
        index = self.path("docs", "evolution", "INDEX.md")
        self.git("add", "-A")
        self.git("commit", "-qm", "init")
        with open(index, "a", encoding="utf-8") as f:
            f.write("| 2026-01-01 | 决策 | A → B | 甲 | ✅ | x |\n")
        self.git("add", "-A")
        self.git("commit", "-qm", "main side")
        base = self.git("rev-parse", "HEAD~1")
        self.git("checkout", "-q", "-b", "other", base)
        with open(index, "a", encoding="utf-8") as f:
            f.write("| 2026-02-02 | 决策 | C → D | 乙 | ✅ | y |\n")
        self.git("add", "-A")
        self.git("commit", "-qm", "other side")
        merge = subprocess.run(["git", "merge", "-", "--no-edit"], cwd=self.dir,
                               capture_output=True, text=True)
        self.assertEqual(merge.returncode, 0, merge.stdout + merge.stderr)
        self.assertNotIn("<<<<<<<", read(index))

    def test_初始化后_check_立即生效(self):
        run_init(["--project-dir", self.dir], self.dir)
        with open(self.path("t.jsonl"), "w", encoding="utf-8") as f:
            f.write("我们决定重构掉旧模块")
        code, _ = run_check({"cwd": self.dir, "session_id": "s1",
                             "transcript_path": self.path("t.jsonl")}, self.dir)
        self.assertEqual(code, 2)


class TestInitCodex(TempProject):
    def test_skill_装到_codex_发现目录且自包含(self):
        run_init(["--project-dir", self.dir, "--codex"], self.dir)
        root = self.path(".agents", "skills", "evolution-log")
        for rel in [("SKILL.md",), ("templates", "record.md"),
                    ("scripts", "evolog-index.py"), ("scripts", "evolog-init.py"),
                    ("scripts", "evolog-check.py")]:
            self.assertTrue(os.path.exists(os.path.join(root, *rel)), rel)

    def test_codex_hook_命令自行解析_git_root(self):
        """Codex hook 继承会话 cwd,相对路径在子目录会失效。"""
        run_init(["--project-dir", self.dir, "--codex"], self.dir)
        cmd = read_json(self.path(".codex", "hooks.json"))["hooks"]["Stop"][0]["hooks"][0]["command"]
        self.assertIn("git rev-parse --show-toplevel", cmd)
        self.assertNotIn(self.dir, cmd)          # 不把安装机的绝对路径写死进仓库

    def test_codex_hook_命令在子目录可用(self):
        """真的从子目录跑一遍这条命令,验证它能定位到脚本。"""
        subprocess.run(["git", "init", "-q", self.dir], check=True, capture_output=True)
        run_init(["--project-dir", self.dir, "--codex"], self.dir)
        sub = self.path("a", "b")
        os.makedirs(sub)
        cmd = read_json(self.path(".codex", "hooks.json"))["hooks"]["Stop"][0]["hooks"][0]["command"]
        self.enable()
        with open(self.path("t.jsonl"), "w", encoding="utf-8") as f:
            f.write("这次是架构迁移")
        payload = json.dumps({"cwd": self.dir, "session_id": "sub",
                              "transcript_path": self.path("t.jsonl")})
        p = subprocess.run(cmd, shell=True, input=payload, capture_output=True,
                           text=True, cwd=sub, env=clean_env())
        self.assertEqual(p.returncode, 2, p.stdout + p.stderr)
        self.assertIn("[evolution-log hook]", p.stderr)

    def test_codex_hook_脚本缺失时静默放行(self):
        run_init(["--project-dir", self.dir, "--codex"], self.dir)
        cmd = read_json(self.path(".codex", "hooks.json"))["hooks"]["Stop"][0]["hooks"][0]["command"]
        os.remove(self.path(".claude", "hooks", "evolog-check.py"))
        p = subprocess.run(cmd, shell=True, input="{}", capture_output=True,
                           text=True, cwd=self.dir, env=clean_env())
        self.assertEqual(p.returncode, 0)

    def test_codex_重复初始化不重复注册(self):
        run_init(["--project-dir", self.dir, "--codex"], self.dir)
        run_init(["--project-dir", self.dir, "--codex"], self.dir)
        stop = read_json(self.path(".codex", "hooks.json"))["hooks"]["Stop"]
        self.assertEqual(len(stop), 1)

    def test_codex_保留已有_hooks_配置(self):
        os.makedirs(self.path(".codex"))
        with open(self.path(".codex", "hooks.json"), "w", encoding="utf-8") as f:
            json.dump({"hooks": {"Stop": [{"hooks": [{"type": "command",
                                                      "command": "echo hi"}]}]}}, f)
        run_init(["--project-dir", self.dir, "--codex"], self.dir)
        stop = read_json(self.path(".codex", "hooks.json"))["hooks"]["Stop"]
        self.assertEqual(len(stop), 2)
        self.assertIn("echo hi", json.dumps(stop))


# --------------------------------------------------------------------------- 打包结构

class TestPackaging(unittest.TestCase):
    """市场分发的静态约束:skill 目录必须自包含,hook 注册必须指向它。"""

    def test_skill_目录自包含(self):
        for rel in [("SKILL.md",), ("templates", "record.md"),
                    ("scripts", "evolog-check.py"), ("scripts", "evolog-index.py"),
                    ("scripts", "evolog-init.py")]:
            self.assertTrue(os.path.exists(os.path.join(SKILL, *rel)), rel)

    def test_SKILL_不引用项目根下的插件文件(self):
        body = read(os.path.join(SKILL, "SKILL.md"))
        self.assertNotIn("${CLAUDE_PLUGIN_ROOT}/scripts/", body)

    def test_hook_注册指向_skill_内脚本(self):
        cmd = read_json(os.path.join(PLUGIN, "hooks", "hooks.json"))["Stop"][0]["hooks"][0]["command"]
        self.assertIn("skills/evolution-log/scripts/evolog-check.py", cmd)

    def test_插件版本与市场登记一致(self):
        plugin = read_json(os.path.join(PLUGIN, ".claude-plugin", "plugin.json"))
        market_path = os.path.join(PLUGIN, os.pardir, os.pardir,
                                   ".claude-plugin", "marketplace.json")
        entry = [p for p in read_json(market_path)["plugins"]
                 if p["name"] == "evolution-log"]
        self.assertEqual(len(entry), 1)
        self.assertEqual(entry[0]["version"], plugin["version"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
