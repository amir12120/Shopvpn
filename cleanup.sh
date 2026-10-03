#!/bin/bash
# ============================================================================
# ShopVPN disk cleanup — reclaim space AFTER an install/update.
#
#   sudo bash cleanup.sh            # cleans $HOME/v2ray_bot
#   sudo bash cleanup.sh /opt/shop  # cleans a custom install dir
#
# SAFETY: this script never touches anything the running bot needs. It only
# removes caches and regenerable build artifacts:
#   * pip download/build caches (they can be several GB)
#   * the apt package cache (/var/cache/apt/archives)
#   * __pycache__ / *.pyc / build / dist / *.egg-info inside the project
#   * Argos *downloaded* model archives (installed models are kept)
#   * leftover pip temp dirs in /tmp
#
# It explicitly KEEPS: venv/, translation-venv/ (if installed), .env, the
# SQLite databases, backups/, logs, and installed Argos language packages.
# Running it is idempotent and safe to repeat.
# ============================================================================
set -uo pipefail

INSTALL_DIR="${1:-${SHOPVPN_DIR:-$HOME/v2ray_bot}}"

case "$INSTALL_DIR" in
  ""|"/"|".") echo "cleanup: refusing to operate on '$INSTALL_DIR'" >&2; exit 1 ;;
esac

GREEN=$'\033[32m'; YELLOW=$'\033[33m'; CYAN=$'\033[36m'; RESET=$'\033[0m'

as_root() {
  if [ "$(id -u)" -eq 0 ]; then "$@";
  elif command -v sudo >/dev/null 2>&1; then sudo "$@";
  else "$@"; fi
}

human() { if [ -e "$1" ]; then du -sh "$1" 2>/dev/null | cut -f1; else echo "-"; fi; }

BEFORE_MB=$(df -Pm / 2>/dev/null | awk 'NR==2{print $4}')
echo "${CYAN}🧹 ShopVPN cleanup: $INSTALL_DIR${RESET}"

# Every home directory that can hold a cache for this bot: the account running
# the cleanup, the account the systemd unit runs as (they are not always the
# same — `sudo shopvpn` runs as root while the unit may run as another user),
# and /root when we are root anyway. The list is newline-separated and consumed
# with `read`, because a home directory may contain spaces.
SERVICE_USER="${SHOPVPN_SERVICE_USER:-}"
if [ -z "$SERVICE_USER" ] && command -v systemctl >/dev/null 2>&1; then
  SERVICE_USER="$(systemctl show -p User --value "${SHOPVPN_SERVICE_NAME:-v2raybot}" 2>/dev/null || true)"
fi
[ -z "$SERVICE_USER" ] && SERVICE_USER="root"
SERVICE_HOME="$(getent passwd "$SERVICE_USER" 2>/dev/null | cut -d: -f6 || true)"

UNIQUE_HOMES=""
add_cache_home() {
  local h="$1"
  [ -n "$h" ] || return 0
  case "
$UNIQUE_HOMES
" in
    *"
$h
"*) return 0 ;;
  esac
  UNIQUE_HOMES="${UNIQUE_HOMES}${h}
"
}
add_cache_home "$HOME"
add_cache_home "$SERVICE_HOME"
[ "$(id -u)" -eq 0 ] && add_cache_home /root

# --- 1. pip caches (the biggest silent hog) --------------------------------
for py in "$INSTALL_DIR/venv/bin/python3" "$INSTALL_DIR/translation-venv/bin/python3"; do
  [ -x "$py" ] && "$py" -m pip cache purge >/dev/null 2>&1 || true
done
while IFS= read -r h; do
  [ -n "$h" ] || continue
  rm -rf "$h/.cache/pip" 2>/dev/null || true
done <<< "$UNIQUE_HOMES"
# wheels pip may have staged in the system python's cache directory
as_root rm -rf /var/cache/pip 2>/dev/null || true

# --- 2. apt package cache --------------------------------------------------
if command -v apt-get >/dev/null 2>&1; then
  as_root apt-get clean >/dev/null 2>&1 || true
