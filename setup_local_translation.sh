#!/bin/bash
# ============================================================================
# Disk-aware local translation setup for ShopVPN.
#
# The previous version installed LibreTranslate (PyTorch + CTranslate2 + a
# second copy of every language model) on every server. A default
# LibreTranslate install is several gigabytes (its full image is ~16 GB) and
# routinely fails outright on a VPS with "only" a few GB free. Argos Translate
# alone already provides the fully offline translation ShopVPN needs, and the
# app treats LibreTranslate purely as a *second* fallback (provider order is
# "argos,libretranslate" and Argos is tried first).
#
# So this script now defaults to the lean path:
#   * install Argos Translate only,
#   * download only the language pairs the shop actually uses,
#   * never keep pip's download cache,
#   * leave LibreTranslate off unless you explicitly opt in.
#
# Knobs (all optional):
#   SHOPVPN_TRANSLATION_LANGS=fa,tr,ar   extra target languages to preload
#   SHOPVPN_TRANSLATION_LANGS=all        preload every language in the catalog
#   SHOPVPN_INSTALL_LIBRETRANSLATE=1     also install the heavy LibreTranslate
#   SHOPVPN_SKIP_MODELS=1                skip model downloads entirely
# ============================================================================
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="${VENV_DIR:-$ROOT_DIR/venv}"
TRANSLATION_VENV_DIR="${TRANSLATION_VENV_DIR:-$ROOT_DIR/translation-venv}"
PYTHON_BIN="${PYTHON_BIN:-$VENV_DIR/bin/python3}"
LT_PYTHON="${LT_PYTHON:-$TRANSLATION_VENV_DIR/bin/python3}"

INSTALL_LIBRETRANSLATE="${SHOPVPN_INSTALL_LIBRETRANSLATE:-0}"
SKIP_MODELS="${SHOPVPN_SKIP_MODELS:-0}"
LANGS_SPEC="${SHOPVPN_TRANSLATION_LANGS:-fa}"

# Never let pip keep gigabytes of downloaded wheels around: this is one of the
# biggest silent disk hogs on small VPS disks.
export PIP_NO_CACHE_DIR=1
export PIP_DISABLE_PIP_VERSION_CHECK=1
export PYTHONUNBUFFERED=1

as_root() {
  if [ "$(id -u)" -eq 0 ]; then
    "$@"
  elif command -v sudo >/dev/null 2>&1; then
    sudo "$@"
  else
    echo "ERROR: root privileges are required to install system packages." >&2
    exit 1
  fi
}

pip_q() {
  # pip_q <python> <args...>  -> quiet, cache-less install
  "$1" -m pip install -q --no-cache-dir --disable-pip-version-check "${@:2}"
}

human() { if [ -e "$1" ]; then du -sh "$1" 2>/dev/null | cut -f1; else echo "-"; fi; }

install_system_prereqs() {
  if command -v apt-get >/dev/null 2>&1; then
    echo "[translation] Installing system prerequisites..."
    as_root env DEBIAN_FRONTEND=noninteractive apt-get update -qq
    as_root env DEBIAN_FRONTEND=noninteractive apt-get install -y -qq \
      python3 python3-pip python3-venv ca-certificates curl >/dev/null
  elif ! command -v python3 >/dev/null 2>&1; then
    echo "ERROR: python3 is required on this operating system." >&2
    exit 1
  fi
}

install_system_prereqs

if [ ! -x "$PYTHON_BIN" ]; then
  echo "[translation] Creating Python virtual environment..."
  python3 -m venv "$VENV_DIR"
fi

pip_q "$PYTHON_BIN" --upgrade pip setuptools wheel
# argostranslate -> stanza -> torch. Prefer the CPU-only build so we don't pull
# ~5 GB of CUDA/nvidia libraries onto a small VPS.
if ! pip_q "$PYTHON_BIN" --index-url https://download.pytorch.org/whl/cpu torch; then
  echo "[translation] Warning: CPU-only torch install failed; continuing." >&2
fi
pip_q "$PYTHON_BIN" 'argostranslate>=1.11.0'

