#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""mbti_test — infer an MBTI personality type from your local AI-coding history.

Reads the prompts *you* typed into Claude Code (~/.claude/projects/**/*.jsonl)
and Codex (~/.codex/sessions/**/rollout-*.jsonl + archived_sessions), then scores
the four MBTI dichotomies with transparent, fully local heuristics.

Nothing ever leaves the machine: only local files are read, only the user's own
text is analysed, and the report prints aggregate signals plus a few short
sample phrases as evidence.

Pure Python 3 standard library — no dependencies, no SDK, no network.

Subcommands
-----------
  analyze   (default)  Score the corpus and print an MBTI report.
  sources              List the discovered history files and basic stats.

Examples
--------
  python3 mbti_test.py                          # analyze everything, all time
  python3 mbti_test.py analyze --source claude  # only Claude Code history
  python3 mbti_test.py analyze --days 30 -v     # last 30 days, show evidence
  python3 mbti_test.py analyze --project hr     # only sessions whose cwd ~ "hr"
  python3 mbti_test.py analyze --json           # machine-readable output
  python3 mbti_test.py sources                  # what would be analysed
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path

# --------------------------------------------------------------------------- #
# History discovery
# --------------------------------------------------------------------------- #

def claude_history_root() -> Path:
    return Path(os.environ.get("CLAUDE_HISTORY_DIR", Path.home() / ".claude" / "projects"))


def codex_history_roots() -> list[Path]:
    base = Path(os.environ.get("CODEX_HISTORY_DIR", Path.home() / ".codex"))
    return [base / "sessions", base / "archived_sessions"]


def discover_files(source: str) -> dict[str, list[Path]]:
    """Return {"claude": [...], "codex": [...]} of session jsonl files."""
    out: dict[str, list[Path]] = {"claude": [], "codex": []}
    if source in ("all", "claude"):
        root = claude_history_root()
        if root.is_dir():
            out["claude"] = sorted(root.rglob("*.jsonl"))
    if source in ("all", "codex"):
        for root in codex_history_roots():
            if root.is_dir():
                out["codex"].extend(sorted(root.rglob("rollout-*.jsonl")))
    return out


# --------------------------------------------------------------------------- #
# Prompt extraction
# --------------------------------------------------------------------------- #

def _clean(text: str) -> str | None:
    """Normalise a candidate prompt; return None if it should be dropped."""
    if not isinstance(text, str):
        return None
    t = text.strip()
    if not t:
        return None
    # Drop harness-injected blocks (system reminders, command stdout, hooks…).
    if t.startswith("<"):
        return None
    # Drop pure slash-command / meta lines.
    if t in {"resume", "continue", "/clear", "/compact"}:
        return None
    return t


def extract_claude(path: Path):
    """Yield (text, cwd, mtime) of real user prompts from a Claude Code session."""
    try:
        fh = path.open(encoding="utf-8", errors="replace")
    except OSError:
        return
    with fh:
        for line in fh:
            try:
                obj = json.loads(line)
            except (ValueError, TypeError):
                continue
            if obj.get("type") != "user":
                continue
            # Sub-agent sidechain turns and SDK/system messages are not the
            # human's own voice — drop them.
            if obj.get("isSidechain"):
                continue
            if obj.get("promptSource") in ("sdk", "system"):
                continue
            msg = obj.get("message") or {}
            content = msg.get("content")
            text = None
            if isinstance(content, str):
                text = content
            elif isinstance(content, list):
                # Skip tool results — those are not user-authored.
                if any(isinstance(b, dict) and b.get("type") == "tool_result" for b in content):
                    continue
                parts = [b.get("text") for b in content
                         if isinstance(b, dict) and b.get("type") == "text"]
                text = "\n".join(p for p in parts if p)
            t = _clean(text or "")
            if t:
                yield t, obj.get("cwd", ""), obj.get("gitBranch", "")


def extract_codex(path: Path):
    """Yield (text, cwd, branch) of real user prompts from a Codex rollout."""
    try:
        fh = path.open(encoding="utf-8", errors="replace")
    except OSError:
        return
    cwd = ""
    with fh:
        for line in fh:
            try:
                obj = json.loads(line)
            except (ValueError, TypeError):
                continue
            payload = obj.get("payload") or {}
            kind = obj.get("type")
            if kind == "session_meta" and not cwd:
                cwd = payload.get("cwd", "") or ""
            elif kind == "turn_context" and not cwd:
                cwd = payload.get("cwd", "") or ""
            elif kind == "event_msg" and payload.get("type") == "user_message":
                t = _clean(payload.get("message") or payload.get("text") or "")
                if t:
                    yield t, cwd, ""


EXTRACTORS = {"claude": extract_claude, "codex": extract_codex}


def _is_subagent_file(path: Path) -> bool:
    return "subagents" in path.parts or path.name.startswith("agent-")


