# 🛰️ ShopVPN install guide (personal fork `amir12120/Shopvpn`)

This document is specific to the **personal fork** and explains a lean,
disk-aware installation on **Ubuntu 22.04** (and Debian 11+).

- 🔗 Repository: <https://github.com/amir12120/Shopvpn>
- 🧩 Upstream project: `mehdirafatpanah/Shopvpn`

> Note: this fork makes the installer "lean" so **disk usage drops sharply**
> (details in [Fixing high disk usage](#disk)).

---

## 📋 Contents

1. [Requirements](#prereqs)
2. [Install with one command](#install)
3. [Day-to-day management (`shopvpn`)](#manage)
4. [Fixing high disk usage](#disk)
5. [Translation languages and optional LibreTranslate](#langs)
6. [Troubleshooting](#troubleshoot)

---

<a id="prereqs"></a>

## 1) Requirements

| Item | Minimum | Notes |
|---|---|---|
| OS | Ubuntu 20.04+ / Debian 11+ | Ubuntu 22.04 recommended |
| Python | 3.10+ | Ubuntu 22.04 ships Python 3.10 by default ✅ |
| Free disk | ~1.5 GB | Lean install; 2 GB+ is better for logs/backups |
| RAM | 1 GB (2 GB recommended) | Local translation also needs RAM |
| Access | root / sudo | To install packages and create the systemd service |
| Internet | Stable | To clone from git and download models |
| Optional (webhook/panel) | A domain whose DNS points to the server IP | Only for Webhook mode or the Mini App |
| Telegram | A bot token from [@BotFather](https://t.me/BotFather) and the admin numeric ID | To build `.env` |

System packages that get installed:

- Base: `git`, `curl`, `ca-certificates`, `python3`, `python3-pip`, `python3-venv`
- Build (only if no prebuilt wheel exists): `build-essential`, `python3-dev`, `pkg-config`, `libffi-dev`, `libssl-dev`, `zlib1g-dev`, `libjpeg-dev`
- Optional webhook: `nginx`, `certbot`, `python3-certbot-nginx`

---

<a id="install"></a>

## 2) Install with one command

On a fresh Ubuntu/Debian server, run **one** command. It does everything:

1. installs every missing system prerequisite,
2. installs (or updates) the bot from this fork,
3. installs the `shopvpn` CLI command,
4. opens the management menu automatically when the install finishes.

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/amir12120/Shopvpn/main/install.sh)
```

> 🔁 Running the same command again = update (idempotent). The `.env` file and
> the database are always preserved.

While installing you will be asked for the **bot token** and the **admin
numeric ID**, and whether the bot should use **Polling** (default) or
**Webhook**.

Prefer to only install prerequisites first (optional, so apt never stalls
mid-install)? You can still run the preflight checker on its own:

```bash
# check + install prerequisites only
sudo bash <(curl -fsSL https://raw.githubusercontent.com/amir12120/Shopvpn/main/preflight.sh)

# report what is missing without changing anything
bash preflight.sh --check

# also install nginx + certbot for webhook mode
sudo bash preflight.sh --with-web
```

### Installer environment knobs (all optional)

| Variable | Effect |
|---|---|
| `SHOPVPN_TRANSLATION_LANGS="tr,ar"` | Preload extra Argos languages (or `all`) |
| `SHOPVPN_INSTALL_LIBRETRANSLATE=1` | Also install the heavy LibreTranslate fallback |
| `SHOPVPN_SKIP_MODELS=1` | Skip Argos model downloads |
| `SHOPVPN_SKIP_SERVICE_START=1` | Create/enable the service but don't start it |
| `SHOPVPN_SKIP_MENU=1` | Don't auto-open the management menu at the end |

---

<a id="manage"></a>

## 3) Day-to-day management (`shopvpn`)

The installer puts a `shopvpn` command in `/usr/local/bin`, so the management
menu is always one word away:

```bash
shopvpn
```

You can also run the same CLI straight from the repository without installing
anything:

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/amir12120/Shopvpn/main/manage.sh)
```

The bot runs as a `systemd` service:

```bash
sudo systemctl status v2raybot      # status
sudo journalctl -u v2raybot -f      # live logs
sudo systemctl restart v2raybot     # restart
sudo systemctl stop v2raybot        # stop
```

The management menu handles install/update, backups, the web panel, the Mini
App, the Integration API, VPN panels and translation languages. The default
menu language is English; press `L` in the menu to switch to Persian.

---

<a id="disk"></a>

## 4) Fixing high disk usage

The default install is lean (~1 to 1.5 GB) instead of several GB:

- ✅ **LibreTranslate is not installed by default.** Argos alone is enough;
  the app tries Argos first and treats LibreTranslate as a second fallback.
- ✅ **Model files are downloaded only for the languages you need** (default
  just `fa`).
- ✅ **pip's cache is never kept** (`PIP_NO_CACHE_DIR=1` plus cleanup).
- ✅ **CPU-only `torch`** is pre-installed (`--index-url .../whl/cpu`) so pip
  never pulls ~5 GB of CUDA/`nvidia-*` libraries. On a real Ubuntu 22.04 test
  the venv dropped from **~5.7 GB to ~1.3 GB**.
- ✅ The apt cache and downloaded package archives are cleaned, and
  prerequisites use `--no-install-recommends`.
- ✅ The clone is **shallow** (`--depth 1`).

At the end of every install **and every update** (the `shopvpn` update action
runs the same cleanup step), [`cleanup.sh`](cleanup.sh) runs automatically and
removes only regenerable files (pip/apt caches, `__pycache__`, `*.pyc`, build
artifacts, downloaded Argos archives). It never removes `venv/`,
`translation-venv/`, `.env`, databases, `backups/`, logs or installed language
models.

After the service is restarted, the installer (and every `shopvpn` update)
waits until the unit has stayed active across several checks before reporting
success. If it never comes up, the last 25 journal lines are printed instead of
a misleading "done" — the same check is applied to the Mini App, panel and API
units.

Run it manually any time (e.g. when the disk is full):

```bash
sudo bash ~/v2ray_bot/cleanup.sh
```

If you installed the old heavy version before, remove LibreTranslate from the
`shopvpn` menu (option 28) or manually:

```bash
sudo systemctl disable --now shopvpn-libretranslate 2>/dev/null
sudo rm -f /etc/systemd/system/shopvpn-libretranslate.service && sudo systemctl daemon-reload
rm -rf ~/v2ray_bot/translation-venv ~/v2ray_bot/.translation-home
rm -rf ~/.cache/pip /root/.cache/pip
df -h /
```

---

<a id="langs"></a>

## 5) Translation languages and optional LibreTranslate

By default only the **Persian/English** pairs (`en_fa` and `fa_en`) are
installed. To translate more languages locally:

```bash
# install specific languages (e.g. Turkish and Arabic)
SHOPVPN_TRANSLATION_LANGS="tr,ar" bash ~/v2ray_bot/setup_local_translation.sh

# or every language in the catalog (~1.5 GB+)
SHOPVPN_TRANSLATION_LANGS=all bash ~/v2ray_bot/setup_local_translation.sh
```

> You can do the same from the `shopvpn` menu (option 29).

**LibreTranslate (heavy, optional)** — only if you need more language/quality:

```bash
SHOPVPN_INSTALL_LIBRETRANSLATE=1 bash ~/v2ray_bot/setup_local_translation.sh
```

> ⚠️ This uses several GB. Most shops do not need it.

---

<a id="troubleshoot"></a>

## 6) Troubleshooting

| Problem | Fix |
|---|---|
| The install stalls on apt | Run `preflight.sh` first; the `DEBIAN_FRONTEND=noninteractive` and `NEEDRESTART_*` variables are already set |
| git clone fails / asks for a username+password | The script automatically falls back to the `codeload.github.com` archive |
| Disk is full | See [Fixing high disk usage](#disk); remove LibreTranslate and purge the pip cache |
| The bot does not start | `sudo journalctl -u v2raybot -n 80 --no-pager`; usually a wrong `BOT_TOKEN`/`OWNER_ID` |
| A language does not translate | Install that language (see [languages](#langs)) |
| Python is too old | Make sure it is Ubuntu 22.04, or install python3.10+ |

---

## 🔒 Security notes

- Never commit `BOT_TOKEN`, the `.env` file or API keys to GitHub or a public
  chat.
- If a token leaks, immediately issue a new one from
  [@BotFather](https://t.me/BotFather) with `/revoke`.

## 📄 License

MIT — the original project is by **Mehdi Rafatpanah**
([@mehdirafatpanah](https://github.com/mehdirafatpanah)).
