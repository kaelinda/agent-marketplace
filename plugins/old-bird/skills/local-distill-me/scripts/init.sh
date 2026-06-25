#!/usr/bin/env bash
#
# local-distill-me / init.sh
# 把 "CLAUDE.local.md 共享规则体系" 移植到一个项目，并软链所有 git worktree。
#
# 用法:
#   init.sh [<slug>] [<project-root>]
#     <slug>          共享规则目录名，默认 = 项目目录 basename
#     <project-root>  项目根目录，默认 = 当前目录 (pwd)
#
# 幂等：重复运行不会破坏已有内容；已正确软链的 worktree 会跳过。
# 不会 commit 任何东西；只改 worktree 内的 CLAUDE.local.md(软链) 与 .gitignore。
set -euo pipefail

SHARED_ROOT="$HOME/.claude/shared"
COMMON_DIR="$SHARED_ROOT/_common"
TEMPLATE_DIR="$SHARED_ROOT/_template"

# 自举：_common/_template 缺失时，从 skill 自带 assets/ 拷一份（便于换机复现）
SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
bootstrap_shared() {
  local name="$1" dst="$2"
  [ -d "$dst" ] && return 0
  if [ -d "$SKILL_DIR/assets/$name" ]; then
    mkdir -p "$dst"
    cp -R "$SKILL_DIR/assets/$name/." "$dst/"
    echo "  [bootstrap] 从 skill assets 还原 $name → $dst"
  else
    echo "  [warn] 缺少 $dst 且 skill assets 里也没有 $name，跳过（请先手工准备 _common/_template）"
  fi
}
bootstrap_shared "_common"   "$COMMON_DIR"
bootstrap_shared "_template" "$TEMPLATE_DIR"

# ---- 入参 ----
ROOT="${2:-$(pwd)}"
ROOT="$(cd "$ROOT" && pwd)"          # 规整为绝对路径
SLUG="${1:-$(basename "$ROOT")}"
SLUG="${SLUG//\//-}"                  # slug 不允许带斜杠

PROJ_DIR="$SHARED_ROOT/$SLUG"
AUTH_INDEX="$PROJ_DIR/CLAUDE.local.md"   # 权威索引（worktree 软链到这）

echo "== local-distill-me =="
echo "  slug         : $SLUG"
echo "  project root : $ROOT"
echo "  shared dir   : $PROJ_DIR"
echo

# ---- 1. 共享规则目录脚手架 ----
mkdir -p "$PROJ_DIR/project-rules"

render() {  # render <tmpl> <dst>  —— 只在 dst 不存在时渲染，保护用户后续编辑
  local tmpl="$1" dst="$2"
  if [ -f "$dst" ]; then
    echo "  [skip] 已存在: ${dst#$HOME/}"
  elif [ -f "$tmpl" ]; then
    sed "s/{{PROJECT}}/$SLUG/g" "$tmpl" > "$dst"
    echo "  [new ] ${dst#$HOME/}"
  fi
}

if [ -d "$TEMPLATE_DIR/project-rules" ]; then
  for tmpl in "$TEMPLATE_DIR"/project-rules/*.tmpl; do
    [ -e "$tmpl" ] || continue
    base="$(basename "$tmpl" .tmpl)"      # commit-preflight.md.tmpl -> commit-preflight.md
    render "$tmpl" "$PROJ_DIR/project-rules/$base"
  done
fi

# personal.md 空桩（避免 @import 悬空）
if [ ! -f "$PROJ_DIR/personal.md" ]; then
  printf '# personal.md（%s 跨 worktree 私有，不入 git）\n\n<在这里写只属于你自己的、不入库的项目笔记>\n' "$SLUG" > "$PROJ_DIR/personal.md"
  echo "  [new ] ${PROJ_DIR#$HOME/}/personal.md"
fi

# 权威索引
render "$TEMPLATE_DIR/CLAUDE.local.md.tmpl" "$AUTH_INDEX"
if [ ! -f "$AUTH_INDEX" ]; then
  echo "  [error] 未能生成权威索引 $AUTH_INDEX（模板缺失？）" >&2
  exit 1
fi
echo

# ---- 2. 发现 worktree ----
echo "== 软链 worktree =="
worktrees=()
if git -C "$ROOT" rev-parse --git-dir >/dev/null 2>&1; then
  while IFS= read -r wt; do
    [ -n "$wt" ] && worktrees+=("$wt")
  done < <(git -C "$ROOT" worktree list --porcelain 2>/dev/null | awk '/^worktree /{sub(/^worktree /,""); print}')
fi
# 非 git 仓库 / 无 worktree 时，至少处理项目根目录本身
if [ "${#worktrees[@]}" -eq 0 ]; then
  worktrees=("$ROOT")
  echo "  (非 git worktree 仓库，只处理根目录)"
fi

ts="$(date +%Y%m%d%H%M%S)"
for wt in "${worktrees[@]}"; do
  [ -d "$wt" ] || { echo "  [miss] worktree 不存在: $wt"; continue; }
  link="$wt/CLAUDE.local.md"

  if [ -L "$link" ]; then
    cur="$(readlink "$link")"
    if [ "$cur" = "$AUTH_INDEX" ]; then
      echo "  [ok  ] 已软链: $wt"
    else
      ln -sfn "$AUTH_INDEX" "$link"
      echo "  [fix ] 重指软链: $wt (原 → $cur)"
    fi
  elif [ -e "$link" ]; then
    mv "$link" "$link.bak.$ts"
    ln -s "$AUTH_INDEX" "$link"
    echo "  [link] 原文件备份为 CLAUDE.local.md.bak.$ts 并软链: $wt"
  else
    ln -s "$AUTH_INDEX" "$link"
    echo "  [link] 新建软链: $wt"
  fi

  # .gitignore 确保忽略软链与备份
  gi="$wt/.gitignore"
  if ! { [ -f "$gi" ] && grep -qxF "CLAUDE.local.md" "$gi"; }; then
    {
      printf '\n# Claude private rules index (symlink -> ~/.claude/shared/%s/)\n' "$SLUG"
      printf 'CLAUDE.local.md\n'
      printf 'CLAUDE.local.md.bak.*\n'
    } >> "$gi"
    echo "         ↳ 已向 .gitignore 追加 CLAUDE.local.md（这是 tracked 改动，记得提交该行）"
  fi
done

echo
echo "== 完成 =="
echo "权威索引: ${AUTH_INDEX#$HOME/}"
echo "项目规则: ${PROJ_DIR#$HOME/}/project-rules/  (去填 commit-preflight.md / business-summary.md 等骨架)"
