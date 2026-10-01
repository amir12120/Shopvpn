#!/bin/bash
# ============================================================================
# ShopVPN installer / updater  (personal fork: amir12120/Shopvpn)
#
# One command does everything, in this order:
#   1. installs every missing system prerequisite (git, python3, venv, ...)
#   2. installs or updates the bot from this fork
#   3. installs the `shopvpn` CLI command
#   4. opens the management CLI menu automatically when the install is done
#
#   bash <(curl -fsSL https://raw.githubusercontent.com/amir12120/Shopvpn/main/install.sh)
#
# Afterwards, typing `shopvpn` opens the same management menu at any time.
#
# Disk-lean by default: Argos only (no heavy LibreTranslate) and no pip cache.
# The script is idempotent: run it again to update. The .env file and the
# database are always preserved.
#
# Environment knobs (all optional):
#   SHOPVPN_TRANSLATION_LANGS="tr,ar"   extra Argos languages to preload (or "all")
#   SHOPVPN_INSTALL_LIBRETRANSLATE=1    also install the heavy LibreTranslate
#   SHOPVPN_SKIP_MODELS=1               skip Argos model downloads
#   SHOPVPN_SKIP_SERVICE_START=1        create the systemd unit but don't start it
#   SHOPVPN_SKIP_MENU=1                 don't auto-open the CLI menu at the end
# ============================================================================

set -e

# Never let apt hang behind interactive prompts (e.g. needrestart restarting
# services during an unattended install).
export DEBIAN_FRONTEND=noninteractive
export NEEDRESTART_MODE=a
export NEEDRESTART_SUSPEND=1

# ----------------------------------------------------------------------------
# Settings
# ----------------------------------------------------------------------------
REPO_URL="https://github.com/amir12120/Shopvpn.git"
INSTALL_DIR="$HOME/v2ray_bot"
SERVICE_NAME="v2raybot"
CLI_NAME="shopvpn"
GITHUB_OWNER="amir12120"
GITHUB_REPO="Shopvpn"
GITHUB_BRANCH="main"

TOTAL_STEPS=7

echo "🚀 ShopVPN — V2Ray sales bot installer / updater"
echo "──────────────────────────────────────────"

# ----------------------------------------------------------------------------
# 1/7. System prerequisites (always first, so the Python/translation steps
#      never stall on a slow or interactive apt call later).
# ----------------------------------------------------------------------------
echo "📦 Step 1/${TOTAL_STEPS} — installing system prerequisites first..."
# --no-install-recommends keeps the apt footprint small.
sudo env DEBIAN_FRONTEND=noninteractive NEEDRESTART_MODE=a NEEDRESTART_SUSPEND=1 apt-get update -qq
timeout 240 sudo env DEBIAN_FRONTEND=noninteractive NEEDRESTART_MODE=a NEEDRESTART_SUSPEND=1 \
    apt-get install -y -qq --no-install-recommends \
    git curl ca-certificates python3 python3-pip python3-venv \
    build-essential python3-dev pkg-config libffi-dev libssl-dev zlib1g-dev libjpeg-dev > /dev/null

echo "   git: $(git --version 2>/dev/null || echo MISSING) | python3: $(python3 --version 2>/dev/null || echo MISSING)"

# Never keep pip's download cache (it can be several GB on a small disk).
export PIP_NO_CACHE_DIR=1
export PIP_DISABLE_PIP_VERSION_CHECK=1
export GIT_TERMINAL_PROMPT=0

