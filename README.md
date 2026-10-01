[🇬🇧 English](README.md) | [🇮🇷 فارسی](README.fa.md) | [🇷🇺 Русский](README.ru.md) | [🇨🇳 中文](README.zh.md)

<div align="center">

# 🛰️ ShopVPN — Smart V2Ray Configuration Sales Bot

**An automated Telegram V2Ray sales platform with a dedicated Mini App, AI support assistant, Android management app, web administration, multi-level reseller support, and Persian/English UI.**

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![aiogram](https://img.shields.io/badge/aiogram-3.x-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white)](https://docs.aiogram.dev/)
[![FastAPI](https://img.shields.io/badge/FastAPI-MiniApp%20%2B%20Panel-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](LICENSE)

</div>

---

## 📚 Table of Contents

- [📖 Overview](#overview)
- [✨ Features](#features)
- [🧠 AI Support Assistant](#ai-support)
- [💼 Telegram Business](#business)
- [💳 Payment Gateways](#payment-gateways)
- [📲 Telegram Mini App](#miniapp)
- [🖥️ Standalone Web Admin Panel](#admin-panel)
- [📱 Android Management App](#android-app)
- [🔌 Supported VPN Panels](#vpn-panels)
- [🖥️ Requirements](#requirements)
- [🚀 One-Line Automatic Installation](#auto-install)
- [🛠️ Manual Installation](#manual-install)
- [⚙️ Environment Variables](#env-vars)
- [🧰 manage.sh](#manage-sh)
- [🗂️ Project Structure](#project-structure)
- [🧪 Technology Stack](#tech-stack)
- [🆕 Recently Added Features](#new-features)
- [🔎 Additional Features](#additional-features)
- [🤝 Contributing & License](#contributing)

---

<a id="overview"></a>

## 📖 Overview

**ShopVPN** is a production-oriented Telegram bot for selling and managing V2Ray/VPN configurations. It combines automated provisioning, multiple payment methods, reseller management, AI support, a Telegram Mini App, a standalone web admin panel, and Android management infrastructure.

The project is designed for real-world operation, with wallets, referrals, discounts, support tickets, monitoring, backups, reports, configurable products, and multi-bot reseller support.

### 📢 Official Links

- 📢 **Project:** [@celenorbot](https://t.me/celenorbot)
- 👤 **Author:** [@celenor](https://t.me/celenor)

### ⚡ Quick Summary

- 🔑 Automatic configuration delivery on supported VPN panels
- 💳 Multiple automatic payment methods
- 🧠 AI support assistant
- 🔄 Flexible service renewal
- 🏢 Independent and linked reseller modes
- 🖥️ Telegram admin + web admin + Android management app
- 📲 Telegram Mini App storefront
- 🌍 Server map and panel health monitoring
- 🌐 Polling and Webhook support
- 🚀 Anti-spam, reports, backups, cashback, coins, lottery, gifts and Integration API

> **Detailed sections are collapsed below. Click any section to expand it.**

---

<a id="features"></a>

## ✨ Features

<details>
<summary><strong>🤖 Main Bot — click to expand</strong></summary>

- 🔑 Unique configuration inventory per user with automatic provisioning
- 🔗 Direct product-to-panel assignment
- 🔄 Free-form renewal by traffic/time amount
- 👤 Unified **My Account** for purchased, gifted and test services
- 🧪 Multiple configurable test plans
- 🔢 Multi-quantity purchases with automatic total calculation
- 💱 Automatic USD/USDT exchange-rate lookup with fallback rates
- 💰 Internal wallet with top-up requests and admin approval
- 🗂️ Product/category management with pricing and stock controls
- 🚫 User blocking and mandatory channel membership
- 📊 Live subscription information and expiration/traffic reminders
- ⚠️ Low-stock alerts for administrators
- 📱 Configuration delivery as text + QR code
- 🎫 Support tickets and live support chat
- 🎨 Customizable main-menu layout, labels and colors
- 🏷️ Store branding controls
- 🏢 Independent reseller bots with isolated databases
- 🌐 Polling or Webhook mode
- 💾 Persistent FSM state on SQLite
- ⏳ Temporary/sensitive-message cleanup
- 📣 Channel advertising and deep-link utilities

</details>

<details>
<summary><strong>🤝 Resellers, Referrals, Discounts & Wallet — click to expand</strong></summary>

- 🏢 Linked reseller mode inside the main bot
- 🤖 Independent reseller bots
- 👥 Referral links with multiple reward models
- 💸 Percentage commissions and fixed wallet rewards
- 🎁 Free configuration rewards after referral thresholds
- 🏷️ Discount codes with limits, expiration and product/category scope
- 🎡 Lucky wheel with configurable rewards and cooldown
- 🪜 Reseller tiers, fees, expiration, reminders and credit limits
- 📦 Product-based reseller supply
- 💰 Wallet and cashback features

</details>

<details>
<summary><strong>👑 Telegram Admin Panel — click to expand</strong></summary>

- 👑 Owner, Admin, Mid-level Admin and Support roles
- 📢 Broadcast messaging
- 📈 Sales statistics with date filters
- 📝 Full administrator audit logs
- 🗄️ Automatic daily backups to Telegram
- ♻️ Immediate backup and full database restore
- 📅 Jalali/Persian calendar support
- 👥 Users, products, categories, gateways, panels and reseller management
- 🎫 Support, reports and system settings

</details>

<details>
<summary><strong>🚀 Growth, Security & Monitoring — click to expand</strong></summary>

### 🔐 Security

- 🛡️ User anti-spam/rate limiting
- 🎟️ Advanced discount-code limits
- 🔒 Sensitive payment/card message cleanup

### 📊 Operations

- 🩺 VPN panel health monitoring and recovery alerts
- 📊 Daily sales reports
- 📣 Topic-based report groups
- 🎁 Bulk traffic/time gifts
- 🧹 Automatic cleanup of expired services
- 🔌 Token-scoped Integration API

### 💰 Sales & Retention

- ⏸️ On-hold services that start expiration on first connection
- 📦 Per-panel capacity limits
- 📍 Service location/panel migration
- 💰 Bulk product price editing with undo
- 💸 Renewal/wallet cashback
- 🎁 Wallet top-up gift codes
- 🪙 Coins and scheduled lottery
- 🎫 Department-based support tickets and outage reports

</details>

---

<a id="ai-support"></a>

## 🧠 AI Support Assistant

<details>
<summary><strong>Click to expand</strong></summary>

The AI layer answers repetitive customer questions before escalating to human support.

- 🔌 Selectable providers: Gemini, Groq or OpenRouter
- 📚 Administrator-managed FAQ knowledge
- 🔎 Real user-specific answers for services, expiration, wallet and orders
- 🛒 Real purchase cards with current prices and payment buttons
- 🔒 Wallet purchases/renewals and service changes run only through the bot's validated flows after explicit user confirmation; refunds and complaints go to human support
- 🙋 Automatic escalation for financial complaints or explicit human-support requests
- ⚡ If no API provider is configured, requests can go directly to human support

</details>

---

<a id="business"></a>

## 💼 Telegram Business

<details>
<summary><strong>Click to expand</strong></summary>

The seller can connect the main bot to their own Telegram Business account (Settings → Telegram Business → Chatbots). The bot then answers customers inside the seller's personal chats on their behalf. This works on the main bot only (not on reseller bots) and is **off by default** until an administrator turns it on.

- 🔗 **Connection handling** — `business_connection` and `business_message` updates are stored per connection (owner, reply/read rights, enabled/disabled); admins are notified when a connection is activated or cut
- 🤖 **Automatic AI replies** — customer messages are answered through the AI support assistant with real data; only read-only tools are available here: prices and products, payment methods, service status, server countries, service history and free test config
- 🔒 **No financial actions in business chats** — wallet purchases, renewals and service changes are disabled; such requests are handed to the seller
- 🛡 **Safety filters** — the bot ignores the seller's own messages, administrators, other bots and blocked users; the anti-spam guard and the global bot on/off switch apply to this path as well; non-text messages are ignored
- 🤝 **Human handoff** — when the assistant escalates, it goes silent in that chat and the seller gets a notice in the main bot with the last messages, a button to open the chat and a button to return the chat to automatic mode
- ✏️ **Edit/delete tracking** — customer edits and deletions in handed-off chats are reported to the seller (can be turned off); message log is pruned automatically after a few days
- ✅ **Mark as read** — optional; requires the `can_read_messages` right from the account owner
- 🛒 **Purchase card (optional, off by default)** — when a customer wants to buy, the bot sends a product card (name, price, volume, duration, description) with a link button that opens the bot at that product. Payment and delivery always run inside the bot; no payment happens in the business chat
- ⚙️ **Admin panel** — **Admin & Access → 💼 Telegram Business**: master switch, mark-as-read, edit/delete notices, purchase card switch, list of active connections, per-connection auto-reply switch, first message (sent once at the start of each new chat), exception list of customer IDs and the list of chats handed to a human

> Inline callback buttons inside business chats are intentionally not used: URL buttons are used instead, because callback delivery in business chats has not been verified.

</details>

---

<a id="payment-gateways"></a>

## 💳 Payment Gateways

<details>
<summary><strong>Supported payment methods — click to expand</strong></summary>

| Method | Confirmation | Notes |
|---|---|---|
| 💳 Manual card-to-card | Admin | Receipt/image flow |
| 📲 Bank SMS card-to-card | Automatic | Unique invoice amount and rotating cards |
| 🏧 Aban Gateway | Automatic | API-based invoice and verification |
| 💎 Plisio | Automatic | Crypto with callback/signature validation |
| 🔵 Blupal | Automatic | Automated card-to-card |
| ⭐ NoaPay / Telegram Stars | Automatic | Telegram Stars |
| 🟡 ZarinPal | Automatic | Main bot |
| 🔵 Mr. Pardakht | Automatic | Main bot |
| 💸 Tetra98 | Automatic | Main bot |
| 💳 CubePay | Automatic | Main bot |
| 💰 NowPayments | Automatic | Crypto invoice + IPN |
| ⭐ Telegram Stars | Automatic | Native `XTR` invoices |
| 🧩 Generic Gateway | Automatic | Configure HTTP APIs without writing code |

All gateways are independent and can be enabled or disabled separately.

</details>

---

<a id="miniapp"></a>

## 📲 Telegram Mini App

<details>
<summary><strong>Click to expand</strong></summary>

The `miniapp/` directory contains a full Telegram Mini App with both a customer storefront and web administration.

### 🛍️ Customer Side

- ⚡ FastAPI backend with secure Telegram `initData` verification
- 🎨 Responsive storefront
- 🛒 Products, cart, wallet, lucky wheel, referrals and test configurations
- 🔔 Expiration and traffic alerts
- 📲 Add subscriptions to popular VPN apps using deep links
- 🎫 Support tickets and live support chat
- 🌐 Persian/English switch with automatic RTL/LTR direction

### 🛠️ Web Administration Side

- 📊 Dashboard and order exports
- 🗂️ Categories, products, panels and configuration management
- 🏢 Reseller management
- 🏷️ Discounts, lucky wheel, referrals and reminders
- 👥 User search, blocking and targeted broadcasts
- 💰 Wallet lookup and balance adjustments
- 🎨 Branding and theme customization
- 🧩 Telegram main-menu layout management
- 🎫 Ticket/support management
- 📝 System and admin logs
- 🗄️ Backup and database restore

</details>

---

<a id="admin-panel"></a>

## 🖥️ Standalone Web Admin Panel

<details>
<summary><strong>Click to expand</strong></summary>

The `admin_panel/` package provides a standalone web administration panel independent of Telegram.

- 🔐 Username/password login with independent sessions
- 👥 Separate web-admin roles and permissions
- 📊 Sales, orders, wallet and system dashboards
- 🎨 Multiple visual themes
- 📱 PWA installation on mobile
- 🌍 Global server map and health checks
- 💱 Exchange-rate management
- ✅ Order, wallet and payment approval
- 🏢 Reseller management and analytics
- 🎫 Support tickets and conversations
- 📢 Broadcast messaging
- 🗄️ Backup and restore
- 🔔 Web Push notifications
- 📱 Android app token management
- 📝 Web-admin audit logs
- 🌐 Persian/English UI with automatic RTL/LTR

### Quick Setup

**Automatic:** use the relevant `manage.sh` option for the web panel.

**Manual:**

```bash
python -m admin_panel.create_admin <username> <password>
uvicorn admin_panel.server:app --host 127.0.0.1 --port 8002
```

</details>

---

<a id="android-app"></a>

## 📱 Android Management App

<details>
<summary><strong>Click to expand</strong></summary>

The backend provides infrastructure for a native Android management application.

- 🔑 Secure long-lived administrator token (PAT)
- 🧩 Server-Driven UI
- 🔔 Firebase Cloud Messaging (FCM) push notifications
- 📋 Orders, tickets, users, products, discounts, VPN panels and web admins
- 🌍 Server map through WebView
- 🎨 Light/dark interface
- 🔕 Per-section notification controls

</details>

---

<a id="vpn-panels"></a>

## 🔌 Supported VPN Panels

<details>
<summary><strong>Click to expand</strong></summary>

| Panel | Status | Notes |
|---|---|---|
| PasarGuard | ✅ Full | Automatic provisioning |
| Marzban | ✅ Full | Automatic provisioning |
| Marzneshin | ✅ Full | Service-based provisioning |
| Hiddify | ✅ Full | API-key based |
| 3X-UI | ✅ Full | Bearer API token |
| Alireza X-UI | ✅ Full | Cookie-based login |
| Rebecca | ✅ Full | Marzban-based provider |
| S-UI | ✅ Full | Token-based API |
| WGDashboard | ✅ Full | Configuration-based |
| MikroTik / User Manager | ⚠️ Limited | Profile-based |
| IBSng | ⚠️ Limited | Admin-panel integration |
| Other panels | ➕ Extensible | Add a provider |

</details>

---

<a id="requirements"></a>

## 🖥️ Requirements

- 🐧 Ubuntu 20.04+ / Debian 11+ recommended
- 🐍 Python 3.10+
- 🖥️ Linux VPS/server with a stable public IP
- 🤖 Telegram bot token
- 🌐 Public HTTPS domain for Mini App/web panel/webhook features
- 🔑 API credentials for the payment/VPN providers you enable

> 🔒 Never publish bot tokens, `.env` files, API keys or production secrets.

---

<a id="auto-install"></a>

## 🚀 One-Line Automatic Installation

> 🌿 This is the personal fork `amir12120/Shopvpn`. Its installer is disk-lean: no heavy LibreTranslate and no pip cache by default. Full guide: [`INSTALL.md`](INSTALL.md) (English) or [`INSTALL.fa.md`](INSTALL.fa.md) (Persian).

**One command, on a fresh Ubuntu/Debian server.** It installs every missing
prerequisite, installs the bot, adds the `shopvpn` CLI command and **opens the
management menu automatically** when the install finishes:

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/amir12120/Shopvpn/main/install.sh)
```

Afterwards, typing `shopvpn` opens the same management menu at any time:

```bash
shopvpn
```

> 🧪 All install steps are printed in English.
>
> If you prefer to install prerequisites on their own first (optional):
>
> ```bash
> sudo bash <(curl -fsSL https://raw.githubusercontent.com/amir12120/Shopvpn/main/preflight.sh)
> ```

> 💾 Instead of LibreTranslate (which alone uses several GB), this installer installs Argos only and downloads just the language models you need. Add languages with `SHOPVPN_TRANSLATION_LANGS=tr,ar`; enable the heavy fallback with `SHOPVPN_INSTALL_LIBRETRANSLATE=1`.

<details>
<summary><strong>What does the installer do?</strong></summary>

1. Installs system prerequisites
2. Clones or updates the project
3. Creates the Python virtual environment
4. Installs required packages
5. Installs/updates the local translation runtime and language models automatically
6. Creates/configures `.env`
7. Creates the systemd service
8. Starts the bot and keeps it running after server reboots
9. Installs the `shopvpn` CLI command and opens the management menu

### Basic service commands

```bash
sudo systemctl status v2raybot
sudo journalctl -u v2raybot -f
sudo systemctl restart v2raybot
sudo systemctl stop v2raybot
```

The same one-line installer can be run again for future updates. Translation runtime and language models are installed/updated automatically; no manual translation setup is required.

</details>

---

<a id="manual-install"></a>

## 🛠️ Manual Installation

<details>
<summary><strong>Click to expand</strong></summary>

### 1. Clone

```bash
git clone https://github.com/amir12120/Shopvpn.git
cd Shopvpn
```

### 2. Create virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure `.env`

```bash
cp .env.example .env
nano .env
```

At minimum:

```env
BOT_TOKEN=your_bot_token
OWNER_ID=your_numeric_telegram_id
```

### 4. Start

```bash
python main.py
```

For production, use the automatic installer/systemd approach or another process manager.

</details>

---

<a id="env-vars"></a>

## ⚙️ Environment Variables

<details>
<summary><strong>Click to expand</strong></summary>

The exact variables depend on enabled features. Common configuration areas include:

| Area | Examples |
|---|---|
| Telegram | `BOT_TOKEN`, `OWNER_ID` |
| Database | database/storage paths |
| Web | domain, authentication, webhook settings |
| Payments | gateway API keys |
| VPN Panels | URLs, credentials, tokens, IDs |
| AI | provider API keys |
| Backups | destinations and SFTP credentials |
| Android | FCM credentials |

Keep production secrets outside the repository.

</details>

---

<a id="manage-sh"></a>

## 🧰 `manage.sh`

<details>
<summary><strong>Click to expand</strong></summary>

`manage.sh` is the main installation and maintenance helper.

Depending on the project version, it can handle:

- 🚀 Installation and dependency setup
- ⚙️ Environment/configuration
- ▶️ Start/stop/restart
- 📲 Mini App and web panel setup
- 🗄️ Backup/restore
- 🔌 VPN panel setup
- 📋 Logs and diagnostics
- 🔗 Integration API setup
- 🌐 Persian/English management menu
- 🌐 Local translation runtime install/repair and unused-language cleanup
- 🏭 Full cleanup / factory reset

After install, just type `shopvpn`:

```bash
shopvpn
```

Or run it straight from the repository (no install required):

```bash
chmod +x manage.sh
./manage.sh
```

> The script itself is the authoritative source for the current menu options.

</details>

---

<a id="project-structure"></a>

## 🗂️ Project Structure

<details>
<summary><strong>Click to expand</strong></summary>

```text
Shopvpn/
├── server.py
├── bot_manager.py
├── handlers_admin.py
├── payment_*.py
├── ai_support.py
├── business_chat.py
├── db/
├── miniapp/
│   ├── server.py
│   └── static/
├── admin_panel/
│   ├── server.py
│   └── static/
├── manage.sh
├── requirements*.txt
├── VERSION
├── README.md
└── README.fa.md
```

</details>

---

<a id="tech-stack"></a>

## 🧪 Technology Stack

<details>
<summary><strong>Click to expand</strong></summary>

- **Python 3.10+**
- **aiogram 3.x**
- **FastAPI**
- **SQLite**
- **HTML/CSS/JavaScript**
- **Telegram Mini Apps / WebApp authentication**
- **Firebase Cloud Messaging**
- **HTTP/API integrations for VPN panels, payments and AI providers**

</details>

---

<a id="new-features"></a>

## 🆕 Recently Added Features

<details>
<summary><strong>Click to expand</strong></summary>

### 🧾 AI Fake/Duplicate Receipt Detection

Manual card-to-card receipts are screened before they reach the admin chat. Most findings are advisory notes; the final decision stays with the admin.

- 🔁 Exact-duplicate detection through the file SHA-256 hash and the receipt reference number, plus a perceptual hash (dHash) that flags re-compressed or cropped reuse (warning only)
- 🤖 Multi-model vision analysis: Gemini, plus Groq and OpenRouter in parallel when their keys are configured
- 🔢 Deterministic OCR checks: card number (Luhn + known Iranian bank prefix), IBAN checksum, amount match in Toman or Rial, reference-number reuse
- 🕵️ Forensics: Error Level Analysis on JPEGs, image-metadata scan, screenshot status-bar time vs. send time, bank/holder-name and amount-in-words consistency
- ⚖️ Automatic rejection only for exact duplicates (when auto-reject is on) or when at least two independent signals agree
- 🎛️ Admin toggles for the check, auto-reject, strict mode and multi-model, plus a learning report that tunes per-model weights from admin approve/reject decisions

### 🌐 Automatic Translation Engine & 16 Languages

- 🗺️ Built-in language catalog: Persian, English, Turkish, Arabic, Russian, German, French, Spanish, Italian, Portuguese, Chinese, Japanese, Korean, Dutch, Polish and Ukrainian
- 🏠 Offline-first: local Argos Translate and LibreTranslate need no API key; public translation APIs are not used unless explicitly allowed; Gemini/OpenRouter are optional providers
- 🛡️ Quality guard: placeholders, URLs, markup, code and emoji are protected and verified, and broken provider output is rejected
- ⚡ Strings missing from a language catalog are translated on the fly just before a message is sent
- 📊 Admin-panel translation dashboard: status, health, providers, history, live logs, per-language and bulk sync
- ✍️ Admin-written content (broadcasts, product names, etc.) is never auto-translated; background notifications use each recipient's language
- 🧰 Languages are chosen at install time; `manage.sh` options 27, 28 and 30 repair the runtime, remove LibreTranslate and delete unwanted languages to free disk space

### 🧠 AI Assistant Account Actions

Beyond answering questions, the assistant can prepare account actions that the bot then executes through its own validated flows.

- 🛒 Purchase with wallet and 🔄 renewal from wallet (with cost calculation), only after a separate explicit confirmation message from the user
- 🔁 Auto-renew toggle, QR code, individual configs, enable/disable, rename, new access link, transfer to another user and service history
- 🗑️ Deleting a service always ends with a final confirmation button
- 🎟️ Discount-code check, referral info, recent tickets and server countries
- 🙋 Refunds, complaints and financial disputes are still escalated to human support

### ➕ Add Existing Account

- 🔗 Users attach a service they already own by pasting its subscription link or (optionally) the config username; it is matched against your connected panels
- 🔒 Conflict protection: a config already linked to another account is refused, and repeated failures temporarily block the user
- 🎛️ The button and the username option can be switched off separately from the admin panel

### 📚 Contextual Tutorials

- 📍 Tutorials can be attached to specific bot sections: main-menu buttons, the purchase flow, each payment method, wallet actions and more
- 📚 A "Tutorial" button is added automatically under the matching page, with no handler changes needed
- 🎁 A tutorial can also be offered right after a successful purchase

### 📜 Terms & Conditions

- ✅ Admins can require users to accept written terms before using the bot
- 📲 The Mini App has its own accept flow, so acceptance is shared across both

### 🧾 Renewal Warnings & Log

- ⚠️ Users see the current state of a service (remaining time and traffic) before they confirm a renewal
- 📣 Every renewal (full, volume, time or extra users) is logged to the admin report group with before/after values

### 🧰 More `manage.sh` Options

| Option | Action |
|:---:|---|
| 27 | Install/repair the local translation runtime (automatic) |
| 28 | Remove LibreTranslate |
| 29 | Full cleanup / factory reset |
| 30 | Remove unwanted translation languages (free disk space) |

</details>

---

<a id="additional-features"></a>

## 🔎 Additional Features

<details>
<summary><strong>Click to expand</strong></summary>

- 🩺 VPN panel health monitoring
- 📊 Advanced sales and activity analytics
- 📣 Topic-based reporting
- 🎁 Bulk gifts
- 🧹 Expired-service cleanup
- 🔌 Token-scoped Integration API
- ⏸️ On-hold services
- 📦 Panel capacity limits
- 📍 Service migration
- 💰 Bulk price editing with undo
- 💸 Cashback
- 🎁 Wallet gift codes
- 🪙 Coins and lottery
- ⭐ Order/service ratings
- 💸 Wallet transfers
- 🧾 Wallet transaction ledger
- 📦 Configurable delivery modes and QR backgrounds
- 🔗 Multi-domain subscription links
- 🧩 Custom configuration-builder products
- 🛠️ 3X-UI utilities
- 🗄️ Multi-bot backup/restore
- 📨 Secondary backup destinations
- 🏭 Owner-only factory reset
- ⏰ Scheduled broadcasts
- 🔘 Automatic Mini App menu-button synchronization
- 🔗 Advertising/deep-link tracking
- 🟢 Admin-presence routing
- 🔔 Pending-invoice push notifications
- 🖼️ Mini App banner/catalog management
- 🔀 Multi-level referral commissions and fraud suspension
- 💳 Reseller postpaid credit
- 📉 Reseller-tier quantity discounts
- 🌐 Resellers without their own Telegram bot through the web API

</details>

---

<a id="contributing"></a>

## 🤝 Contributing & License

<details>
<summary><strong>Click to expand</strong></summary>

Bug reports, feature suggestions, documentation improvements and pull requests are welcome.

Before opening a pull request:

1. Keep secrets and production credentials out of the repository.
2. Preserve database compatibility where possible.
3. Run relevant Python/JavaScript checks.
4. Keep Persian and English user-facing text synchronized through the i18n layer.

### 📄 License

This project is released under the **MIT License**.

### 👤 Author

Created by **Mehdi Rafatpanah**

- Telegram: [@celenor](https://t.me/celenor)
- GitHub: [@mehdirafatpanah](https://github.com/mehdirafatpanah)

</details>

---

## 🌍 Documentation Languages

- 🇬🇧 **English:** `README.md`
- 🇮🇷 **Persian:** `README.fa.md`
- 🇷🇺 **Russian:** `README.ru.md`
- 🇨🇳 **Chinese:** `README.zh.md`

The application supports multiple UI languages with persisted user language selection and automatic RTL/LTR switching. The built-in catalog has 16 languages (Persian, English, Turkish, Arabic, Russian, German, French, Spanish, Italian, Portuguese, Chinese, Japanese, Korean, Dutch, Polish, Ukrainian); they are chosen at install time and managed from the admin panel's language manager, which auto-generates the in-app translations.