def collect_prompts(files: dict[str, list[Path]], *, days: int | None,
                    project: str | None, min_len: int, max_chars: int):
    """Gather prompts honouring --days / --project / --max-chars filters.

    Returns (prompts, meta) where prompts is a list of strings and meta carries
    per-tool counts, distinct sessions, and how many oversized pastes were
    dropped (so the report can be honest about what was excluded).
    """
    import time
    cutoff = (time.time() - days * 86400) if days else None
    prompts: list[str] = []
    per_tool = Counter()
    sessions = Counter()
    dropped_big = 0
    for tool, paths in files.items():
        extractor = EXTRACTORS[tool]
        for path in paths:
            if _is_subagent_file(path):
                continue
            if cutoff is not None:
                try:
                    if path.stat().st_mtime < cutoff:
                        continue
                except OSError:
                    continue
            saw_one = False
            for text, cwd, _branch in extractor(path):
                if project and project.lower() not in (cwd or "").lower():
                    continue
                if length_units(text) < min_len:
                    continue
                # Oversized messages are pasted docs / slash-command expansions /
                # auto-generated plans — not the user's conversational voice.
                if max_chars and len(text) > max_chars:
                    dropped_big += 1
                    continue
                prompts.append(text)
                per_tool[tool] += 1
                saw_one = True
            if saw_one:
                sessions[tool] += 1
    return prompts, {"per_tool": dict(per_tool), "sessions": dict(sessions),
                     "dropped_oversized": dropped_big}


# --------------------------------------------------------------------------- #
# Text metrics
# --------------------------------------------------------------------------- #

_CJK = re.compile(r"[一-鿿]")
_ASCII_WORD = re.compile(r"[A-Za-z0-9_]+")
_PATH = re.compile(r"(?:[~./][\w.\-]*)?(?:[\w.\-]+/){1,}[\w.\-]+|\b\w+\.[a-zA-Z]{1,5}\b")
_LINEREF = re.compile(r":\d+")
_BACKTICK = re.compile(r"`[^`]+`")
_IDENT = re.compile(r"\b[a-z]+[A-Z][A-Za-z]+\b|\b\w+_\w+\b|\b\w+\(\)")
_NUMBER = re.compile(r"\b\d+\b")
_EMOJI = re.compile(
    "[\U0001F300-\U0001FAFF\U00002600-\U000027BF\U0001F000-\U0001F0FF❤]")


def length_units(text: str) -> int:
    """Language-fair length: CJK chars + ASCII word tokens."""
    return len(_CJK.findall(text)) + len(_ASCII_WORD.findall(text))


def _count(pattern: re.Pattern, text: str, cap: int) -> int:
    return min(len(pattern.findall(text)), cap)


# --------------------------------------------------------------------------- #
# Keyword lexicons  (CJK matched as substrings, ASCII matched word-boundary)
# --------------------------------------------------------------------------- #

LEXICON: dict[str, list[str]] = {
    # E — extraversion: thinking out loud, collaborative, conversational
    "E": ["我觉得", "我想", "我们", "咱们", "你觉得", "你说", "聊聊", "讨论", "想法",
          "头脑风暴", "一起", "帮我想", "顺便", "对了", "另外", "还有", "感觉",
          "i think", "i feel", "let's", "lets", "we should", "what do you",
          "brainstorm", "discuss", "by the way", "also", "wonder"],
    # S — sensing: concrete, specific, detail / fact oriented
    "S": ["具体", "步骤", "一步一步", "第一", "第二", "例子", "比如", "精确", "准确",
          "行号", "这一行", "报错", "复现", "细节", "参数", "字段", "现状", "当前",
          "specific", "exact", "step by step", "error", "reproduce", "detail",
          "example", "for instance", "parameter", "field", "current"],
    # N — intuition: abstract, big-picture, why / pattern oriented
    "N": ["架构", "设计", "思路", "原理", "概念", "整体", "方案", "愿景", "为什么",
          "本质", "模式", "抽象", "长远", "未来", "可能", "也许", "大概", "通用",
          "architecture", "design", "concept", "why", "overall", "approach",
          "vision", "abstract", "pattern", "in general", "big picture", "what if"],
    # T — thinking: impersonal logic, analysis, correctness
    "T": ["因为", "所以", "逻辑", "性能", "效率", "正确", "错误", "验证", "对比",
          "权衡", "原因", "分析", "因此", "优化", "规范",
          "because", "therefore", "logic", "performance", "correct", "verify",
          "compare", "tradeoff", "analyze", "efficient", "optimize"],
    # F — feeling: politeness, gratitude, warmth, emotion
    "F": ["请", "谢谢", "多谢", "麻烦", "辛苦", "拜托", "帮忙", "抱歉", "不好意思",
          "感谢", "太好了", "喜欢", "加油", "厉害", "棒",
          "please", "thanks", "thank you", "sorry", "appreciate", "great",
          "awesome", "love", "nice", "kindly", "would you mind"],
    # J — judging: plan-first, structured, decisive
    "J": ["计划", "规划", "方案", "先", "然后", "按顺序", "列出", "整理", "确定",
          "一定要", "必须", "流程", "制定", "拆分", "待办", "梳理",
          "plan", "first", "then", "steps", "outline", "list", "organize",
          "must", "ensure", "finalize", "milestone", "todo"],
    # P — perceiving: exploratory, tentative, spontaneous, iterative
    "P": ["试试", "试一下", "看看", "跑跑看", "随便", "改改", "或者", "要不", "再说",
          "临时", "玩玩", "探索", "随意", "再看", "调整下", "改一下",
          "try", "let's see", "maybe", "just", "quick", "play around",
          "explore", "tweak", "experiment", "whatever", "see how", "for now"],
}

