#!/usr/bin/env bash
# cursor-dispatch.sh — Cursor Agent CLI 调度脚本
# 用法: cursor-dispatch.sh <mode> [options] "<prompt>"
#   mode: check | review | task | ask
#
# 输出策略（解决 Bash 工具输出截断问题）：
#   1. 原始输出（含工具调用轨迹）始终落盘到 $CURSOR_OUT_DIR 或 /tmp
#   2. 默认从 JSON 结果中提炼最终文本（需要 jq），显著减少体积
#   3. 若提炼后文本仍超过阈值，stdout 仅输出 head+tail + 文件路径
#      调用方（Claude）可使用 Read 工具对原始文件做分页读取
#   4. 尾部附加元信息脚注：text/raw 文件路径、大小、exit code

set -euo pipefail

# ─── 常量 ───────────────────────────────────────────────
CURSOR_CMD="cursor"
DEFAULT_OUTPUT_FORMAT="json"
DEFAULT_OUT_DIR="${CURSOR_OUT_DIR:-${TMPDIR:-/tmp}}"
# stdout 回显文本体积阈值（字节），超过则只输出头尾摘要
STDOUT_SIZE_LIMIT="${CURSOR_STDOUT_LIMIT:-20000}"
STDOUT_HEAD_BYTES=10000
STDOUT_TAIL_BYTES=4000

# ─── 辅助函数 ───────────────────────────────────────────
die()  { echo "ERROR: $*" >&2; exit 1; }
debug() { [[ "${CURSOR_DISPATCH_DEBUG:-}" == "1" ]] && echo "DEBUG: $*" >&2 || true; }

usage() {
  cat >&2 <<'EOF'
Usage: cursor-dispatch.sh <mode> [options] "<prompt>"

Modes:
  check                   检查 Cursor CLI 环境是否就绪
  review [opts] <prompt>  只读审查模式（--mode plan）
  task   [opts] <prompt>  读写任务模式（默认模式）
  ask    [opts] <prompt>  问答模式（--mode ask）

Common Options:
  --model <model>         指定模型（如 gpt-5, sonnet-4）
  --workspace <path>      工作目录（默认当前目录）
  --worktree [name]       在隔离 worktree 中执行
  --worktree-base <ref>   worktree 基于的分支
  --force                 自动批准所有操作（仅 task 模式）
  --format <fmt>          输出格式: text | json | stream-json（默认 json）
  --continue              续接上次会话
  --resume <chatId>       恢复指定会话

Output Options:
  --raw                   不提炼结果，stdout 直接回显原始输出
  --no-extract            等价于 --raw
  --out-dir <path>        原始输出落盘目录（默认 $TMPDIR 或 /tmp）
  --out-file <path>       指定原始输出文件路径（覆盖 --out-dir）

Environment Variables:
  CURSOR_OUT_DIR          默认落盘目录
  CURSOR_STDOUT_LIMIT     stdout 回显字节上限（默认 20000）
  CURSOR_DISPATCH_DEBUG   设为 1 输出调试信息（不含 prompt）

EOF
  exit 1
}

# ─── 环境检查 ───────────────────────────────────────────
cmd_check() {
  echo "=== Cursor Agent 环境检查 ==="

  if ! command -v "$CURSOR_CMD" >/dev/null 2>&1; then
    echo "FAIL: cursor 命令不可用"
    echo "  请安装 Cursor IDE 并运行 Shell Command: Install 'cursor' command"
    exit 1
  fi
  echo "OK: cursor 命令路径 — $(which "$CURSOR_CMD")"

  local version
  version=$("$CURSOR_CMD" agent --version 2>/dev/null || echo "UNKNOWN")
  echo "OK: cursor agent 版本 — $version"

  if command -v jq >/dev/null 2>&1; then
    echo "OK: jq 已安装 — $(jq --version)（可提炼 JSON 结果）"
  else
    echo "WARN: jq 未安装，将无法自动提炼 JSON 结果（建议 brew install jq）"
  fi

  echo "OK: 输出落盘目录 — $DEFAULT_OUT_DIR"
  echo "OK: stdout 回显阈值 — ${STDOUT_SIZE_LIMIT} 字节"

  local auth_status
  auth_status=$(timeout 10 "$CURSOR_CMD" agent status 2>/dev/null \
    | sed $'s/\x1b\[[0-9;]*[a-zA-Z]//g' \
    | sed 's/^[[:space:]]*//' \
    | grep -v '^$' \
    | head -3 \
    || echo "无法获取（可通过 cursor agent login 手动检查）")
  echo "AUTH: $auth_status"

  echo ""
  echo "=== 检查完成 ==="
  echo "提示: 运行 cursor agent --list-models 可查看可用模型列表"
}

