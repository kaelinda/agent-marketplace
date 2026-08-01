#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Evolution Log — Stop hook 判定器
职责:在 AI 结束一轮响应前,判断本轮是否可能发生了方案级变更;
     若是,阻断结束(exit 2)并回注补录指令,交由会话内模型自评后决定是否补录。

设计约束:
  - opt-in:项目未初始化(无 .claude/evolution-log.json 且无 EVOLOG_DIR)时直接放行,
    插件装在全局也不会打扰未启用本系统的项目
  - fail-open:任何内部错误一律 exit 0 放行,绝不阻塞用户
  - stop_hook_active 防无限循环
  - 单会话最多阻断一次(标记文件在项目内 .claude/cache/evolog/)
  - transcript 只读末尾定长窗口(默认 200KB),耗时与会话长度无关
  - 零外发:本脚本不调用任何网络 API,二级判断交由会话内模型自评
仅依赖 Python 3 标准库。兼容 Claude Code 与 Codex CLI 的 Stop 事件。
"""
import json
import os
import re
import sys
import time

TAIL_BYTES = 200 * 1024          # 快筛窗口:transcript 末尾 200KB
DEFAULT_KEYWORDS = [
    # 中文信号
    "迁移", "替换", "重构", "改用", "弃用", "废弃", "切换到", "换成",
    "方案变更", "架构调整", "推翻", "改造", "升级到",
    # 英文信号
    "migrate", "migration", "refactor", "deprecate", "switch to",
    "replace with", "rewrite", "redesign",
]
INSTRUCTION_WITH_JUDGE = (
    "[evolution-log hook] 快筛检测到本轮可能发生了方案/需求/架构层面的变更。\n"
    "请先自行判断:本轮工作是否真的构成一次值得记录的演进"
    "(方案 A→B、需求调整、架构迁移、重要技术决策)?\n"
    "- 若否(只是普通编码/修 bug/小改动):无需任何操作,直接正常结束本轮。\n"
    "- 若是:调用 evolution-log skill 的记录工作流,按模板创建一条记录"
    "(frontmatter 设 status: draft、source: auto_hook),"
    "从本轮上下文预填 from/to/变更原因,owner 字段务必向用户确认,"
    "写入后运行索引重建脚本,然后结束本轮。\n"
    "(本提示每个会话至多出现一次,不会再次阻断。)"
)
INSTRUCTION_DIRECT = (
    "[evolution-log hook] 检测到本轮可能发生了方案级变更且未记录。\n"
    "请调用 evolution-log skill 的记录工作流补录一条记录"
    "(status: draft、source: auto_hook,owner 向用户确认),"
    "完成后重建索引并结束本轮。若确认本轮并无实质演进,直接正常结束。"
)


def log_error(cache_dir, msg):
    try:
        os.makedirs(cache_dir, exist_ok=True)
        with open(os.path.join(cache_dir, "error.log"), "a", encoding="utf-8") as f:
            f.write("%s  %s\n" % (time.strftime("%Y-%m-%d %H:%M:%S"), msg))
    except Exception:
        pass  # 日志失败也不影响放行


def config_path(project_dir):
    return os.path.join(project_dir, ".claude", "evolution-log.json")


def is_enabled(project_dir):
    """opt-in 门禁:项目显式初始化过才启用。

    满足任一即视为已启用:
      1) 项目内存在 .claude/evolution-log.json(evolog-init.py 会创建)
      2) 设置了 EVOLOG_DIR 环境变量(仓库外集中知识库场景)
    """
    if os.environ.get("EVOLOG_DIR", "").strip():
        return True
    return os.path.isfile(config_path(project_dir))


def has_local_copy(project_dir):
    """项目自带一份 check 脚本(standalone 安装)时,让项目内那份负责,避免双重注册重复阻断。"""
    return os.path.isfile(os.path.join(project_dir, ".claude", "hooks", "evolog-check.py"))


def load_config(project_dir):
    cfg = {
        "sensitive_paths": [],
        "keywords": DEFAULT_KEYWORDS,
        "llm_gate": True,   # true=回注指令中包含"先自评再补录";false=直接请求补录
        "auto_hook": True,  # false=关闭自动兜底,只保留手动记录/查询
    }
    try:
        path = config_path(project_dir)
        if os.path.isfile(path):
            with open(path, "r", encoding="utf-8") as f:
                user_cfg = json.load(f)
            for k in ("sensitive_paths", "keywords", "llm_gate", "auto_hook"):
                if k in user_cfg:
                    cfg[k] = user_cfg[k]
            if user_cfg.get("extra_keywords"):
                cfg["keywords"] = list(cfg["keywords"]) + list(user_cfg["extra_keywords"])
    except Exception:
        pass  # 配置损坏按默认值走,不报错
    return cfg


def read_tail(path):
    """安全读取 transcript 末尾窗口:必须是常规文件且非符号链接。"""
    if not path or not os.path.isfile(path) or os.path.islink(path):
        return ""
    size = os.path.getsize(path)
    with open(path, "rb") as f:
        if size > TAIL_BYTES:
            f.seek(size - TAIL_BYTES)
        data = f.read(TAIL_BYTES)
    return data.decode("utf-8", errors="replace")


def fast_screen(text, cfg):
    """第一级规则快筛:关键词 / 敏感路径,纯文本匹配,毫秒级。"""
    if not text:
        return False
    lowered = text.lower()
    for kw in cfg["keywords"]:
        if kw.lower() in lowered:
            return True
    for p in cfg.get("sensitive_paths") or []:
        if p and p in text:
            return True
    return False


def main():
    payload = json.load(sys.stdin)

    # ① 防无限循环:本次结束由上一次阻断驱动 → 无条件放行
    if payload.get("stop_hook_active"):
        return 0

    project_dir = payload.get("cwd") or os.getcwd()

    # ② opt-in 门禁 + 避免与项目内自带脚本双重注册
    if not is_enabled(project_dir):
        return 0
    if os.environ.get("CLAUDE_PLUGIN_ROOT") and has_local_copy(project_dir):
        return 0

    cache_dir = os.path.join(project_dir, ".claude", "cache", "evolog")
    session_id = re.sub(r"[^A-Za-z0-9_.-]", "_", str(payload.get("session_id") or "nosession"))
    marker = os.path.join(cache_dir, session_id + ".done")

    # ③ 单会话最多阻断一次
    if os.path.exists(marker):
        return 0

    # ④ 第一级快筛(定长窗口)
    cfg = load_config(project_dir)
    if not cfg.get("auto_hook", True):
        return 0
    tail = read_tail(payload.get("transcript_path"))
    if not fast_screen(tail, cfg):
        return 0

    # ⑤ 命中:先落标记(即使后续失败也不允许二次阻断),再阻断回注
    os.makedirs(cache_dir, exist_ok=True)
    with open(marker, "w", encoding="utf-8") as f:
        f.write(str(int(time.time())))

    msg = INSTRUCTION_WITH_JUDGE if cfg.get("llm_gate", True) else INSTRUCTION_DIRECT
    sys.stderr.write(msg)
    return 2


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception as e:  # fail-open 总包装
        try:
            cwd = os.getcwd()
            log_error(os.path.join(cwd, ".claude", "cache", "evolog"),
                      "evolog-check error: %r" % (e,))
        except Exception:
            pass
        sys.exit(0)