# Pre-compile ASCII keyword matchers; CJK stay as substrings.
_ASCII_KW: dict[str, list[tuple[str, re.Pattern]]] = {}
_CJK_KW: dict[str, list[str]] = {}
for _pole, _words in LEXICON.items():
    _ASCII_KW[_pole] = []
    _CJK_KW[_pole] = []
    for _w in _words:
        if _CJK.search(_w):
            _CJK_KW[_pole].append(_w)
        else:
            _ASCII_KW[_pole].append((_w, re.compile(r"\b" + re.escape(_w) + r"\b")))


# Cap each keyword's contribution per prompt so one repetitive / pasted message
# cannot dominate the corpus.
_KW_CAP_PER_PROMPT = 3


def keyword_hits(pole: str, text_lower: str) -> Counter:
    """Count keyword occurrences for one pole within a lowercased prompt."""
    hits: Counter = Counter()
    for w in _CJK_KW[pole]:
        c = text_lower.count(w)
        if c:
            hits[w] += min(c, _KW_CAP_PER_PROMPT)
    for w, pat in _ASCII_KW[pole]:
        c = len(pat.findall(text_lower))
        if c:
            hits[w] += min(c, _KW_CAP_PER_PROMPT)
    return hits


# --------------------------------------------------------------------------- #
# Scoring
# --------------------------------------------------------------------------- #

# Calibration constants for the length-based EI signals. Length uses the MEDIAN
# prompt size (robust to the occasional huge paste that survives filtering).
_LEN_MID, _LEN_SCALE = 12.0, 16.0      # median length-units per prompt
_PPS_MID, _PPS_SCALE = 10.0, 12.0      # prompts per session
_TERSE_UNITS = 6                       # a prompt this short counts as "terse"

# Axis definition: (left_letter, right_letter)
AXES = [("E", "I"), ("S", "N"), ("T", "F"), ("J", "P")]
AXIS_NAMES = {
    "E": "外向 Extraversion", "I": "内向 Introversion",
    "S": "实感 Sensing", "N": "直觉 Intuition",
    "T": "思考 Thinking", "F": "情感 Feeling",
    "J": "判断 Judging", "P": "知觉 Perceiving",
}


def analyse(prompts: list[str]) -> dict:
    """Compute per-axis evidence and resulting MBTI type from prompts."""
    n = len(prompts)
    if n == 0:
        return {"n_prompts": 0}

    # Per-pole keyword tallies, and per-keyword evidence for display.
    kw_rate: dict[str, float] = {p: 0.0 for p in LEXICON}
    kw_evidence: dict[str, Counter] = {p: Counter() for p in LEXICON}

    # Structural accumulators (averaged per prompt later).
    path_d = code_d = num_d = emoji_d = exclaim_d = polite_d = 0.0
    total_len = 0
    lengths: list[int] = []
    terse = 0
    why_d = seq_d = 0.0

    for raw in prompts:
        low = raw.lower()
        for pole in LEXICON:
            h = keyword_hits(pole, low)
            kw_rate[pole] += sum(h.values())
            kw_evidence[pole].update(h)

        lu = length_units(raw)
        total_len += lu
        lengths.append(lu)
        if lu <= _TERSE_UNITS:
            terse += 1

        path_d += _count(_PATH, raw, 6) + _count(_LINEREF, raw, 4)
        code_d += _count(_BACKTICK, raw, 5) + _count(_IDENT, raw, 5)
        num_d += _count(_NUMBER, raw, 5)
        emoji_d += _count(_EMOJI, raw, 4)
        exclaim_d += min(raw.count("!") + raw.count("！"), 4)
        polite_d += min(low.count("请") + low.count("谢") + low.count("麻烦")
                        + low.count("please") + low.count("thanks"), 4)
        why_d += min(raw.count("为什么") + len(re.findall(r"\bwhy\b", low)), 3)
        seq_d += 1.0 if ("先" in raw and ("然后" in raw or "再" in raw)) else 0.0

    for pole in kw_rate:
        kw_rate[pole] /= n  # mentions per prompt
    import statistics
    avg_len = total_len / n
    median_len = statistics.median(lengths)
    pps = n / max(1, _session_estimate)  # set by caller via closure-free global

    # Normalise structural densities to per-prompt rates.
    path_d /= n; code_d /= n; num_d /= n
    emoji_d /= n; exclaim_d /= n; polite_d /= n; why_d /= n; seq_d /= n
    terse_ratio = terse / n

    # ---- Evidence points per pole ---------------------------------------- #
    len_excess = max(0.0, (median_len - _LEN_MID) / _LEN_SCALE)
    len_deficit = max(0.0, (_LEN_MID - median_len) / _LEN_SCALE)
    pps_excess = max(0.0, (pps - _PPS_MID) / _PPS_SCALE)
    pps_deficit = max(0.0, (_PPS_MID - pps) / _PPS_SCALE)

    ev = {
        "E": 1.4 * kw_rate["E"] + 0.3 * len_excess + 0.5 * pps_excess,
        "I": 0.9 * terse_ratio + 0.3 * len_deficit + 0.5 * pps_deficit,
        "S": 1.0 * kw_rate["S"] + 1.2 * path_d + 0.8 * code_d + 0.6 * num_d,
        "N": 1.2 * kw_rate["N"] + 0.6 * why_d,
        "T": 1.0 * kw_rate["T"] + 0.25,                 # mild blunt-by-default prior
        "F": 1.4 * kw_rate["F"] + 0.8 * polite_d + 0.6 * emoji_d + 0.4 * exclaim_d,
        "J": 1.2 * kw_rate["J"] + 0.4 * seq_d,
        "P": 1.2 * kw_rate["P"],
    }

    alpha = 0.15  # Laplace prior so a thin corpus stays near 50/50
    axes_out = []
    letters = ""
    for left, right in AXES:
        el, er = ev[left], ev[right]
        p_left = (el + alpha) / (el + er + 2 * alpha)
        p_right = 1 - p_left
        letter = left if p_left >= p_right else right
        conf = max(p_left, p_right)
        letters += letter
        axes_out.append({
            "left": left, "right": right,
            "letter": letter,
            "p_left": round(p_left, 4), "p_right": round(p_right, 4),
            "confidence": round(conf * 100, 1),
            "evidence": {
                left: round(el, 3), right: round(er, 3),
                "top_keywords": {
                    left: kw_evidence.get(left, Counter()).most_common(5),
                    right: kw_evidence.get(right, Counter()).most_common(5),
                },
            },
        })

    return {
        "n_prompts": n,
        "type": letters,
        "axes": axes_out,
        "stats": {
            "avg_length_units": round(avg_len, 1),
            "median_length_units": round(median_len, 1),
            "prompts_per_session": round(pps, 1),
            "terse_ratio": round(terse_ratio, 3),
            "path_density": round(path_d, 3),
            "politeness_density": round(polite_d, 3),
            "emoji_density": round(emoji_d, 3),
        },
    }


