#!/bin/bash
# ============================================================================
# ShopVPN prerequisites for Ubuntu 22.04 / Debian 11+ (disk-aware).
#
# Run this BEFORE the main installer so a slow or failing apt step never
# happens in the middle of the Python/translation install:
#
#   sudo bash preflight.sh            # check + install everything needed
#   bash preflight.sh --check         # only report what is missing (no changes)
#   sudo bash preflight.sh --with-web # also install nginx + certbot (webhook)
#
# It is safe and idempotent: running it twice changes nothing.
# ============================================================================
set -euo pipefail

WITH_WEB=0
CHECK_ONLY=0
for arg in "$@"; do
  case "$arg" in
    --check) CHECK_ONLY=1 ;;
    --with-web) WITH_WEB=1 ;;
    -h|--help)
      grep '^#' "$0" | sed 's/^# \{0,1\}//'
      exit 0 ;;
  esac
done

export DEBIAN_FRONTEND=noninteractive
export NEEDRESTART_MODE=a
export NEEDRESTART_SUSPEND=1

RED=$'\033[31m'; GREEN=$'\033[32m'; YELLOW=$'\033[33m'; CYAN=$'\033[36m'; RESET=$'\033[0m'

as_root() {
  if [ "$(id -u)" -eq 0 ]; then "$@";
  elif command -v sudo >/dev/null 2>&1; then sudo "$@";
  else echo "${RED}Root privileges are required. Re-run with sudo.${RESET}" >&2; exit 1; fi
}

echo "${CYAN}== ShopVPN preflight =="

# --- Operating system ------------------------------------------------------
if [ -r /etc/os-release ]; then
  # shellcheck disable=SC1091
  . /etc/os-release
  echo "OS: ${PRETTY_NAME:-unknown}"
  case "${ID:-}" in
    ubuntu|debian) : ;;
    *) echo "${YELLOW}! Tested on Ubuntu/Debian; '${ID:-?}' may need manual package names.${RESET}" ;;
  esac
else
  echo "${YELLOW}! /etc/os-release missing; assuming a Debian-like system.${RESET}"
fi

# --- Disk space ------------------------------------------------------------
# The lean installer needs roughly 1 GB (Python venv + a couple of Argos
# models). The old LibreTranslate path needed 6-16 GB. Warn early on a tiny disk.
AVAIL_MB=$(df -Pm / 2>/dev/null | awk 'NR==2{print $4}')
AVAIL_H=$(df -Ph / 2>/dev/null | awk 'NR==2{print $4}')
echo "Free disk on /: ${AVAIL_H:-?}"
if [ -n "${AVAIL_MB:-}" ]; then
  if [ "$AVAIL_MB" -lt 1200 ]; then
    echo "${RED}✗ Less than ~1.2 GB free. Free space before installing (see docs/disk usage).${RESET}"
  elif [ "$AVAIL_MB" -lt 2500 ]; then
    echo "${YELLOW}! Free space is low for growth (logs/backups). Aim for 2 GB+.${RESET}"
  else
    echo "${GREEN}✓ Disk space is sufficient for the lean install.${RESET}"
  fi
fi

# --- Python version --------------------------------------------------------
if command -v python3 >/dev/null 2>&1; then
  PYV=$(python3 -c 'import sys; print("%d.%d"%sys.version_info[:2])')
  echo "Python: $PYV"
  python3 - <<'PY' || echo "${YELLOW}! Python 3.10+ is required; install a newer python3.${RESET}"
import sys
raise SystemExit(0 if sys.version_info >= (3, 10) else 1)
PY
else
  echo "${YELLOW}! python3 is not installed yet (it will be installed below).${RESET}"
fi

# --- Package lists ---------------------------------------------------------
# Base runtime + build fallbacks so every wheel compiles even on minimal images.
PKGS_BASE="git curl ca-certificates python3 python3-pip python3-venv \
build-essential python3-dev pkg-config libffi-dev libssl-dev zlib1g-dev libjpeg-dev"
PKGS_WEB="nginx certbot python3-certbot-nginx"

MISSING=()
for p in $PKGS_BASE; do
  dpkg -s "$p" >/dev/null 2>&1 || MISSING+=("$p")
done
if [ "$WITH_WEB" = "1" ]; then
  for p in $PKGS_WEB; do
    dpkg -s "$p" >/dev/null 2>&1 || MISSING+=("$p")
  done
fi

if [ "${#MISSING[@]}" -eq 0 ]; then
  echo "${GREEN}✓ All required packages are already installed.${RESET}"
else
  echo "Missing packages: ${MISSING[*]}"
fi

if [ "$CHECK_ONLY" = "1" ]; then
  echo "${CYAN}--check mode: no changes made.${RESET}"
  exit 0
fi

if [ "${#MISSING[@]}" -gt 0 ] && command -v apt-get >/dev/null 2>&1; then
  echo "Installing prerequisites (apt)..."
  as_root apt-get update -qq
  as_root apt-get install -y -qq "${MISSING[@]}" >/dev/null
fi

# --- Summary ---------------------------------------------------------------
echo
echo "${GREEN}Preflight complete.${RESET} Next step: the one-line ShopVPN install command."
echo "  git:     $(command -v git || echo MISSING)"
echo "  python3: $(command -v python3 || echo MISSING) ${PYV:-}"
echo "  pip:     $(python3 -m pip --version 2>/dev/null | cut -d' ' -f1-2 || echo MISSING)"
