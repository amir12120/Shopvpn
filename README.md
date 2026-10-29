# 🛰️ ShopVPN Amir

A personal, standalone fork of [ShopVPN](https://github.com/mehdirafatpanah/Shopvpn) for selling and managing VPN/SSH services through Telegram.

- **Repository:** <https://github.com/amir12120/shopvpn-amir>
- **Default branch:** `main`
- **UI languages:** Persian and English only
- **Install style:** lean, English-only output, no heavy LibreTranslate by default

> This repository is **not** a GitHub fork anymore. It keeps its own history and
> releases; upstream changes are reviewed and copied manually with
> [`SYNC_UPSTREAM.md`](SYNC_UPSTREAM.md).

---

## ✨ What this fork changes

| Area | Behaviour in this fork |
|---|---|
| Languages | Only `fa` and `en`; no third language is installed or offered |
| Translation | Local Argos models (`en↔fa`) by default; LibreTranslate is opt-in and never downloaded silently |
| Disk | No pip cache, CPU-only PyTorch, capped systemd journal, automatic cleanup after install **and** update |
| Install | One command, English output, no interactive questions except bot token/admin ID and polling vs. webhook |
| Updates | `sp update` / menu option 2: fetch, packages, translation, cleanup, restart and a real readiness check |
| Update errors | A failed translation refresh is a warning, not a dead bot; the bot keeps the models it already has |
| Translation repair | Missing `SHOPVPN_TRANSLATION_LANGS` is self-healed, and the script can no longer exit silently |
| Repository | Standalone since v4.17.0; upstream can still be synced manually at any time |

---

## 🚀 Install

On a fresh Ubuntu 20.04+/Debian 11+ server (Ubuntu 22.04 recommended):

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/amir12120/shopvpn-amir/main/install.sh)
```

The installer:

1. installs the missing system packages,
2. clones this repository and creates the Python virtual environment,
3. installs the packages and the local Persian/English translation models,
4. asks for the bot token and the admin numeric ID,
5. creates and starts the `v2raybot` systemd service,
6. installs the `shopvpn` and `sp` commands and opens the management menu.

Full details, requirements and troubleshooting: [`INSTALL.md`](INSTALL.md) (English) / [`INSTALL.fa.md`](INSTALL.fa.md) (Persian).

> The `.env` file and the database are preserved when the installer is run again.
> Running the same command is also the supported update path.

---

## 🧰 Manage and update

```bash
shopvpn          # interactive management menu
sp update        # fetch, packages, translation, cleanup, restart, readiness check
sp status        # service state and installed version
sp restart       # restart and wait until the bot is really up
sp version       # print the installed version
```

The bot itself is a normal systemd unit:

```bash
sudo systemctl status v2raybot
sudo journalctl -u v2raybot -f
sudo systemctl restart v2raybot
```

If an update ends with **“⚠️ Bot did not start”**, first check the real unit:

```bash
sudo systemctl status v2raybot --no-pager
sudo journalctl -u v2raybot -n 80 --no-pager
```

A translation warning printed *above* a successful restart does not mean the bot
is down. The update summary now reports failure only when the unit is actually
inactive.

---

## 🔌 Provisioning and sales

- Automatic configuration delivery on the supported VPN panels.
- **SSH management** (added in v4.17): SSH nodes, SSH accounts, create/extend/disable, usage and subscription URI.
- **Combined VPN + SSH products** share one volume/expiry quota pool; renewing either member renews the pool.
- Per-panel data-limit synchronization after sales and renewals.
- Config inventory, direct product-to-panel assignment, multi-quantity purchases, test plans.
- Renewals by time or volume, on-hold services, service migration, panel capacity limits.
- Product/category management, stock alerts, discount codes, wallets, cashback, gift cards and coins.

## 💳 Payments and customers

- Multiple automatic gateways (card-to-card and online providers), wallet top-up and admin approval.
- Manual receipt screening: duplicate/OCR/forensic checks, optional bank inquiry, admin decision stays final.
- Support tickets, live chat, mandatory channel membership, anti-spam and user blocking.
- Reseller bots, linked reseller mode, tiers, credit limits and referral commissions.

## 🖥️ Interfaces

- **Telegram admin panel:** users, products, panels, payments, backups, reports, broadcasts and settings.
- **Telegram Mini App:** storefront, orders, services, renewals, SSH and support.
- **Standalone web admin panel** (`admin_panel/`): server-driven UI, roles, settings, reports.
- **Android management app:** server-driven screens and push notifications.
- **Integration API:** token-scoped endpoints for external tools.

## 🧠 Automation and operations

- AI support assistant with account actions and optional multi-provider vision/OCR.
- AI admin help, campaign manager, churn prediction and contextual tutorials.
- Automatic daily backups, restore, secondary backup destinations and factory reset.
- Panel health monitoring, topic-based report groups, scheduled broadcasts and deep-link tracking.
- Local translation dashboard, quality guard and per-user language selection (Persian/English).

---

## 🔌 Supported panels

| Panel | Status |
|---|---|
| PasarGuard | ✅ Full |
| Marzban | ✅ Full |
| Marzneshin | ✅ Full |
| Hiddify | ✅ Full |
| 3X-UI / Alireza X-UI | ✅ Full |
| Rebecca | ✅ Full |
| S-UI | ✅ Full |
| WGDashboard | ✅ Full |
| MikroTik / User Manager | ⚠️ Limited |
| IBSng | ⚠️ Limited |

SSH nodes are separate Linux hosts managed through `ssh_node_agent`; they can be
combined with a VPN panel in one product.

---

## 🖥️ Requirements

- Ubuntu 20.04+ / Debian 11+ (Ubuntu 22.04 recommended)
- Python 3.10+
- 1 GB RAM minimum, 2 GB recommended
- About 1.5 GB free disk for the lean install (more for logs/backups)
- A Telegram bot token and the admin numeric ID
- A domain with HTTPS for webhook, Mini App or the web panel
- API credentials for the payment/VPN providers you enable

> Never commit `.env`, bot tokens, API keys or production databases.

---

## 🔄 Updating from upstream

The repository is standalone, so GitHub will not merge upstream automatically.
The reviewed procedure is in [`SYNC_UPSTREAM.md`](SYNC_UPSTREAM.md): fetch
upstream, classify the changes, keep this fork's installer/cleanup/language
policy, merge only useful Python features, run the tests and publish a release.

Protected by design:

- `install.sh`, `manage.sh`, `update.sh`, `preflight.sh`, `cleanup.sh`,
  `setup_local_translation.sh`
- `.github/`, `tests/`, `VERSION`
- English/Persian docs
- the `fa`/`en`-only language policy

---

## 📚 Documentation

- 🇬🇧 English: [`README.md`](README.md) · [`INSTALL.md`](INSTALL.md)
- 🇮🇷 Persian: [`README.fa.md`](README.fa.md) · [`INSTALL.fa.md`](INSTALL.fa.md)
- 🔄 Upstream sync: [`SYNC_UPSTREAM.md`](SYNC_UPSTREAM.md)

Russian and Chinese readmes were removed: the application and its docs support
Persian and English only.

---

## 📄 License and credits

MIT. The original project is by **Mehdi Rafatpanah**
([@mehdirafatpanah](https://github.com/mehdirafatpanah)).
This fork is maintained by [@amir12120](https://github.com/amir12120).