# `analyse` needs a session count for prompts-per-session; pass it via a module
# global set immediately before the call (keeps the function signature clean and
# the unit tests trivial to drive).
_session_estimate = 1


def run_analysis(prompts: list[str], sessions: int) -> dict:
    global _session_estimate
    _session_estimate = max(1, sessions)
    return analyse(prompts)


# --------------------------------------------------------------------------- #
# Type catalogue
# --------------------------------------------------------------------------- #

# type -> (nickname, one-line tag, witty roast)
TYPE_INFO = {
    "INTJ": ("建筑师", "深谋远虑的策略家",
             "脑子里永远跑着一张三年后的架构图，跟你聊需求像在被面试。计划通本通，就是偶尔忘了人类需要解释。"),
    "INTP": ("逻辑学家", "拆解原理的思想者",
             "对「为什么」的执着堪比三岁小孩，能为一个边界条件跟 AI 辩到天亮。落地？等我先把原理想明白。"),
    "ENTJ": ("指挥官", "目标驱动的统帅",
             "开口就是路线图和里程碑，AI 在你这儿不是助手是下属。效率拉满，连 DDL 都怕你。"),
    "ENTP": ("辩论家", "点子机关枪",
             "点子比 commit 还多，「要不试试这个」是口头禅。九个坑同时挖，填完算我输。"),
    "INFJ": ("提倡者", "理想主义的设计者",
             "既要宏大愿景又要照顾每个细节的感受，AI 一边写代码一边被你的理想主义感动到。"),
    "INFP": ("调停者", "温和的探索者",
             "在乎的不是能不能跑，是这段代码「对不对味」。温柔地探索，认真地纠结。"),
    "ENFJ": ("主人公", "暖心的协作者",
             "「我们一起」挂在嘴边，连重构都要让 AI 有参与感。团队气氛组组长，bug 都被你哄好了。"),
    "ENFP": ("竞选者", "热情的探险家",
             "好奇心爆棚，三句话能跳四个话题，AI 陪你聊天得开五个浏览器标签。热情就是生产力。"),
    "ISTJ": ("物流师", "务实的执行者",
             "字段、路径、行号张口就来，你不是在提问，是在派工单。说一不二，AI 不敢摸鱼。"),
    "ISFJ": ("守卫者", "细心的守护者",
             "需求说得明明白白还不忘说声谢谢，AI 在你这儿被照顾得明明白白。靠谱二字写在脸上。"),
    "ESTJ": ("总经理", "雷厉风行的组织者",
             "流程、步骤、先后顺序安排得明明白白，AI 是你流水线上的一环。要的是结果，不是借口。"),
    "ESFJ": ("执政官", "周到的协调者",
             "既盯落地细节又顾及他人感受，催进度都催得让人心甘情愿。组织协调天花板。"),
    "ISTP": ("鉴赏家", "动手派的工匠",
             "少废话，先跑起来看看再说。文档？代码能跑就是最好的文档。动手能力点满。"),
    "ISFP": ("探险家", "安静的实验者",
             "安静地边做边调，不喜欢被计划绑架，手感对了就上。随性，但有审美。"),
    "ESTP": ("企业家", "行动至上的玩家",
             "直接上手快速迭代，能 demo 绝不画饼，「先跑通再优化」是信仰。行动派代言人。"),
    "ESFP": ("表演者", "活力四射的即兴者",
             "边聊边干即兴发挥，会话现场感拉满，写代码都自带 BGM。气氛和产出双在线。"),
}

