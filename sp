#!/usr/bin/env bash
# ============================================================================
# sp — the short ShopVPN command.
#
#   sp update     fetch the latest code, refresh packages and translation,
#                 reclaim disk, restart the services and wait until the bot is
#                 actually up (same pipeline as menu item 2, no menu, no key
#                 press, meaningful exit status)
#   sp status     show the installed services and the installed version
#   sp restart    restart the bot and wait until it is ready
#   sp version    print the installed version
#   sp            open the interactive management menu
#
# install.sh writes /usr/local/bin/sp. To use a checkout somewhere else (or to
# run this file straight from the repo):
#
#   SHOPVPN_DIR=/srv/shopvpn bash sp update
# ============================================================================
set -u

self="$0"
# Follow symlinks so an installed /usr/local/bin/sp still resolves to the
# checkout it belongs to.
if resolved="$(readlink -f "$self" 2>/dev/null)" && [ -n "$resolved" ]; then
    self="$resolved"
fi

if [ -n "${SHOPVPN_DIR:-}" ]; then
    install_dir="$SHOPVPN_DIR"
else
    install_dir="$(cd "$(dirname "$self")" && pwd)"
    [ -f "$install_dir/manage.sh" ] || install_dir="$HOME/v2ray_bot"
fi

if [ ! -f "$install_dir/manage.sh" ]; then
    echo "ShopVPN is not installed (no manage.sh in $install_dir)." >&2
    echo "Install it first:" >&2
    echo "  bash <(curl -fsSL https://raw.githubusercontent.com/amir12120/shopvpn-amir/main/install.sh)" >&2
    exit 1
fi

# manage.sh reads the same variable, so both halves agree on the checkout
export SHOPVPN_DIR="$install_dir"
exec bash "$install_dir/manage.sh" "$@"
