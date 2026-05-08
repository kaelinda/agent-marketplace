#!/usr/bin/env bash
# manji-upgrade — Upgrade manji marketplace to latest version
#
# Usage: bash manji-upgrade.sh [--auto]
#
# This script:
# 1. Detects install type (git / vendored)
# 2. Fetches latest code
# 3. Writes upgrade marker
# 4. Shows what's new

set -euo pipefail

MANJI_HOME="${MANJI_HOME:-$HOME/.manji}"
MARKER_FILE="$MANJI_HOME/just-upgraded-from"
REMOTE_REPO="https://github.com/kaelinda/agent-marketplace"

# ── Helpers ────────────────────────────────────────────────────────────

get_local_version() {
  local script_dir
  script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  local version_file="$script_dir/../VERSION"
  if [[ -f "$version_file" ]]; then
    tr -d '[:space:]' < "$version_file"
  else
    echo "0.0.0"
  fi
}

detect_install_type() {
  local script_dir
  script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  local repo_root
  repo_root="$(cd "$script_dir/.." && pwd)"

  if [[ -d "$repo_root/.git" ]]; then
    echo "git"
  else
    echo "vendored"
  fi
}

get_repo_root() {
  local script_dir
  script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  cd "$script_dir/.." && pwd
}

# ── Upgrade Logic ──────────────────────────────────────────────────────

upgrade_git() {
  local repo_root="$1"
  local old_ver="$2"

  echo "Upgrading manji (git install)..."
  cd "$repo_root"

  # Fetch latest
  if ! git fetch origin main 2>/dev/null; then
    echo "ERROR: Failed to fetch from remote" >&2
    return 1
  fi

  # Get remote version before applying
  local remote_ver
  remote_ver=$(git show origin/main:VERSION 2>/dev/null | tr -d '[:space:]') || {
    echo "ERROR: Could not read remote VERSION" >&2
    return 1
  }

  # Apply update
  git reset --hard origin/main 2>/dev/null

  # Write upgrade marker
  mkdir -p "$MANJI_HOME"
  echo "$old_ver" > "$MARKER_FILE"

  echo "✅ Upgraded from $old_ver → $remote_ver"
  show_changelog
}

upgrade_vendored() {
  local repo_root="$1"
  local old_ver="$2"

  echo "Upgrading manji (vendored install)..."

  local tmp_dir
  tmp_dir=$(mktemp -d)
  trap "rm -rf '$tmp_dir'" EXIT

  # Shallow clone latest
  if ! git clone --depth 1 "$REMOTE_REPO" "$tmp_dir/manji-new" 2>/dev/null; then
    echo "ERROR: Failed to clone latest version" >&2
    return 1
  fi

  local remote_ver
  remote_ver=$(tr -d '[:space:]' < "$tmp_dir/manji-new/VERSION") || {
    echo "ERROR: Could not read remote VERSION" >&2
    return 1
  }

  # Backup and swap
  local backup_dir="$repo_root.bak.$(date +%s)"
  cp -r "$repo_root" "$backup_dir"
  rm -rf "$repo_root"
  cp -r "$tmp_dir/manji-new" "$repo_root"

  # Write upgrade marker
  mkdir -p "$MANJI_HOME"
  echo "$old_ver" > "$MARKER_FILE"

  echo "✅ Upgraded from $old_ver → $remote_ver"
  echo "📦 Backup at: $backup_dir"
  show_changelog
}

show_changelog() {
  local repo_root
  repo_root=$(get_repo_root)
  if [[ -f "$repo_root/CHANGELOG.md" ]]; then
    echo ""
    echo "── What's New ──────────────────────────────────"
    head -30 "$repo_root/CHANGELOG.md"
    echo "────────────────────────────────────────────────"
  fi
}

# ── Main ───────────────────────────────────────────────────────────────

main() {
  local old_ver
  old_ver=$(get_local_version)

  local install_type
  install_type=$(detect_install_type)

  case "$install_type" in
    git)
      upgrade_git "$(get_repo_root)" "$old_ver"
      ;;
    vendored)
      upgrade_vendored "$(get_repo_root)" "$old_ver"
      ;;
    *)
      echo "ERROR: Unknown install type: $install_type" >&2
      exit 1
      ;;
  esac
}

main "$@"