# Type group → display theme (used by both the catalogue text and the HTML report).
TYPE_GROUP = {
    **{t: ("分析家 Analysts", "#7c5cbf", "#a98be0") for t in ("INTJ", "INTP", "ENTJ", "ENTP")},
    **{t: ("外交家 Diplomats", "#2e9e74", "#5cc79a") for t in ("INFJ", "INFP", "ENFJ", "ENFP")},
    **{t: ("守护者 Sentinels", "#3d86c6", "#6fb0e6") for t in ("ISTJ", "ISFJ", "ESTJ", "ESFJ")},
    **{t: ("探险家 Explorers", "#d99a2b", "#f0c45e") for t in ("ISTP", "ISFP", "ESTP", "ESFP")},
}


def axis_quip(letter: str, conf: float, stats: dict) -> str:
    """A data-aware, tongue-in-cheek one-liner for an axis result."""
    terse = stats["terse_ratio"] * 100
    pps = stats["prompts_per_session"]
    med = stats["median_length_units"]
    polite = stats["politeness_density"]
    if letter == "I":
        if terse >= 20:
            return f"{terse:.0f}% 的提示词短到像发电报——标点都嫌多余，言简意赅本赅。"
        if pps < 6:
            return f"每会话平均才 {pps:.0f} 句就把活派完，社恐人士的高效典范。"
        return "话不多，但每句都踩在点上，惜字如金。"
    if letter == "E":
        if med >= 25:
            return f"平均一条 {med:.0f} 词元，话痨实锤，AI 都得中途喘口气。"
        if pps >= 14:
            return f"一个会话能聊 {pps:.0f} 个来回，AI 是你最忠实的搭子。"
        return "想到哪说到哪，边聊边把思路理顺。"
    if letter == "S":
        if conf >= 80:
            return "张口就是字段 / 路径 / 报错——你不是在聊天，是在写需求文档。"
        return "偏爱具体细节，喜欢有图有真相。"
    if letter == "N":
        if conf >= 80:
            return "满嘴「架构 / 思路 / 为什么」，AI 怀疑自己在陪你上哲学课。"
        return "更关心大方向和「为什么」，细节嘛交给 AI 去抠。"
    if letter == "T":
        if conf >= 70:
            return "「逻辑 / 验证 / 对比」轮番上阵，对就是对、错就是错，AI 不敢造次。"
        return "讲道理为主，偶尔也会客气一句。"
    if letter == "F":
        if polite >= 0.2:
            return "「请 / 谢谢 / 麻烦」不离口，AI 被尊重得有点受宠若惊。"
        return "在意沟通的温度，代码也要有点人情味。"
    if letter == "J":
        if conf >= 70:
            return "「先…然后…列出步骤」，没有计划浑身难受，甘特图刻进了 DNA。"
        return "习惯先谋后动，心里得先有个谱。"
    if letter == "P":
        if conf >= 70:
            return "「试试看 / 或者 / 再说」——方案？跑起来再说，敏捷开发亲儿子。"
        return "走一步看一步，灵活应变不内耗。"
    return ""


# --------------------------------------------------------------------------- #
# Rendering
# --------------------------------------------------------------------------- #

def _bar(pct: float, width: int = 24, fill: str = "█", empty: str = "░") -> str:
    k = int(round(pct / 100 * width))
    return fill * k + empty * (width - k)