# ---------------------------------------------------------------------------
# Decide which language pairs to preload.
#   * fa (default)  -> en->fa and fa->en only (~200 MB): enough for the
#                      Persian/English shop UI and the admin panel.
#   * a CSV list    -> those targets as well (e.g. "tr,ar,ru").
#   * all           -> every language in the project catalog (~1.5 GB+).
# Anything not preloaded still works later via:
#   SHOPVPN_TRANSLATION_LANGS=... bash setup_local_translation.sh
# ---------------------------------------------------------------------------
TARGETS=()
if [ "$SKIP_MODELS" != "1" ]; then
  if [ "$LANGS_SPEC" = "all" ]; then
    mapfile -t TARGETS < <(SHOPVPN_ROOT="$ROOT_DIR" "$PYTHON_BIN" - <<'PY'
import os
import sys
sys.path.insert(0, os.environ["SHOPVPN_ROOT"])
try:
    from i18n import LANGUAGE_CATALOG
except Exception:
    print("fa")
    raise SystemExit(0)
for code in sorted(LANGUAGE_CATALOG):
    if code not in {"en", "fa"}:
        print(code)
PY
)
  else
    IFS=',' read -r -a _raw <<< "$LANGS_SPEC"
    for _lang in "${_raw[@]}"; do
      _lang="$(echo "$_lang" | tr -d '[:space:]')"
      [ -z "$_lang" ] && continue
      [ "$_lang" = "en" ] && continue
      [ "$_lang" = "fa" ] && continue
      TARGETS+=("$_lang")
    done
  fi
fi

install_pair() {
  local pair="$1"
  echo "[translation] Installing Argos model: $pair"
  if ! "$VENV_DIR/bin/argospm" install "translate-${pair}"; then
    echo "[translation] Warning: model translate-${pair} is unavailable; continuing." >&2
  fi
}

if [ "$SKIP_MODELS" = "1" ]; then
  echo "[translation] SHOPVPN_SKIP_MODELS=1 -> skipping model downloads."
else
  # Argos package metadata is public/open and does not require an API key.
  "$VENV_DIR/bin/argospm" update

  # en -> fa is what the Persian UI needs; fa -> en completes the admin panel,
  # which can contain raw Persian strings.
  install_pair "en_fa"
  install_pair "fa_en"
  for lang in "${TARGETS[@]}"; do
    [ "$lang" = "fa" ] && continue
    install_pair "en_${lang}"
  done
fi

# ---------------------------------------------------------------------------
# Optional: LibreTranslate fallback (heavy). Off by default.
# ---------------------------------------------------------------------------
LT_ENABLED=0
if [ "$INSTALL_LIBRETRANSLATE" = "1" ]; then
  LT_ENABLED=1
  echo "[translation] SHOPVPN_INSTALL_LIBRETRANSLATE=1 -> installing LibreTranslate (several GB)."
  echo "[translation] This is optional; Argos already handles offline translation."

  if [ ! -x "$LT_PYTHON" ]; then
    echo "[translation] Creating isolated LibreTranslate environment..."
    python3 -m venv "$TRANSLATION_VENV_DIR"
  fi
  pip_q "$LT_PYTHON" --upgrade pip setuptools wheel
  pip_q "$LT_PYTHON" --upgrade 'libretranslate>=1.9.0'
fi

# ---------------------------------------------------------------------------
# Environment file
# ---------------------------------------------------------------------------
ENV_FILE="$ROOT_DIR/.env"
touch "$ENV_FILE"
set_env() {
  local key="$1" value="$2"
  if grep -q "^${key}=" "$ENV_FILE"; then
    sed -i "s#^${key}=.*#${key}=${value}#" "$ENV_FILE"
  else
    printf '\n%s=%s\n' "$key" "$value" >> "$ENV_FILE"
  fi
}
unset_env() {
  [ -f "$ENV_FILE" ] && sed -i "/^$1=/d" "$ENV_FILE" || true
}

# The local engine is the source of truth. Public providers stay disabled so
# Google/MyMemory/OpenRouter rate limits can never break the UI.
set_env SHOPVPN_TRANSLATION_ALLOW_PUBLIC_APIS 0

