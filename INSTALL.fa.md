# 🛰️ راهنمای نصب ShopVPN (فورک شخصی `amir12120/Shopvpn`)

این سند مخصوص **فورک شخصی** است و نصب را روی **Ubuntu 22.04** (و Debian 11+) به‌صورت سبک و آگاه‌به‌دیسک توضیح می‌دهد.

- 🔗 مخزن: <https://github.com/amir12120/Shopvpn>
- 🧩 پروژه اصلی (upstream): `mehdirafatpanah/Shopvpn`

> نکته: این فورک نصب‌کننده را «سبک» کرده تا **مصرف دیسک به‌شدت کاهش پیدا کند** (جزئیات در بخش [رفع مشکل فضای دیسک](#disk)).

---

## 📋 فهرست

1. [پیش‌نیازها](#prereqs)
2. [نصب پیش‌نیازها (یک‌خطی)](#prereq-install)
3. [نصب یک‌خطی بات](#install)
4. [رفع مشکل اشغال زیاد فضای دیسک](#disk)
5. [زبان‌های ترجمه و LibreTranslate اختیاری](#langs)
6. [مدیریت و اجرای دائمی](#manage)
7. [عیب‌یابی](#troubleshoot)

---

<a id="prereqs"></a>

## ۱) پیش‌نیازها

| مورد | حداقل | توضیح |
|---|---|---|
| سیستم‌عامل | Ubuntu 20.04+ / Debian 11+ | پیشنهاد: Ubuntu 22.04 |
| Python | 3.10+ | Ubuntu 22.04 به‌صورت پیش‌فرض Python 3.10 دارد ✅ |
| فضای دیسک آزاد | ~۱.۵ گیگابایت | نصب سبک؛ برای رشد لاگ/بکاپ ۲ گیگ به بالا بهتر است |
| RAM | ۱ گیگابایت (پیشنهاد ۲) | ترجمه محلی به RAM هم نیاز دارد |
| دسترسی | root / sudo | برای نصب پکیج و ساخت سرویس systemd |
| اینترنت | پایدار | برای کلون گیت و دانلود مدل‌ها |
| اختیاری (وب‌هوک/پنل) | دامنه با DNS روی IP سرور | فقط اگر حالت Webhook یا Mini App می‌خواهی |
| تلگرام | توکن بات از [@BotFather](https://t.me/BotFather) و آیدی عددی ادمین | برای ساخت `.env` |

پکیج‌های سیستمی که نصب می‌شوند:

- پایه: `git`, `curl`, `ca-certificates`, `python3`, `python3-pip`, `python3-venv`
- ساخت (اگر wheel آماده نبود): `build-essential`, `python3-dev`, `pkg-config`, `libffi-dev`, `libssl-dev`, `zlib1g-dev`, `libjpeg-dev`
- اختیاری وب‌هوک: `nginx`, `certbot`, `python3-certbot-nginx`

---

<a id="prereq-install"></a>

## ۲) نصب پیش‌نیازها (یک‌خطی، قبل از نصب اصلی)

برای اینکه نصب اصلی وسط کار روی apt گیر نکند، اول این را اجرا کن:

```bash
sudo bash <(curl -fsSL https://raw.githubusercontent.com/amir12120/Shopvpn/main/preflight.sh)
```

- فقط بررسی بدون تغییر: `bash preflight.sh --check`
- همراه با nginx و certbot برای وب‌هوک: `sudo bash preflight.sh --with-web`

خروجی این اسکریپت، نسخهٔ سیستم‌عامل، نسخهٔ پایتون، فضای آزاد دیسک و پکیج‌های ناموجود را نشان می‌دهد و همه‌چیز را نصب می‌کند (idempotent است؛ اجرای دوباره بی‌خطر است).

---

<a id="install"></a>

## ۳) نصب یک‌خطی بات (اختصاصی این فورک)

پس از نصب پیش‌نیازها، فقط این دستور:

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/amir12120/Shopvpn/main/install.sh)
```

این اسکریپت:

1. پیش‌نیازهای سیستمی را بررسی/نصب می‌کند.
2. کد را از همین فورک کلون (یا آپدیت) می‌کند → `$HOME/v2ray_bot`.
3. محیط مجازی می‌سازد و پکیج‌ها را **بدون کش pip** نصب می‌کند.
4. توکن بات و آیدی ادمین را می‌پرسد و `.env` را می‌سازد (اگر از قبل باشد، دست‌نخورده می‌ماند).
5. مدل‌های ترجمهٔ محلی را **فقط برای زبان‌های موردنیاز** نصب می‌کند.
6. سرویس `systemd` به نام `v2raybot` می‌سازد و بات را اجرا می‌کند.

> 🔁 اجرای دوبارهٔ همین دستور = آپدیت (idempotent). فایل `.env` و دیتابیس حفظ می‌شود.

---

<a id="disk"></a>

## ۴) رفع مشکل اشغال زیاد فضای دیسک

### چرا فضای زیادی اشغال می‌شد؟

نصب‌کنندهٔ قبلی روی هر سرور، علاوه بر Argos، **LibreTranslate** را هم نصب می‌کرد. مشکل اصلی دقیقاً همین بود:

| عامل مصرف فضا | حجم تقریبی | توضیح |
|---|---|---|
| LibreTranslate (+ PyTorch / CTranslate2 / transformers) | **۲ تا ۴+ گیگ** فقط وابستگی‌ها | ایمیج کامل LibreTranslate حدود **۱۶ گیگابایت** است و روی دیسکی با ~۸ گیگ آزاد حتی `pip install` آن شکست می‌خورد |
| مدل‌های Argos برای همهٔ زبان‌های کاتالوگ | **~۱.۵ گیگ** | هر جفت‌زبان به‌طور میانگین ~۱۰۰ مگابایت (همهٔ مدل‌های Argos روی هم ~۷ گیگ) |
| مدل‌های تکراری LibreTranslate | **چند صد مگ تا چند گیگ** | LibreTranslate مدل‌ها را جدا از Argos هم دانلود می‌کرد |
| کش pip | **۱ تا ۳ گیگ** | چرخ‌های دانلودشده (مثل torch) در `~/.cache/pip` می‌ماندند |

جمع این‌ها می‌توانست نصب را به **۸ تا ۱۲ گیگابایت** برساند — و روی VPSهای کوچک باعث پرشدن دیسک شود.

### چه چیزی درست شد؟

- ✅ **LibreTranslate به‌صورت پیش‌فرض نصب نمی‌شود.** کافی است Argos، چون خود اپ هم اول Argos را امتحان می‌کند و LibreTranslate فقط یک fallback دوم است.
- ✅ **مدل‌ها فقط برای زبان‌های موردنیاز** دانلود می‌شوند (پیش‌فرض فقط `fa`).
- ✅ **کش pip نگه داشته نمی‌شود** (`PIP_NO_CACHE_DIR=1` + پاکسازی کش در پایان).
- ✅ اگر LibreTranslate را اختیاری فعال کنی، مدل‌های Argos بین هر دو **مشترک** می‌شوند (دانلود تکراری حذف می‌شود).

نتیجه: مصرف نصب سبک معمولاً حدود **۱ تا ۱.۵ گیگابایت** است (به‌جای ۸+ گیگ).

### آزاد کردن فضا روی نصب‌های قبلی

اگر قبلاً نسخهٔ سنگین را نصب کرده‌ای، LibreTranslate را حذف کن:

- از منوی `manage.sh` گزینهٔ ۲۸ (حذف LibreTranslate)، یا دستور دستی زیر روی سرور:

```bash
sudo systemctl disable --now shopvpn-libretranslate 2>/dev/null
sudo rm -f /etc/systemd/system/shopvpn-libretranslate.service && sudo systemctl daemon-reload
rm -rf ~/v2ray_bot/translation-venv ~/v2ray_bot/.translation-home
rm -rf ~/.cache/pip /root/.cache/pip
df -h /        # بررسی فضای آزادشده
```

---

<a id="langs"></a>

## ۵) زبان‌های ترجمه و LibreTranslate اختیاری

پیش‌فرض فقط زبان **فارسی/انگلیسی** (`en_fa` و `fa_en`) نصب می‌شود. اگر می‌خواهی زبان‌های بیشتری به‌صورت محلی ترجمه شوند:

```bash
# نصب چند زبان مشخص (مثلاً ترکی و عربی)
SHOPVPN_TRANSLATION_LANGS="tr,ar" bash ~/v2ray_bot/setup_local_translation.sh

# یا همهٔ زبان‌های کاتالوگ (~۱.۵ گیگ+)
SHOPVPN_TRANSLATION_LANGS=all bash ~/v2ray_bot/setup_local_translation.sh
```

> می‌توانی همین کار را از منوی `manage.sh` گزینهٔ **۲۹** هم انجام دهی.

**LibreTranslate (سنگین، اختیاری):** فقط اگر کیفیت/زبان بیشتری لازم داری:

```bash
SHOPVPN_INSTALL_LIBRETRANSLATE=1 bash ~/v2ray_bot/setup_local_translation.sh
```

> ⚠️ این کار چند گیگابایت فضا می‌برد. برای اکثر فروشگاه‌ها لازم نیست.

---

<a id="manage"></a>

## ۶) مدیریت و اجرای دائمی

بات به‌صورت سرویس `systemd` نصب می‌شود:

```bash
sudo systemctl status v2raybot      # وضعیت
sudo journalctl -u v2raybot -f      # لاگ زنده
sudo systemctl restart v2raybot     # ری‌استارت
sudo systemctl stop v2raybot        # توقف
```

پنل مدیریت متنی (نصب/آپدیت/بکاپ/پنل وب/زبان‌ها):

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/amir12120/Shopvpn/main/manage.sh)
```

---

<a id="troubleshoot"></a>

## ۷) عیب‌یابی کوتاه

| مشکل | راه‌حل |
|---|---|
| نصب روی apt گیر می‌کند | اول `preflight.sh` را اجرا کن؛ متغیرهای `DEBIAN_FRONTEND=noninteractive` و `NEEDRESTART_*` در اسکریپت ست شده‌اند |
| کلون گیت شکست می‌خورد / پرامپت یوزر/پس می‌خواهد | اسکریپت به‌طور خودکار از آرشیو `codeload.github.com` استفاده می‌کند (بدون نیاز به اعتبار) |
| دیسک پر شده | بخش [رفع مشکل فضای دیسک](#disk)؛ LibreTranslate را حذف و کش pip را پاک کن |
| بات بالا نمی‌آید | `sudo journalctl -u v2raybot -n 80 --no-pager` را ببین؛ معمولاً `BOT_TOKEN`/`OWNER_ID` اشتباه است |
| ترجمهٔ یک زبان کار نمی‌کند | آن زبان را نصب کن (بخش [زبان‌ها](#langs)) |
| Python قدیمی است | مطمئن شو Ubuntu 22.04 باشد یا python3.10+ نصب کن |

---

## 🔒 نکات امنیتی

- هرگز `BOT_TOKEN`، فایل `.env` یا کلیدهای API را در گیت‌هاب/چت عمومی نگذار.
- اگر توکن لو رفت، فوراً از [@BotFather](https://t.me/BotFather) با `/revoke` توکن جدید بگیر.

## 📄 مجوز

MIT — پروژهٔ اصلی ساختهٔ **Mehdi Rafatpanah** ([@mehdirafatpanah](https://github.com/mehdirafatpanah)).