# ─── 结果提炼 ───────────────────────────────────────────
# 从 cursor agent 的 JSON 输出中抽取最终文本结论
# 参数: <raw_file> <format>
# 输出: 提炼后的文本到 stdout（若提炼失败，原样 cat）
extract_result() {
  local file="$1" fmt="$2"

  if [[ ! -s "$file" ]]; then
    return 0
  fi

  if ! command -v jq >/dev/null 2>&1; then
    cat "$file"
    return 0
  fi

  local extracted=""
  case "$fmt" in
    json)
      extracted=$(jq -r '
        if type == "object" then
          (.result // .content // .message // .text // .output //
           (.messages // [] | if length > 0 then .[-1].content // .[-1].text // "" else "" end) //
           "")
        else
          tostring
        end
      ' "$file" 2>/dev/null || true)
      ;;
    stream-json)
      extracted=$(jq -rs '
        [.[] | select(type == "object")]
        | (map(select(.type == "result" or (has("result") and (.result | type == "string"))))
           | if length > 0 then .[-1].result // "" else "" end) as $r
        | if ($r | length) > 0 then $r
          else (map(select(.type == "assistant" or .type == "message"))
                | map(.content // .message // .text // "")
                | join(""))
          end
      ' "$file" 2>/dev/null || true)
      ;;
    *)
      cat "$file"
      return 0
      ;;
  esac

  if [[ -n "$extracted" && "$extracted" != "null" ]]; then
    printf '%s\n' "$extracted"
  else
    # 提炼失败 → 回退到原始内容
    cat "$file"
  fi
}

# 将文本文件输出到 stdout；过大时只打印 head + tail + 截断提示
# 参数: <file> <label>
emit_with_truncation() {
  local file="$1" label="$2"
  local size
  size=$(wc -c < "$file" | tr -d ' ')

  if [[ "$size" -le "$STDOUT_SIZE_LIMIT" ]]; then
    cat "$file"
    return 0
  fi

  # 超过阈值：输出头尾 + 提示
  head -c "$STDOUT_HEAD_BYTES" "$file"
  echo ""
  echo ""
  echo "... [TRUNCATED] ${label} 共 ${size} 字节，stdout 阈值 ${STDOUT_SIZE_LIMIT} 字节 ..."
  echo "... 完整内容见文件：${file} ..."
  echo "... 调用方可用 Read 工具分页读取（offset/limit） ..."
  echo ""
  tail -c "$STDOUT_TAIL_BYTES" "$file"
  echo ""
}

# ─── 命令构建与执行 ─────────────────────────────────────
build_cursor_cmd() {
  local mode="$1"
  shift

  local model="" workspace="" worktree="" worktree_base="" format="$DEFAULT_OUTPUT_FORMAT"
  local force=false do_continue=false resume_id="" prompt=""
  local extract=true out_dir="$DEFAULT_OUT_DIR" out_file=""

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --model)        model="$2"; shift 2 ;;
      --workspace)    workspace="$2"; shift 2 ;;
      --worktree)
        if [[ $# -gt 1 && ! "$2" =~ ^-- ]]; then
          worktree="$2"; shift 2
        else
          worktree="__auto__"; shift
        fi
        ;;
      --worktree-base) worktree_base="$2"; shift 2 ;;
      --force)        force=true; shift ;;
      --format)       format="$2"; shift 2 ;;
      --continue)     do_continue=true; shift ;;
      --resume)       resume_id="$2"; shift 2 ;;
      --raw|--no-extract) extract=false; shift ;;
      --out-dir)      out_dir="$2"; shift 2 ;;
      --out-file)     out_file="$2"; shift 2 ;;
      --)             shift; prompt="$*"; break ;;
      *)              prompt="$*"; break ;;
    esac
  done

  [[ -z "$prompt" ]] && die "未提供 prompt"

  # 落盘路径
  mkdir -p "$out_dir" 2>/dev/null || true
  if [[ -z "$out_file" ]]; then
    local ts
    ts=$(date +%Y%m%d-%H%M%S)
    out_file="${out_dir%/}/cursor-${mode}-${ts}-$$.out"
  fi
  local err_file="${out_file}.err"
  local text_file="${out_file%.out}.txt"

  # 构建命令参数
  local -a cmd_args=("$CURSOR_CMD" "agent" "--print" "--output-format" "$format")

  case "$mode" in
    review) cmd_args+=("--mode" "plan") ;;
    ask)    cmd_args+=("--mode" "ask") ;;
    task)   ;;
    *)      die "未知模式: $mode" ;;
  esac

  [[ -n "$model" ]]     && cmd_args+=("--model" "$model")
  [[ -n "$workspace" ]] && cmd_args+=("--workspace" "$workspace")

  if [[ -n "$worktree" ]]; then
    if [[ "$worktree" == "__auto__" ]]; then
      cmd_args+=("--worktree")
    else
      cmd_args+=("--worktree" "$worktree")
    fi
  fi

  [[ -n "$worktree_base" ]] && cmd_args+=("--worktree-base" "$worktree_base")
  [[ "$force" == true && "$mode" == "task" ]] && cmd_args+=("--force")
  [[ "$do_continue" == true ]] && cmd_args+=("--continue")
  [[ -n "$resume_id" ]]        && cmd_args+=("--resume" "$resume_id")

  cmd_args+=("--trust")
  cmd_args+=("$prompt")

  debug "执行命令: ${cmd_args[*]/%$prompt/[PROMPT_REDACTED]}"
  debug "原始输出落盘: $out_file"

  # 执行：原始输出落盘，不直接透传 stdout
  local exit_code=0
  set +e
  "${cmd_args[@]}" >"$out_file" 2>"$err_file"
  exit_code=$?
  set -e

  local raw_size
  raw_size=$(wc -c < "$out_file" 2>/dev/null | tr -d ' ' || echo 0)
  local err_size
  err_size=$(wc -c < "$err_file" 2>/dev/null | tr -d ' ' || echo 0)

  # 选择回显内容
  if [[ "$extract" == true && ( "$format" == "json" || "$format" == "stream-json" ) ]]; then
    extract_result "$out_file" "$format" >"$text_file" 2>/dev/null || cp "$out_file" "$text_file"
    # 若提炼结果为空，回退到原始
    [[ ! -s "$text_file" ]] && cp "$out_file" "$text_file"
    emit_with_truncation "$text_file" "提炼文本"
  else
    # 原始模式：直接把原始输出按截断规则回显
    text_file=""
    emit_with_truncation "$out_file" "原始输出"
  fi

  # 脚注元信息（供调用方定位完整内容）
  echo ""
  echo "---"
  echo "[cursor-dispatch] mode=${mode} format=${format} extract=${extract} exit=${exit_code}"
  [[ -n "$text_file" ]] && echo "[cursor-dispatch] text file: $text_file"
  echo "[cursor-dispatch] raw  file: $out_file (${raw_size} bytes)"
  if [[ "$err_size" -gt 0 ]]; then
    echo "[cursor-dispatch] stderr   : $err_file (${err_size} bytes)"
  fi

  exit "$exit_code"
}

# ─── 主入口 ─────────────────────────────────────────────
main() {
  [[ $# -lt 1 ]] && usage

  local mode="$1"
  shift

  case "$mode" in
    check)   cmd_check ;;
    review)  build_cursor_cmd "review" "$@" ;;
    task)    build_cursor_cmd "task" "$@" ;;
    ask)     build_cursor_cmd "ask" "$@" ;;
    help|-h|--help) usage ;;
    *)       die "未知模式: $mode — 可用模式: check, review, task, ask" ;;
  esac
}

main "$@"
