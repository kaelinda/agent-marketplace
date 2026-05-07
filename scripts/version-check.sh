#!/usr/bin/env bash
# manji-update-check — Version update checker for manji marketplace
# Inspired by gstack's update checking mechanism
#
# Usage: bash version-check.sh [--force]
#
# Output (to stdout):
#   UPGRADE_AVAILABLE <local_ver> <remote_ver>
#   UP_TO_DATE
#   (nothing — check skipped due to cache/snooze/disabled)
#
# Exit codes:
#   0 — check completed (result on stdout)
#   1 — error (network, missing files, etc.)

set -euo pipefail

# ── Paths ──────────────────────────────────────────────────────────────
MANJI_HOME="${MANJI_HOME:-$HOME/.manji}"
CACHE_FILE="$MANJI_HOME/last-update-check"
SNOOZE_FILE="$MANJI_HOME/update-snoozed"
CONFIG_FILE="$MANJI_HOME/config.json"

# ── Defaults ───────────────────────────────────────────────────────────
UP_TO_DATE_TTL=60        # minutes — how long to cache "up to date" result
UPGRADE_AVAILABLE_TTL=720 # minutes — how long to cache "upgrade available" (12h)
REMOTE_VERSION_URL="https://raw.githubusercontent.com/kaelinda/agent-marketplace/main/VERSION"
FETCH_TIMEOUT=5          # seconds

# ── Helpers ────────────────────────────────────────────────────────────

ensure_dir() {
  mkdir -p "$MANJI_HOME"
}

# Read a simple JSON boolean value from config (returns 0=true, 1=false)
config_is_true() {
  local key="$1"
  [[ -f "$CONFIG_FILE" ]] || return 1
  python3 -c "
import json, sys
try:
    cfg = json.load(open('$CONFIG_FILE'))
    val = cfg.get('$key', False)
    sys.exit(0 if val else 1)
except:
    sys.exit(1)
" 2>/dev/null
}

# Read local version from the installed marketplace
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

# Fetch remote version from GitHub
get_remote_version() {
  curl -fsSL --max-time "$FETCH_TIMEOUT" "$REMOTE_VERSION_URL" 2>/dev/null | tr -d '[:space:]'
}

# Compare semver: returns 0 if $1 < $2
ver_lt() {
  [ "$(printf '%s\n' "$1" "$2" | sort -V | head -n1)" = "$1" ] && [ "$1" != "$2" ]
}

# Check if cache is still fresh
cache_is_fresh() {
  local ttl_minutes="$1"
  [[ -f "$CACHE_FILE" ]] || return 1
  # find -mtime checks file age; we store result + version in cache
  if command -v gfind &>/dev/null; then
    gfind "$CACHE_FILE" -mmin -"$ttl_minutes" -print -quit | grep -q .
  else
    find "$CACHE_FILE" -mmin -"$ttl_minutes" -print -quit 2>/dev/null | grep -q .
  fi
}

# Read cached version from cache file
get_cached_version() {
  [[ -f "$CACHE_FILE" ]] && tail -1 "$CACHE_FILE" | awk '{print $NF}' || echo ""
}

# Write cache entry
write_cache() {
  local status="$1" version="$2"
  ensure_dir
  echo "$status $version" > "$CACHE_FILE"
}

# Check snooze state: returns 0 if snoozed, 1 if not
is_snoozed() {
  [[ -f "$SNOOZE_FILE" ]] || return 1

  local snooze_data
  snooze_data=$(cat "$SNOOZE_FILE" 2>/dev/null) || return 1

  local snoozed_version snooze_until
  snoozed_version=$(echo "$snooze_data" | awk '{print $1}')
  snooze_until=$(echo "$snooze_data" | awk '{print $3}')

  local now
  now=$(date +%s)

  # If snooze expired, remove it
  if [[ "$now" -ge "$snooze_until" ]]; then
    rm -f "$SNOOZE_FILE"
    return 1
  fi

  # If the snoozed version matches current local, still snoozed
  local local_ver
  local_ver=$(get_local_version)
  [[ "$snoozed_version" == "$local_ver" ]]
}

# Write snooze state with escalating backoff
write_snooze() {
  local current_level=0
  if [[ -f "$SNOOZE_FILE" ]]; then
    current_level=$(awk '{print $2}' "$SNOOZE_FILE" 2>/dev/null || echo "0")
  fi

  local new_level=$((current_level + 1))
  local hours
  case 1 in
    $(( new_level <= 1 ))) hours=24 ;;
    $(( new_level <= 2 ))) hours=48 ;;
    *) hours=168 ;;  # 7 days cap
  esac

  local now
  now=$(date +%s)
  local snooze_until=$((now + hours * 3600))
  local local_ver
  local_ver=$(get_local_version)

  ensure_dir
  echo "$local_ver $new_level $snooze_until" > "$SNOOZE_FILE"
  echo "$hours"
}

# ── Main Logic ─────────────────────────────────────────────────────────

main() {
  local force=false
  [[ "${1:-}" == "--force" ]] && force=true

  # Config kill switch
  if config_is_true "update_check_disabled"; then
    exit 0
  fi

  # Auto-upgrade mode — skip interactive, just output status
  local auto_upgrade=false
  config_is_true "auto_upgrade" 2>/dev/null && auto_upgrade=true

  local local_ver
  local_ver=$(get_local_version)

  # Check snooze (unless forced)
  if ! $force && is_snoozed; then
    exit 0
  fi

  # Check cache freshness
  if ! $force; then
    if cache_is_fresh "$UP_TO_DATE_TTL"; then
      local cached_ver
      cached_ver=$(get_cached_version)
      if [[ "$cached_ver" == "$local_ver" ]]; then
        # Cache says up-to-date and still fresh
        exit 0
      fi
    fi

    # For "upgrade available" we use a longer TTL
    if [[ -f "$CACHE_FILE" ]] && grep -q "UPGRADE_AVAILABLE" "$CACHE_FILE" 2>/dev/null; then
      if cache_is_fresh "$UPGRADE_AVAILABLE_TTL"; then
        local cached_ver
        cached_ver=$(get_cached_version)
        if [[ "$cached_ver" != "$local_ver" ]]; then
          # Still showing upgrade available for the same remote version
          local remote_ver
          remote_ver=$(awk '{print $NF}' "$CACHE_FILE")
          echo "UPGRADE_AVAILABLE $local_ver $remote_ver"
          exit 0
        fi
      fi
    fi
  fi

  # Fetch remote version (slow path)
  local remote_ver
  remote_ver=$(get_remote_version) || {
    # Network error — silently skip
    exit 0
  }

  if [[ -z "$remote_ver" ]]; then
    exit 0
  fi

  # Compare versions
  if ver_lt "$local_ver" "$remote_ver"; then
    write_cache "UPGRADE_AVAILABLE" "$remote_ver"
    echo "UPGRADE_AVAILABLE $local_ver $remote_ver"
  else
    write_cache "UP_TO_DATE" "$local_ver"
    # Remove snooze if we're up to date
    rm -f "$SNOOZE_FILE" 2>/dev/null
  fi
}

main "$@"
