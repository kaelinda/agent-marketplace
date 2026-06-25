#!/usr/bin/env bash
#
# local-distill-me / install-hook.sh
# 安装 git post-checkout 钩子：新建 worktree（或检出）时，若本 worktree 缺
# CLAUDE.local.md 软链则自动补上。这样新建 worktree 零手动。
#
# 用法: install-hook.sh <slug> <repo-root>
#
# 钩子是项目级 .git 配置：不入库、不影响协作者、所有 worktree 共享同一份。
# 安全策略：core.hooksPath 被重定向（husky 等）或已存在他人的 post-checkout 时，
#           不自动改写，改为打印片段让用户手动加。
set -euo pipefail

SLUG="${1:?用法: install-hook.sh <slug> <repo-root>}"
ROOT="${2:-$(pwd)}"
ROOT="$(cd "$ROOT" && pwd)"

MARKER_OPEN="# >>> local-distill-me auto-symlink >>>"
MARKER_CLOSE="# <<< local-distill-me auto-symlink <<<"

emit_block() {   # 钩子主体（不含 shebang）；$HOME 留到钩子运行时再展开
  echo "$MARKER_OPEN"
  echo '# 新建 worktree / 检出时，若本 worktree 缺 CLAUDE.local.md 软链则补上。由 local-distill-me 生成。'
  printf '__ldm_auth="$HOME/.claude/shared/%s/CLAUDE.local.md"\n' "$SLUG"
  cat <<'EOF'
__ldm_root="$(git rev-parse --show-toplevel 2>/dev/null)"
if [ -n "$__ldm_root" ] && [ -f "$__ldm_auth" ] && [ ! -e "$__ldm_root/CLAUDE.local.md" ]; then
  ln -s "$__ldm_auth" "$__ldm_root/CLAUDE.local.md"
fi
EOF
  echo "$MARKER_CLOSE"
}

# ---- 校验 ----
AUTH="$HOME/.claude/shared/$SLUG/CLAUDE.local.md"
[ -f "$AUTH" ] || { echo "[error] 权威索引不存在：${AUTH/#$HOME/\~} —— 先跑 init.sh <slug> <root>" >&2; exit 1; }
git -C "$ROOT" rev-parse --git-dir >/dev/null 2>&1 || { echo "[error] $ROOT 不是 git 仓库" >&2; exit 1; }

# ---- core.hooksPath 重定向（husky 等）→ 不自动写 ----
hp="$(git -C "$ROOT" config --get core.hooksPath || true)"
if [ -n "$hp" ]; then
  echo "[skip] 仓库设置了 core.hooksPath=$hp（可能是 husky 等），不自动安装以免改到受版本控制的钩子目录。"
  echo "       手动把下面这段加进你的 post-checkout 钩子即可："
  echo "----8<----"; emit_block; echo "---->8----"
  exit 2
fi

# ---- 共享 hooks 目录（所有 worktree 共用主仓库 .git/hooks）----
HOOKS_DIR="$(cd "$ROOT" && cd "$(git rev-parse --git-common-dir)" && pwd)/hooks"
mkdir -p "$HOOKS_DIR"
HOOK="$HOOKS_DIR/post-checkout"

if [ -f "$HOOK" ]; then
  if grep -qF "$MARKER_OPEN" "$HOOK"; then
    echo "[ok] 钩子已安装，跳过：${HOOK/#$HOME/\~}"
    exit 0
  fi
  echo "[skip] 已存在 post-checkout 钩子（非本工具），不自动改写：${HOOK/#$HOME/\~}"
  echo "       手动把下面这段加到它末尾："
  echo "----8<----"; emit_block; echo "---->8----"
  exit 2
fi

{ echo '#!/usr/bin/env bash'; emit_block; } > "$HOOK"
chmod +x "$HOOK"
echo "[new] 已安装 post-checkout 钩子 → ${HOOK/#$HOME/\~}"
echo "      以后新建 worktree 会自动软链 CLAUDE.local.md（项目级 .git 配置，不入库、不影响协作者）"