def render(result: dict, meta: dict, *, verbose: bool, color: bool) -> str:
    def c(code: str, s: str) -> str:
        return f"\033[{code}m{s}\033[0m" if color else s

    if result.get("n_prompts", 0) == 0:
        return ("没有找到可分析的用户提示词。\n"
                "请确认本机存在 Claude Code (~/.claude/projects) 或 "
                "Codex (~/.codex/sessions) 的会话历史，或放宽 --days / --project 过滤。")

    mtype = result["type"]
    nick, tag, roast = TYPE_INFO.get(mtype, ("神秘类型", "未解之谜", ""))
    group = TYPE_GROUP.get(mtype, ("", "", ""))[0]
    lines = []
    lines.append(c("1;36", "╭───────────────  AI 会话人格画像  ───────────────╮"))
    lines.append(f"  你的 MBTI 类型：{c('1;33', mtype)}  「{c('1;35', nick)}」"
                 + (f"  · {c('2', group)}" if group else ""))
    lines.append(f"  {c('3', tag)}")
    lines.append(f"  {c('1;37', '锐评：')}{roast}")
    pt = meta.get("per_tool", {})
    src = " + ".join(f"{k} {v}" for k, v in pt.items()) or "—"
    lines.append(f"  样本：{result['n_prompts']} 条你亲手输入的提示词（{src}）")
    lines.append(c("1;36", "╰─────────────────────────────────────────────────╯"))
    lines.append("")

    for ax in result["axes"]:
        left, right = ax["left"], ax["right"]
        chosen = ax["letter"]
        pr = ax["p_right"] * 100  # how far toward the right letter
        # Highlight the winning side.
        ln = AXIS_NAMES[left].split()[0]
        rn = AXIS_NAMES[right].split()[0]
        lL = c("1;32", left) if chosen == left else c("2", left)
        rL = c("1;32", right) if chosen == right else c("2", right)
        lines.append(f"{lL} {ln:<6} {_bar(100 - pr)}┃{_bar(pr)} {rn:<6} {rL}"
                     f"   →  {c('1;32', chosen)} {ax['confidence']:.0f}%")
        lines.append(f"    {c('2', '↪ ' + axis_quip(chosen, ax['confidence'], result['stats']))}")
        if verbose:
            tk = ax["evidence"]["top_keywords"]
            for pole in (left, right):
                kws = tk[pole]
                if kws:
                    shown = "、".join(f"{w}×{n}" for w, n in kws)
                    lines.append(f"    {c('2', pole+' 证据')}: {shown}")
        lines.append("")

    s = result["stats"]
    lines.append(c("1;36", "信号面板"))
    lines.append(f"  提示词长度中位数 ~ {s['median_length_units']} 词元"
                 f" · 每会话提示词 ~ {s['prompts_per_session']}"
                 f" · 极简短占比 {s['terse_ratio']*100:.0f}%")
    lines.append(f"  路径/代码密度 {s['path_density']:.2f}"
                 f" · 礼貌用语密度 {s['politeness_density']:.2f}"
                 f" · emoji 密度 {s['emoji_density']:.2f}")
    dropped = meta.get("dropped_oversized", 0)
    if dropped:
        lines.append(c("2", f"  （已忽略 {dropped} 条超长粘贴/自动展开消息，只看你的对话语气）"))
    if result["n_prompts"] < 20:
        lines.append(c("1;33", "  ⚠ 样本偏少，结果仅供娱乐，置信度有限。"))
    lines.append("")
    lines.append(c("2", "纯本地启发式推断 · 仅读取本机文件 · 不上传任何数据 · 娱乐向，非心理诊断"))
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# HTML report
# --------------------------------------------------------------------------- #

# Warm tones for the left poles (E/S/T/J), cool tones for the right (I/N/F/P).
_POLE_COLOR = {
    "E": "#ff8a5c", "S": "#ff8a5c", "T": "#ff8a5c", "J": "#ff8a5c",
    "I": "#5a9fe0", "N": "#5a9fe0", "F": "#5a9fe0", "P": "#5a9fe0",
}