# ----------------------------------------------------------------------------
# 2/7. Fetch or update the code from GitHub.
#      Some servers (especially cheap VPS providers) get blocked or throttled
#      by GitHub for the git-over-https protocol even on public repos, and git
#      then falls back to an interactive username/password prompt that hangs a
#      headless install. We try git first (fast, incremental) and fall back to
#      the plain archive download (codeload.github.com), which is not subject
#      to that block.
# ----------------------------------------------------------------------------
fetch_project_code() {
    local ok=0
    if [ -d "$INSTALL_DIR/.git" ]; then
        echo "🔄 Existing checkout found, fetching the latest changes..."
        if git -C "$INSTALL_DIR" pull --quiet; then ok=1; fi
    else
        echo "📥 Downloading the project from GitHub..."
        # Shallow clone: the full history is never stored on the server disk.
        if git clone --quiet --depth 1 "$REPO_URL" "$INSTALL_DIR"; then ok=1; fi
    fi

    if [ "$ok" = "1" ]; then
        return 0
    fi

    echo "⚠️ git access was blocked, downloading the archive instead..."
    local tmp_tar tmp_dir
    tmp_tar=$(mktemp)
    tmp_dir=$(mktemp -d)
    if ! curl -fsSL "https://codeload.github.com/${GITHUB_OWNER}/${GITHUB_REPO}/tar.gz/refs/heads/${GITHUB_BRANCH}" -o "$tmp_tar"; then
        echo "❌ Could not download the project archive either. Check the server's internet connection."
        rm -f "$tmp_tar"; rm -rf "$tmp_dir"
        return 1
    fi
    tar -xzf "$tmp_tar" -C "$tmp_dir" --strip-components=1
    rm -f "$tmp_tar"
    mkdir -p "$INSTALL_DIR"
    if ! command -v rsync > /dev/null 2>&1; then
        sudo env DEBIAN_FRONTEND=noninteractive apt-get install -y -qq rsync > /dev/null
    fi
    rsync -a --exclude='.env' --exclude='*.db' --exclude='*.db-journal' \
        --exclude='*.sqlite3' --exclude='venv' --exclude='.git' --exclude='backups' \
        "$tmp_dir"/ "$INSTALL_DIR"/
    rm -rf "$INSTALL_DIR/.git" 2>/dev/null
    rm -rf "$tmp_dir"
    return 0
}

echo "📥 Step 2/${TOTAL_STEPS} — fetching the project code..."
fetch_project_code
cd "$INSTALL_DIR"

# ----------------------------------------------------------------------------
# 3/7. Create the virtual environment and install the packages.
# ----------------------------------------------------------------------------
echo "🐍 Step 3/${TOTAL_STEPS} — preparing the Python environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
# argostranslate -> stanza -> torch. pip installs the CUDA build on Linux by
# default, which pulls ~5 GB of nvidia libraries. We pre-install the CPU-only
# build from the official PyTorch index so pip never fetches the heavy one.
if ! pip -q --no-cache-dir --disable-pip-version-check install \
        --index-url https://download.pytorch.org/whl/cpu torch; then
    echo "⚠️ Could not install CPU-only torch; continuing (the heavy build may be used)."
fi
pip install -q --no-cache-dir -r requirements.txt
deactivate

# ----------------------------------------------------------------------------
# 4/7. Configure the .env file (first run only; the file is never in git).
# ----------------------------------------------------------------------------
echo "🔑 Step 4/${TOTAL_STEPS} — configuring .env..."
if [ ! -f "$INSTALL_DIR/.env" ]; then
    echo ""
    echo "🔑 No .env file found. Enter the details below:"
    read -rp "Bot token (from BotFather): " BOT_TOKEN_INPUT
    read -rp "Admin numeric ID (e.g. from @userinfobot): " OWNER_ID_INPUT
    cat > "$INSTALL_DIR/.env" <<EOF