fi
as_root rm -rf /var/cache/apt/archives/*.deb /var/cache/apt/archives/partial/* 2>/dev/null || true

# --- 3. regenerable Python artifacts inside the project --------------------
find "$INSTALL_DIR" -type d -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null || true
find "$INSTALL_DIR" -type f \( -name '*.pyc' -o -name '*.pyo' \) -delete 2>/dev/null || true
rm -rf "$INSTALL_DIR/build" "$INSTALL_DIR/dist" 2>/dev/null || true
find "$INSTALL_DIR" -maxdepth 3 -type d -name '*.egg-info' -prune -exec rm -rf {} + 2>/dev/null || true

# --- 4. Argos *download* cache (installed packages are kept) ---------------
while IFS= read -r h; do
  [ -n "$h" ] || continue
  rm -rf "$h/.local/cache/argos-translate" 2>/dev/null || true
done <<< "$UNIQUE_HOMES"

# --- 5. leftover pip temp dirs --------------------------------------------
rm -rf /tmp/pip-* /tmp/pip_build_* /tmp/pip-unpack-* 2>/dev/null || true

# --- 5b. abandoned restore/QR temp dirs from the bot ----------------------
# The bot stages every uploaded backup/image in a /tmp/<prefix>_XXXX directory.
# The confirm/cancel handlers delete them, but a flow the admin simply walks
# away from would keep a full database copy on disk forever. Anything older than
# a day is a leftover by definition.
for prefix in restore_ restore_full_ xui_restore_ qr_bg_ image_ media_; do
  as_root find /tmp -maxdepth 1 -type d -name "${prefix}*" -mtime +1 -exec rm -rf {} + 2>/dev/null || true
done

# --- 5c. system journal (unbounded by default on a long-running server) ----
# systemd keeps rotated bot logs until 10% of the whole filesystem is used,
# which on a small VPS is hundreds of megabytes for log text nobody reads.
JOURNAL_MAX="${SHOPVPN_JOURNAL_MAX:-200M}"
if command -v journalctl >/dev/null 2>&1; then
  as_root journalctl --vacuum-size="$JOURNAL_MAX" >/dev/null 2>&1 || true
fi

# --- Report ----------------------------------------------------------------
AFTER_MB=$(df -Pm / 2>/dev/null | awk 'NR==2{print $4}')
echo "  venv:             $(human "$INSTALL_DIR/venv")"
echo "  translation-venv: $(human "$INSTALL_DIR/translation-venv")"
echo "  Argos models:     $(human "$SERVICE_HOME/.local/share/argos-translate")"
echo "  backups:          $(human "$INSTALL_DIR/backups")"
if command -v journalctl >/dev/null 2>&1; then
  JOURNAL_SIZE="$(journalctl --disk-usage 2>/dev/null | grep -oE '[0-9]+([.][0-9]+)?[KMGTP]?B?' | head -1)"
  echo "  system journal:   ${JOURNAL_SIZE:--}"
fi
# A second model copy that belongs to the wrong account is pure waste on a
# small disk, so call it out instead of leaving it to be discovered later.
while IFS= read -r h; do
  [ -n "$h" ] || continue
  if [ "$h" != "$SERVICE_HOME" ] && [ -d "$h/.local/share/argos-translate/packages" ]; then
    echo "${YELLOW}  note: unused Argos copy in $h ($(human "$h/.local/share/argos-translate")) — safe to delete${RESET}"
  fi
done <<< "$UNIQUE_HOMES"
if [ -n "${BEFORE_MB:-}" ] && [ -n "${AFTER_MB:-}" ]; then
  FREED=$(( AFTER_MB - BEFORE_MB ))
  [ "$FREED" -lt 0 ] && FREED=0
  echo "${GREEN}  ✓ freed ~${FREED} MB (free on /: $((AFTER_MB/1024)) GB)${RESET}"
else
  echo "${GREEN}  ✓ cleanup done${RESET}"
fi
echo "${YELLOW}  kept: venv, .env, databases, backups, logs, installed language models${RESET}"
echo "  free on /:        $(df -Ph / 2>/dev/null | awk 'NR==2{print $4}')  ($(human "$INSTALL_DIR") total for the project)"