def render_html(result: dict, meta: dict, *, source_label: str,
                generated_at: str = "") -> str:
    """Render a self-contained, offline HTML report (no external assets)."""
    from html import escape as e

    if result.get("n_prompts", 0) == 0:
        return ("<!doctype html><meta charset='utf-8'>"
                "<body style='font-family:sans-serif;padding:3rem'>"
                "<h1>没有可分析的会话历史 🤷</h1>"
                "<p>请确认本机存在 Claude Code / Codex 的会话历史，或放宽 --days / --project 过滤。</p>")

    mtype = result["type"]
    nick, tag, roast = TYPE_INFO.get(mtype, ("神秘类型", "未解之谜", ""))
    group, c1, c2 = TYPE_GROUP.get(mtype, ("", "#555", "#888"))
    pt = meta.get("per_tool", {})
    src = "、".join(f"{k} {v} 条" for k, v in pt.items()) or "—"
    s = result["stats"]

    axis_html = []
    for ax in result["axes"]:
        left, right, win = ax["left"], ax["right"], ax["letter"]
        pl, pr = ax["p_left"] * 100, ax["p_right"] * 100
        ln, rn = AXIS_NAMES[left], AXIS_NAMES[right]
        quip = axis_quip(win, ax["confidence"], s)
        win_kws = ax["evidence"]["top_keywords"].get(win, [])
        chips = "".join(
            f"<span class='chip'>{e(str(w))}<i>×{n}</i></span>" for w, n in win_kws[:6])
        chips_html = f"<div class='chips'>{chips}</div>" if chips else ""
        axis_html.append(f"""
      <div class="axis">
        <div class="poles">
          <span class="pole {'win' if win == left else 'lose'}" style="--pc:{_POLE_COLOR[left]}">
            <b>{left}</b> {e(ln.split()[0])}</span>
          <span class="verdict">→ {win} · {ax['confidence']:.0f}%</span>
          <span class="pole right {'win' if win == right else 'lose'}" style="--pc:{_POLE_COLOR[right]}">
            {e(rn.split()[0])} <b>{right}</b></span>
        </div>
        <div class="track">
          <div class="fill {'win' if win == left else 'lose'}" style="width:{pl:.1f}%;background:{_POLE_COLOR[left]}"></div>
          <div class="fill {'win' if win == right else 'lose'}" style="width:{pr:.1f}%;background:{_POLE_COLOR[right]}"></div>
        </div>
        <div class="quip">{e(quip)}</div>
        {chips_html}
      </div>""")

    dropped = meta.get("dropped_oversized", 0)
    dropped_note = (f"（已忽略 {dropped} 条超长粘贴/自动展开消息，只看你的对话语气）"
                    if dropped else "")
    small_warn = ("<p class='warn'>⚠ 样本偏少，结果仅供娱乐，置信度有限。</p>"
                  if result["n_prompts"] < 20 else "")
    gen = f"<span>· 生成于 {e(generated_at)}</span>" if generated_at else ""

    return f"""<!doctype html>
<html lang="zh-CN"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>AI 会话人格画像 · {mtype} {e(nick)}</title>
<style>
  :root {{ --c1:{c1}; --c2:{c2}; }}
  * {{ box-sizing: border-box; }}
  body {{ margin:0; padding:2.2rem 1rem 3rem; background:#0f1117;
         font-family:-apple-system,"PingFang SC","Microsoft YaHei",Segoe UI,sans-serif;
         color:#e8eaf0; line-height:1.6; }}
  .wrap {{ max-width:720px; margin:0 auto; }}
  .card {{ background:#171a23; border:1px solid #242838; border-radius:18px;
          padding:1.6rem 1.8rem; margin-bottom:1.1rem;
          box-shadow:0 10px 40px rgba(0,0,0,.35); }}
  .hero {{ background:linear-gradient(135deg,var(--c1),var(--c2));
          color:#fff; position:relative; overflow:hidden; border:none; }}
  .hero .watermark {{ position:absolute; right:-.4rem; bottom:-2.4rem; font-size:9rem;
          font-weight:800; letter-spacing:-.05em; opacity:.16; line-height:1; }}
  .hero .group {{ display:inline-block; font-size:.8rem; padding:.15rem .7rem;
          background:rgba(255,255,255,.2); border-radius:999px; margin-bottom:.6rem; }}
  .hero h1 {{ margin:.1rem 0 .2rem; font-size:3.2rem; letter-spacing:.06em; }}
  .hero h1 small {{ font-size:1.4rem; font-weight:600; opacity:.95; letter-spacing:0; }}
  .hero .tag {{ font-size:1.05rem; opacity:.95; margin:.1rem 0 .9rem; }}
  .hero .roast {{ background:rgba(0,0,0,.18); border-radius:12px; padding:.7rem .9rem;
          font-size:.98rem; position:relative; z-index:1; }}
  .hero .roast b {{ opacity:.85; }}
  .sample {{ color:#aeb4c6; font-size:.9rem; margin-top:.9rem; position:relative; z-index:1; }}
  h2.sec {{ font-size:.85rem; text-transform:uppercase; letter-spacing:.12em;
          color:#8b93a9; margin:0 0 1rem; font-weight:700; }}
  .axis {{ margin-bottom:1.35rem; }}
  .axis:last-child {{ margin-bottom:.2rem; }}
  .poles {{ display:flex; align-items:center; justify-content:space-between;
          font-size:.92rem; margin-bottom:.4rem; }}
  .pole b {{ font-size:1.05rem; color:var(--pc); }}
  .pole.lose {{ opacity:.4; }}
  .pole.win b {{ text-shadow:0 0 12px var(--pc); }}
  .verdict {{ font-weight:700; color:#fff; font-size:.9rem; }}
  .track {{ display:flex; height:13px; border-radius:999px; overflow:hidden;
          background:#0f1117; }}
  .fill.lose {{ opacity:.28; }}
  .quip {{ color:#c7cdde; font-size:.92rem; margin-top:.5rem; }}
  .chips {{ margin-top:.5rem; display:flex; flex-wrap:wrap; gap:.4rem; }}
  .chip {{ background:#222636; border:1px solid #2e3346; color:#c7cdde;
          font-size:.78rem; padding:.16rem .55rem; border-radius:8px; }}
  .chip i {{ color:#7f879c; font-style:normal; margin-left:.2rem; }}
  .signals {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr));
          gap:.7rem; }}
  .sig {{ background:#1c2030; border-radius:12px; padding:.7rem .8rem; }}
  .sig .v {{ font-size:1.3rem; font-weight:700; color:#fff; }}
  .sig .k {{ font-size:.78rem; color:#8b93a9; }}
  .warn {{ color:#f0c45e; font-size:.9rem; }}
  .foot {{ text-align:center; color:#697089; font-size:.8rem; margin-top:1.4rem; }}
  .foot b {{ color:#8b93a9; }}
</style></head>
<body><div class="wrap">

  <div class="card hero">
    <div class="watermark">{mtype}</div>
    {f'<span class="group">{e(group)}</span>' if group else ''}
    <h1>{mtype} <small>「{e(nick)}」</small></h1>
    <div class="tag">{e(tag)}</div>
    <div class="roast"><b>锐评 ·</b> {e(roast)}</div>
    <div class="sample">📊 基于你亲手输入的 {result['n_prompts']} 条提示词 · {e(src)}（{e(source_label)}）<br>{e(dropped_note)}</div>
  </div>

  <div class="card">
    <h2 class="sec">四维度倾向</h2>
    {''.join(axis_html)}
  </div>

  <div class="card">
    <h2 class="sec">信号面板</h2>
    <div class="signals">
      <div class="sig"><div class="v">{s['median_length_units']:.0f}</div><div class="k">提示词长度中位数（词元）</div></div>
      <div class="sig"><div class="v">{s['prompts_per_session']:.1f}</div><div class="k">每会话提示词数</div></div>
      <div class="sig"><div class="v">{s['terse_ratio']*100:.0f}%</div><div class="k">极简短提示词占比</div></div>
      <div class="sig"><div class="v">{s['path_density']:.2f}</div><div class="k">路径 / 代码密度</div></div>
      <div class="sig"><div class="v">{s['politeness_density']:.2f}</div><div class="k">礼貌用语密度</div></div>
      <div class="sig"><div class="v">{s['emoji_density']:.2f}</div><div class="k">emoji 密度</div></div>
    </div>
    {small_warn}
  </div>

  <div class="foot">
    <b>纯本地启发式推断</b> · 仅读取本机文件 · 不上传任何数据 · 娱乐向，非心理诊断 {gen}
  </div>

</div></body></html>"""