BOT_TOKEN=$BOT_TOKEN_INPUT
OWNER_ID=$OWNER_ID_INPUT
EOF

    echo ""
    echo "How should the bot receive Telegram updates?"
    echo "  1) Polling  (default - simpler, no domain/SSL required)"
    echo "  2) Webhook  (requires a domain whose DNS points to this server's IP)"
    read -rp "Choose [1]: " BOT_MODE_CHOICE
    BOT_MODE_CHOICE="${BOT_MODE_CHOICE:-1}"

    if [ "$BOT_MODE_CHOICE" = "2" ]; then
        read -rp "Domain to use for the bot webhook (e.g. bot.example.com): " WEBHOOK_DOMAIN
        if [ -z "$WEBHOOK_DOMAIN" ]; then
            echo "⚠️ No domain entered; starting the bot with Polling (you can enable webhook later from the manage CLI)."
        else
            WEBHOOK_PORT=8010
            echo "📦 Installing nginx and certbot..."
            sudo env DEBIAN_FRONTEND=noninteractive NEEDRESTART_MODE=a NEEDRESTART_SUSPEND=1 \
                apt-get install -y -qq nginx certbot python3-certbot-nginx > /dev/null

            echo "🌐 Configuring nginx for $WEBHOOK_DOMAIN..."
            sudo bash -c "cat > /etc/nginx/sites-available/${WEBHOOK_DOMAIN}.conf" <<NGXEOF
