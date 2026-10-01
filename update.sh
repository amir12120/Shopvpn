#!/bin/bash
# ============================================================================
# ShopVPN update helper (matches the systemd service that install.sh creates).
#
# Usage: ./update.sh "short change description"
#
# It commits and pushes local changes, refreshes the Python packages and the
# local translation engine, then restarts the bot service.
# ============================================================================

set -e

cd "$(dirname "$0")"

COMMIT_MSG="${1:-Update without a description}"
SERVICE_NAME="v2raybot"

echo "📦 Recording changes in git..."
git add .
git commit -m "$COMMIT_MSG" || echo "  (nothing to commit)"
git push || echo "  ⚠️ push failed (remote not configured or a token is required)"

echo "🐍 Updating Python packages..."
# Never keep pip's download cache (saves disk space).
export PIP_NO_CACHE_DIR=1
source venv/bin/activate
pip install -q --no-cache-dir -r requirements.txt
deactivate
venv/bin/python3 -m pip cache purge >/dev/null 2>&1 || true
rm -rf "$HOME/.cache/pip" 2>/dev/null || true

echo "🌍 Updating the local translation engine and language models automatically..."
bash "$PWD/setup_local_translation.sh" || echo "  ⚠️ Translation engine update did not finish; it will retry on the next run."

echo "🔄 Restarting the bot service..."
sudo systemctl restart "$SERVICE_NAME"
sleep 2

echo "✅ Done."
sudo systemctl status "$SERVICE_NAME" --no-pager -l | head -10