# --------------------------------------------------------------------------- #
# Subcommands
# --------------------------------------------------------------------------- #

def cmd_sources(args) -> int:
    files = discover_files(args.source)
    total = 0
    for tool, paths in files.items():
        if args.source not in ("all", tool):
            continue
        print(f"[{tool}] {len(paths)} 个会话文件")
        total += len(paths)
        for p in paths[:args.limit_files] if args.limit_files else paths[:8]:
            try:
                kb = p.stat().st_size / 1024
            except OSError:
                kb = 0
            print(f"    {p}  ({kb:.0f} KB)")
        if not args.limit_files and len(paths) > 8:
            print(f"    … 其余 {len(paths) - 8} 个未列出")
    print(f"合计：{total} 个文件")
    if total == 0:
        print("未发现任何会话历史。可设置 CLAUDE_HISTORY_DIR / CODEX_HISTORY_DIR 指向自定义路径。")
    return 0


def cmd_analyze(args) -> int:
    files = discover_files(args.source)
    prompts, meta = collect_prompts(
        files, days=args.days, project=args.project, min_len=args.min_len,
        max_chars=args.max_chars)
    sessions = sum(meta["sessions"].values())
    result = run_analysis(prompts, sessions)
    result_meta = {"per_tool": meta["per_tool"],
                   "dropped_oversized": meta.get("dropped_oversized", 0)}

    if args.json:
        print(json.dumps({"result": result, "meta": meta}, ensure_ascii=False, indent=2))
        return 0

    if args.html:
        from datetime import datetime
        src_label = {"all": "Claude Code + Codex", "claude": "Claude Code",
                     "codex": "Codex"}[args.source]
        if args.days:
            src_label += f" · 近 {args.days} 天"
        html = render_html(result, result_meta, source_label=src_label,
                           generated_at=datetime.now().strftime("%Y-%m-%d %H:%M"))
        out = Path(args.output or "mbti-report.html").expanduser()
        out.write_text(html, encoding="utf-8")
        print(f"✅ HTML 报告已生成：{out.resolve()}")
        print(f"   在浏览器打开： open \"{out.resolve()}\"")
        return 0

    color = sys.stdout.isatty() and not args.no_color
    print(render(result, result_meta, verbose=args.verbose, color=color))
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="mbti_test",
        description="从本地 Claude Code / Codex 会话历史推断你的 MBTI 类型（娱乐向，纯本地）。")
    sub = p.add_subparsers(dest="command")

    def add_common(sp):
        sp.add_argument("--source", choices=["all", "claude", "codex"], default="all",
                        help="分析哪个工具的历史（默认 all）")

    a = sub.add_parser("analyze", help="分析并输出 MBTI 报告")
    add_common(a)
    a.add_argument("--days", type=int, default=None, help="只看最近 N 天内修改过的会话")
    a.add_argument("--project", default=None, help="只看 cwd 路径包含该子串的会话")
    a.add_argument("--min-len", type=int, default=2, help="忽略短于该词元数的提示词（默认 2）")
    a.add_argument("--max-chars", type=int, default=4000,
                   help="忽略长于该字符数的消息（粘贴/自动展开，非对话语气；0=不限制，默认 4000）")
    a.add_argument("--json", action="store_true", help="输出 JSON")
    a.add_argument("--html", action="store_true", help="导出精美的独立 HTML 报告")
    a.add_argument("-o", "--output", default=None,
                   help="HTML 报告输出路径（默认 ./mbti-report.html）")
    a.add_argument("--no-color", action="store_true", help="禁用彩色输出")
    a.add_argument("-v", "--verbose", action="store_true", help="显示每个维度的关键词证据")
    a.set_defaults(func=cmd_analyze)

    s = sub.add_parser("sources", help="列出发现的会话历史文件")
    add_common(s)
    s.add_argument("--limit-files", type=int, default=0, help="每个工具最多列出多少文件")
    s.set_defaults(func=cmd_sources)
    return p


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    # Default to `analyze` when no/uknown subcommand is given.
    if not argv or argv[0].startswith("-"):
        argv = ["analyze", *argv]
    elif argv[0] not in {"analyze", "sources"}:
        argv = ["analyze", *argv]
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