server {
    listen 80;
    server_name $WEBHOOK_DOMAIN;

    location / {
        proxy_pass http://127.0.0.1:$WEBHOOK_PORT;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
NGXEOF
            sudo ln -sf "/etc/nginx/sites-available/${WEBHOOK_DOMAIN}.conf" "/etc/nginx/sites-enabled/${WEBHOOK_DOMAIN}.conf"

            if ! sudo nginx -t > /dev/null 2>&1; then
                echo "⛔️ The nginx config has an error; starting the bot with Polling."
            else
                sudo systemctl reload nginx
                echo "🔐 Obtaining an SSL certificate (Let's Encrypt)..."
                if sudo certbot --nginx -d "$WEBHOOK_DOMAIN" --non-interactive --agree-tos \
                    --register-unsafely-without-email --redirect; then
                    WEBHOOK_SECRET_VAL=$(python3 -c "import secrets; print(secrets.token_hex(24))")
                    cat >> "$INSTALL_DIR/.env" <<EOF
BOT_MODE=webhook
WEBHOOK_BASE_URL=https://$WEBHOOK_DOMAIN
WEBHOOK_SECRET=$WEBHOOK_SECRET_VAL
WEBHOOK_LISTEN_HOST=127.0.0.1
WEBHOOK_LISTEN_PORT=$WEBHOOK_PORT
EOF
                    echo "✅ Webhook mode configured: https://$WEBHOOK_DOMAIN"
                else
                    echo "⛔️ SSL setup failed; starting the bot with Polling (retry later from the manage CLI)."
                fi
            fi
        fi
    fi
    echo "✅ .env file created."
else
    echo "✅ .env file already exists, leaving it unchanged."
fi

# ----------------------------------------------------------------------------
# 5/7. Install and start the local translation engine automatically, so the
#      user never has to install an Argos model or LibreTranslate by hand.
# ----------------------------------------------------------------------------
echo "🌍 Step 5/${TOTAL_STEPS} — installing the lean local translation engine and language models..."
# More languages: SHOPVPN_TRANSLATION_LANGS="tr,ar".
# Heavy LibreTranslate fallback: SHOPVPN_INSTALL_LIBRETRANSLATE=1.
if ! bash "$INSTALL_DIR/setup_local_translation.sh"; then
    echo "⚠️ Local translation setup did not finish; the bot will continue and retry on the next update."
fi

# Reclaim wasted space (pip cache, apt cache, model download cache, __pycache__).
# This only removes regenerable files and does not touch the running bot.
if [ -f "$INSTALL_DIR/cleanup.sh" ]; then
    bash "$INSTALL_DIR/cleanup.sh" "$INSTALL_DIR" || true
fi
echo "💾 Disk used -> venv: $(du -sh "$INSTALL_DIR/venv" 2>/dev/null | cut -f1) | project: $(du -sh "$INSTALL_DIR" 2>/dev/null | cut -f1)"

# ----------------------------------------------------------------------------
# 6/7. Create the systemd service for permanent running and auto-start on boot.
# ----------------------------------------------------------------------------
echo "⚙️ Step 6/${TOTAL_STEPS} — configuring the systemd service..."
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
sudo bash -c "cat > $SERVICE_FILE" <<EOF
[Unit]
Description=V2Ray Telegram Sales Bot
After=network.target

[Service]
Type=simple
WorkingDirectory=$INSTALL_DIR
ExecStart=$INSTALL_DIR/venv/bin/python3 $INSTALL_DIR/main.py
Restart=always
RestartSec=5
User=$(whoami)

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable "$SERVICE_NAME" > /dev/null 2>&1

# In CI/tests, SHOPVPN_SKIP_SERVICE_START=1 creates and enables the unit but
# does not start it right now.
if [ "${SHOPVPN_SKIP_SERVICE_START:-0}" = "1" ]; then
    echo "ℹ️ SHOPVPN_SKIP_SERVICE_START=1 → service created but not started."
else
    sudo systemctl restart "$SERVICE_NAME"
fi

sleep 2

echo ""
echo "──────────────────────────────────────────"
if sudo systemctl is-active --quiet "$SERVICE_NAME"; then
    echo "✅ The bot was installed/updated and is running."
else
    echo "⚠️ The bot is not running. To inspect the error:"
    echo "   sudo journalctl -u $SERVICE_NAME -n 50 --no-pager"
fi

# ----------------------------------------------------------------------------
# 7/7. Install the `shopvpn` CLI command and open the management menu.
# ----------------------------------------------------------------------------
echo "🧰 Step 7/${TOTAL_STEPS} — installing the '${CLI_NAME}' CLI command..."
CLI_TMP="$(mktemp)"
cat > "$CLI_TMP" <<EOF
#!/usr/bin/env bash
# ${CLI_NAME} — ShopVPN management CLI (created automatically by install.sh).
# Opens the interactive management menu; safe to run any time.
INSTALL_DIR="${INSTALL_DIR}"
if [ ! -f "\$INSTALL_DIR/manage.sh" ]; then
    echo "ShopVPN is not installed at \$INSTALL_DIR." >&2
    echo "Install it first with:" >&2
    echo "  bash <(curl -fsSL https://raw.githubusercontent.com/amir12120/Shopvpn/main/install.sh)" >&2
    exit 1
fi
exec bash "\$INSTALL_DIR/manage.sh" "\$@"
EOF
if sudo install -m 0755 "$CLI_TMP" "/usr/local/bin/${CLI_NAME}"; then
    echo "✅ Installed: /usr/local/bin/${CLI_NAME}"
else
    echo "⚠️ Could not install /usr/local/bin/${CLI_NAME}; run manage.sh directly instead: bash $INSTALL_DIR/manage.sh"
fi
rm -f "$CLI_TMP"

echo ""
echo "Useful commands:"
echo "  Bot status:   sudo systemctl status $SERVICE_NAME"
echo "  Live logs:    sudo journalctl -u $SERVICE_NAME -f"
echo "  Restart:      sudo systemctl restart $SERVICE_NAME"
echo "  Stop:         sudo systemctl stop $SERVICE_NAME"
echo "  Manage menu:  ${CLI_NAME}"
echo "──────────────────────────────────────────"

# Open the management menu automatically on an interactive install. In CI or a
# piped/non-interactive run (and with SHOPVPN_SKIP_MENU=1) this is skipped.
if [ "${SHOPVPN_SKIP_MENU:-0}" = "1" ]; then
    echo "ℹ️ SHOPVPN_SKIP_MENU=1 → skipping the automatic CLI menu. Run '${CLI_NAME}' to open it later."
elif [ ! -t 0 ]; then
    echo "ℹ️ Non-interactive session → skipping the automatic CLI menu. Run '${CLI_NAME}' to open it later."
else
    echo "▶️ Opening the management CLI menu..."
    echo ""
    exec bash "$INSTALL_DIR/manage.sh"
fi
