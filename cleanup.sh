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

# --- 1. pip caches (the biggest silent hog) --------------------------------
for py in "$INSTALL_DIR/venv/bin/python3" "$INSTALL_DIR/translation-venv/bin/python3"; do
  [ -x "$py" ] && "$py" -m pip cache purge >/dev/null 2>&1 || true
done
rm -rf "$HOME/.cache/pip" 2>/dev/null || true
if [ "$(id -u)" -eq 0 ]; then rm -rf /root/.cache/pip 2>/dev/null || true; fi

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
rm -rf "$HOME/.local/cache/argos-translate" 2>/dev/null || true
if [ "$(id -u)" -eq 0 ]; then rm -rf /root/.local/cache/argos-translate 2>/dev/null || true; fi

# --- 5. leftover pip temp dirs --------------------------------------------
rm -rf /tmp/pip-* /tmp/pip_build_* /tmp/pip-unpack-* 2>/dev/null || true

# --- Report ----------------------------------------------------------------
AFTER_MB=$(df -Pm / 2>/dev/null | awk 'NR==2{print $4}')
echo "  venv:             $(human "$INSTALL_DIR/venv")"
echo "  translation-venv: $(human "$INSTALL_DIR/translation-venv")"
echo "  Argos models:     $(human "$HOME/.local/share/argos-translate")"
if [ -n "${BEFORE_MB:-}" ] && [ -n "${AFTER_MB:-}" ]; then
  FREED=$(( AFTER_MB - BEFORE_MB ))
  [ "$FREED" -lt 0 ] && FREED=0
  echo "${GREEN}  ✓ freed ~${FREED} MB (free on /: $((AFTER_MB/1024)) GB)${RESET}"
else
  echo "${GREEN}  ✓ cleanup done${RESET}"
fi
echo "${YELLOW}  kept: venv, .env, databases, backups, logs, installed language models${RESET}"