if [ "$LT_ENABLED" = "1" ]; then
  set_env SHOPVPN_TRANSLATION_PROVIDERS 'argos,libretranslate'
  set_env SHOPVPN_LIBRETRANSLATE_URL 'http://127.0.0.1:5000'

  # Run LibreTranslate as the installing user with the SAME HOME as the main
  # venv, so it reuses the Argos packages already downloaded instead of
  # fetching a second multi-hundred-MB copy into a private home directory.
  LT_USER="$(id -un)"
  LT_LOAD_ONLY="en,fa"
  for lang in "${TARGETS[@]}"; do
    [ "$lang" = "fa" ] && continue
    LT_LOAD_ONLY="${LT_LOAD_ONLY},${lang}"
  done

  if command -v systemctl >/dev/null 2>&1; then
    SERVICE_FILE=/etc/systemd/system/shopvpn-libretranslate.service
    as_root bash -c "cat > '$SERVICE_FILE' <<EOF
[Unit]
Description=ShopVPN Local LibreTranslate
After=network.target

[Service]
Type=simple
User=$LT_USER
WorkingDirectory=$ROOT_DIR
Environment=HOME=$HOME
Environment=PYTHONUNBUFFERED=1
ExecStart=$TRANSLATION_VENV_DIR/bin/libretranslate --host 127.0.0.1 --port 5000 --load-only $LT_LOAD_ONLY --disable-web-ui
Restart=on-failure
RestartSec=5
TimeoutStartSec=15min
TimeoutStopSec=30s

[Install]
WantedBy=multi-user.target
EOF"
    as_root systemctl daemon-reload
    as_root systemctl enable shopvpn-libretranslate.service >/dev/null
    as_root systemctl restart shopvpn-libretranslate.service || true

    ready=0
    for _ in $(seq 1 90); do
      if curl -fsS --max-time 3 http://127.0.0.1:5000/languages >/dev/null 2>&1; then
        ready=1
        break
      fi
      sleep 2
    done
    if [ "$ready" -ne 1 ]; then
      echo "[translation] WARNING: LibreTranslate did not become ready within 180s." >&2
      as_root systemctl --no-pager --full status shopvpn-libretranslate.service 2>&1 | tail -40 >&2 || true
      as_root journalctl -u shopvpn-libretranslate.service -n 40 --no-pager 2>&1 >&2 || true
    fi
  fi
else
  # Lean default: Argos only. Avoids pointless connections to a server that
  # is intentionally not installed.
  set_env SHOPVPN_TRANSLATION_PROVIDERS 'argos'
  unset_env SHOPVPN_LIBRETRANSLATE_URL
fi

# ---------------------------------------------------------------------------
# Reclaim space: pip caches are pure waste once a venv is built.
# ---------------------------------------------------------------------------
"$PYTHON_BIN" -m pip cache purge >/dev/null 2>&1 || true
if [ -x "$LT_PYTHON" ]; then "$LT_PYTHON" -m pip cache purge >/dev/null 2>&1 || true; fi
rm -rf "$HOME/.cache/pip" 2>/dev/null || true
if [ "$(id -u)" -eq 0 ]; then rm -rf /root/.cache/pip 2>/dev/null || true; fi

"$PYTHON_BIN" - <<'PY'
import argostranslate
print("[translation] Argos Translate: ready")
PY

if [ "$LT_ENABLED" = "1" ] && command -v curl >/dev/null 2>&1; then
  if curl -fsS --max-time 5 http://127.0.0.1:5000/languages >/dev/null 2>&1; then
    echo "[translation] Local LibreTranslate: ready"
  else
    echo "[translation] Local LibreTranslate is not reachable; Argos remains the primary provider."
  fi
fi

echo "[translation] Public translation APIs are disabled by default."
if [ "${#TARGETS[@]}" -gt 0 ]; then
  echo "[translation] Installed Argos pairs: en_fa, fa_en, $(printf 'en_%s ' "${TARGETS[@]}" | sed 's/ $//')"
else
  echo "[translation] Installed Argos pairs: en_fa, fa_en"
fi
echo "[translation] Disk used -> venv: $(human "$VENV_DIR") | translation-venv: $(human "$TRANSLATION_VENV_DIR") | Argos models: $(human "$HOME/.local/share/argos-translate") $(human "$HOME/.local/cache/argos-translate")"
echo "[translation] Add more languages later with: SHOPVPN_TRANSLATION_LANGS=tr,ar bash setup_local_translation.sh"
echo "[translation] Local translation setup completed."
