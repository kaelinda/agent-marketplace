#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Offline unit tests for mbti_test.py — synthetic transcripts, no real history."""
import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "..", "scripts", "mbti_test.py")
spec = importlib.util.spec_from_file_location("mbti_test", SCRIPT)
mbti = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mbti)


def write_jsonl(path: Path, records: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as fh:
        for r in records:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")


class TestTextMetrics(unittest.TestCase):
    def test_length_units_mixed(self):
        # 4 CJK chars + 2 ascii word tokens
        self.assertEqual(mbti.length_units("修复 bug now 啊啊"), 4 + 2)

    def test_length_units_empty(self):
        self.assertEqual(mbti.length_units(""), 0)

    def test_keyword_hits_cap(self):
        # "plan" repeated 10× must be capped at _KW_CAP_PER_PROMPT.
        hits = mbti.keyword_hits("J", ("plan " * 10).strip())
        self.assertEqual(hits["plan"], mbti._KW_CAP_PER_PROMPT)

    def test_keyword_hits_cjk_substring(self):
        hits = mbti.keyword_hits("F", "请 帮我 谢谢 谢谢")
        self.assertGreaterEqual(hits["请"], 1)
        self.assertGreaterEqual(hits["谢谢"], 2)


class TestCleanFilter(unittest.TestCase):
    def test_drops_system_reminder(self):
        self.assertIsNone(mbti._clean("<system-reminder>noise</system-reminder>"))

    def test_drops_meta_commands(self):
        self.assertIsNone(mbti._clean("resume"))
        self.assertIsNone(mbti._clean("  "))

    def test_keeps_real_prompt(self):
        self.assertEqual(mbti._clean("  修复登录 bug  "), "修复登录 bug")


class TestExtractors(unittest.TestCase):
    def test_extract_claude_filters(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "s.jsonl"
            write_jsonl(p, [
                {"type": "user", "cwd": "/proj",
                 "message": {"role": "user", "content": "请帮我重构架构"}},
                # tool_result -> skip
                {"type": "user",
                 "message": {"role": "user",
                             "content": [{"type": "tool_result", "content": "ok"}]}},
                # sidechain (sub-agent) -> skip
                {"type": "user", "isSidechain": True,
                 "message": {"role": "user", "content": "agent task"}},
                # sdk -> skip
                {"type": "user", "promptSource": "sdk",
                 "message": {"role": "user", "content": "automated"}},
                # system reminder text -> skip
                {"type": "user",
                 "message": {"role": "user", "content": "<system-reminder>x</system-reminder>"}},
                # assistant -> skip
                {"type": "assistant", "message": {"role": "assistant", "content": "hi"}},
                # text-block list form -> keep
                {"type": "user", "cwd": "/proj",
                 "message": {"role": "user",
                             "content": [{"type": "text", "text": "试试看跑一下"}]}},
            ])
            got = [t for t, _cwd, _b in mbti.extract_claude(p)]
            self.assertEqual(got, ["请帮我重构架构", "试试看跑一下"])

    def test_extract_codex_filters(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "rollout-x.jsonl"
            write_jsonl(p, [
                {"type": "session_meta", "payload": {"cwd": "/work"}},
                {"type": "event_msg",
                 "payload": {"type": "user_message", "message": "先规划方案再实现"}},
                {"type": "event_msg",
                 "payload": {"type": "agent_message", "message": "I will help"}},
                {"type": "event_msg",
                 "payload": {"type": "user_message",
                             "message": "<system-reminder>noise</system-reminder>"}},
                {"type": "response_item",
                 "payload": {"type": "message", "role": "assistant", "content": "x"}},
            ])
            got = [(t, cwd) for t, cwd, _b in mbti.extract_codex(p)]
            self.assertEqual(got, [("先规划方案再实现", "/work")])


class TestCollect(unittest.TestCase):
    def test_skips_subagent_files_and_oversized(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "subagents").mkdir()
            write_jsonl(root / "main.jsonl", [
                {"type": "user", "cwd": "/p",
                 "message": {"role": "user", "content": "正常的一句话提问"}},
                {"type": "user", "cwd": "/p",
                 "message": {"role": "user", "content": "word " * 2000}},  # oversized paste
            ])
            write_jsonl(root / "subagents" / "agent-x.jsonl", [
                {"type": "user", "message": {"role": "user", "content": "应被忽略的子代理"}},
            ])
            files = {"claude": list(root.rglob("*.jsonl")), "codex": []}
            prompts, meta = mbti.collect_prompts(
                files, days=None, project=None, min_len=2, max_chars=4000)
            self.assertEqual(prompts, ["正常的一句话提问"])
            self.assertEqual(meta["dropped_oversized"], 1)

    def test_project_filter(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            write_jsonl(root / "s.jsonl", [
                {"type": "user", "cwd": "/home/me/alpha",
                 "message": {"role": "user", "content": "属于 alpha 的提问内容"}},
                {"type": "user", "cwd": "/home/me/beta",
                 "message": {"role": "user", "content": "属于 beta 的提问内容"}},
            ])
            files = {"claude": [root / "s.jsonl"], "codex": []}
            prompts, _ = mbti.collect_prompts(
                files, days=None, project="alpha", min_len=2, max_chars=4000)
            self.assertEqual(prompts, ["属于 alpha 的提问内容"])


class TestScoring(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(mbti.run_analysis([], 0)["n_prompts"], 0)

    def test_produces_valid_type(self):
        res = mbti.run_analysis(["修复一个 bug", "看看这个函数", "优化性能"], 1)
        self.assertEqual(len(res["type"]), 4)
        self.assertEqual([a["letter"] for a in res["axes"]],
                         list(res["type"]))
        for ax in res["axes"]:
            self.assertAlmostEqual(ax["p_left"] + ax["p_right"], 1.0, places=3)

    def test_directional_TF(self):
        polite = ["请帮我看看这个，谢谢", "麻烦你了，辛苦", "拜托帮忙改一下，感谢"] * 5
        blunt = ["分析性能瓶颈的逻辑", "验证正确性并对比", "优化效率，原因是什么"] * 5
        self.assertEqual(mbti.run_analysis(polite, 3)["type"][2], "F")
        self.assertEqual(mbti.run_analysis(blunt, 3)["type"][2], "T")

    def test_directional_JP(self):
        planner = ["先规划方案，然后按顺序列出步骤", "制定计划再拆分待办", "必须先梳理流程"] * 5
        explorer = ["试试看，或者改改", "随便跑一下看看效果", "要不先这样玩玩探索一下"] * 5
        self.assertEqual(mbti.run_analysis(planner, 3)["type"][3], "J")
        self.assertEqual(mbti.run_analysis(explorer, 3)["type"][3], "P")

    def test_directional_SN(self):
        concrete = ["第一步看 src/app/main.py:42 的报错", "字段 user_id 的具体参数",
                    "复现这个 error，准确细节"] * 5
        abstract = ["整体架构设计的思路是什么", "这个方案的本质原理为什么", "长远的概念与模式"] * 5
        self.assertEqual(mbti.run_analysis(concrete, 3)["type"][1], "S")
        self.assertEqual(mbti.run_analysis(abstract, 3)["type"][1], "N")


class TestRendering(unittest.TestCase):
    def _result(self):
        return mbti.run_analysis(
            ["先规划方案然后列出步骤", "请帮我看看 src/main.py:10 的报错，谢谢",
             "试试看这个架构思路为什么更好"] * 6, 3)

    def test_every_type_has_humorous_roast(self):
        # All 16 types carry a (nickname, tag, roast) triple with non-empty roast.
        self.assertEqual(len(mbti.TYPE_INFO), 16)
        for t, (nick, tag, roast) in mbti.TYPE_INFO.items():
            self.assertTrue(nick and tag and roast, f"{t} missing witty text")

    def test_axis_quip_nonempty_for_all_letters(self):
        stats = {"terse_ratio": 0.2, "prompts_per_session": 5.0,
                 "median_length_units": 18.0, "politeness_density": 0.3}
        for letter in "EISNTFJP":
            self.assertTrue(mbti.axis_quip(letter, 75.0, stats))

    def test_html_report_well_formed(self):
        meta = {"per_tool": {"claude": 18}, "dropped_oversized": 2}
        html = mbti.render_html(self._result(), meta,
                                source_label="Claude Code", generated_at="2026-06-25 16:00")
        self.assertTrue(html.startswith("<!doctype html>"))
        self.assertTrue(html.rstrip().endswith("</html>"))
        self.assertEqual(html.count('<div class="axis">'), 4)
        # No leaked garbage from the earlier CSS typo.
        self.assertNotIn("governing", html)
        self.assertNotIn("punto", html)

    def test_html_empty_corpus(self):
        html = mbti.render_html({"n_prompts": 0}, {}, source_label="x")
        self.assertIn("没有可分析", html)


if __name__ == "__main__":
    unittest.main(verbosity=2)
