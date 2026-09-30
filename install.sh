#!/bin/bash
# اسکریپت نصب/آپدیت خودکار بات فروش کانفیگ V2Ray
#
# استفاده (این ریپازیتوری فورک شخصی است):
#
#   bash <(curl -fsSL https://raw.githubusercontent.com/amir12120/Shopvpn/main/install.sh)
#
# نصب سبک و آگاه به فضای دیسک: به‌صورت پیش‌فرض فقط Argos (بدون LibreTranslate)
# و بدون نگه‌داشتن کش pip نصب می‌شود تا فضای دیسک کم مصرف شود.
# این اسکریپت هم برای نصب اولیه کار می‌کند و هم برای آپدیت‌های بعدی (idempotent است).

set -e

# جلوگیری از گیر کردن apt پشت پنجره‌های تعاملی (مثل پرسش needrestart برای ری‌استارت سرویس‌ها)
export DEBIAN_FRONTEND=noninteractive
export NEEDRESTART_MODE=a
export NEEDRESTART_SUSPEND=1

# ============================================================================
# تنظیمات - این خط را با آدرس مخزن گیت‌هاب خودت جایگزین کن
# ============================================================================
REPO_URL="https://github.com/amir12120/Shopvpn.git"
INSTALL_DIR="$HOME/v2ray_bot"
SERVICE_NAME="v2raybot"

echo "🚀 شروع نصب/آپدیت بات فروش کانفیگ V2Ray"
echo "──────────────────────────────────────────"

# ----------------------------------------------------------------------------
# ۱. نصب پیش‌نیازهای سیستمی
# ----------------------------------------------------------------------------
echo "📦 بررسی و نصب پیش‌نیازها (git, python3, pip, venv)..."
sudo env DEBIAN_FRONTEND=noninteractive NEEDRESTART_MODE=a NEEDRESTART_SUSPEND=1 apt-get update -qq
timeout 180 sudo env DEBIAN_FRONTEND=noninteractive NEEDRESTART_MODE=a NEEDRESTART_SUSPEND=1 \
    apt-get install -y -qq git curl ca-certificates python3 python3-pip python3-venv \
    build-essential python3-dev pkg-config libffi-dev libssl-dev zlib1g-dev libjpeg-dev > /dev/null

# هرگز کش دانلود pip را نگه نداریم (چند گیگابایت روی دیسک‌های کوچک).
export PIP_NO_CACHE_DIR=1
export PIP_DISABLE_PIP_VERSION_CHECK=1

# ----------------------------------------------------------------------------
# ۲. دریافت یا آپدیت کد از گیت‌هاب
#    نکته: بعضی سرورها (خصوصاً VPSهای ارزان) با پروتکل git-over-https توسط
#    گیت‌هاب مسدود/محدود می‌شوند و به‌جای کلون عادی، درخواست یوزرنیم/پسورد
#    نشان داده می‌شود. برای جلوگیری از گیر کردن اسکریپت روی این پرامپت،
#    اول با گیت (بدون امکان پرامپت تعاملی) تلاش می‌کنیم و در صورت شکست،
#    به دانلود مستقیم آرشیو (tar.gz) که این محدودیت را ندارد سوییچ می‌کنیم.
# ----------------------------------------------------------------------------
GITHUB_OWNER="amir12120"
GITHUB_REPO="Shopvpn"
GITHUB_BRANCH="main"
export GIT_TERMINAL_PROMPT=0

fetch_project_code() {
    local ok=0
    if [ -d "$INSTALL_DIR/.git" ]; then
        echo "🔄 مخزن از قبل موجود است، در حال دریافت آخرین تغییرات..."
        if git -C "$INSTALL_DIR" pull --quiet; then ok=1; fi
    else
        echo "📥 دریافت پروژه از گیت‌هاب..."
        if git clone --quiet "$REPO_URL" "$INSTALL_DIR"; then ok=1; fi
    fi

    if [ "$ok" = "1" ]; then
        return 0
    fi

    echo "⚠️ دسترسی git مسدود شد، در حال دریافت از طریق آرشیو مستقیم..."
    local tmp_tar tmp_dir
    tmp_tar=$(mktemp)
    tmp_dir=$(mktemp -d)
    if ! curl -fsSL "https://codeload.github.com/${GITHUB_OWNER}/${GITHUB_REPO}/tar.gz/refs/heads/${GITHUB_BRANCH}" -o "$tmp_tar"; then
        echo "❌ دانلود آرشیو پروژه هم ناموفق بود. اتصال اینترنت سرور را بررسی کن."
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

fetch_project_code
cd "$INSTALL_DIR"

# ----------------------------------------------------------------------------
# ۳. ساخت virtual environment و نصب پکیج‌ها
# ----------------------------------------------------------------------------
echo "🐍 آماده‌سازی محیط پایتون..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install -q --no-cache-dir -r requirements.txt
deactivate

# ----------------------------------------------------------------------------
# ۴. تنظیم فایل .env (فقط دفعه اول، چون این فایل هیچ‌وقت در گیت نیست)
# ----------------------------------------------------------------------------
if [ ! -f "$INSTALL_DIR/.env" ]; then
    echo ""
    echo "🔑 فایل .env پیدا نشد. اطلاعات زیر را وارد کن:"
    read -rp "توکن بات (از BotFather): " BOT_TOKEN_INPUT
    read -rp "آیدی عددی ادمین (مثلاً از @userinfobot): " OWNER_ID_INPUT
    cat > "$INSTALL_DIR/.env" <<EOF
BOT_TOKEN=$BOT_TOKEN_INPUT
OWNER_ID=$OWNER_ID_INPUT
EOF

    echo ""
    echo "بات چطور آپدیت‌های تلگرام را دریافت کند؟"
    echo "  1) Polling  (پیش‌فرض - ساده‌تر، نیاز به دامنه/SSL ندارد)"
    echo "  2) Webhook  (نیاز به یک دامنه که DNS آن روی IP همین سرور تنظیم شده)"
    read -rp "انتخاب [1]: " BOT_MODE_CHOICE
    BOT_MODE_CHOICE="${BOT_MODE_CHOICE:-1}"

    if [ "$BOT_MODE_CHOICE" = "2" ]; then
        read -rp "دامنه‌ای که برای وب‌هوک بات استفاده می‌کنی (مثلاً bot.example.com): " WEBHOOK_DOMAIN
        if [ -z "$WEBHOOK_DOMAIN" ]; then
            echo "⚠️ دامنه وارد نشد؛ بات با Polling راه‌اندازی می‌شود (بعداً از منوی manage.sh می‌توانی وب‌هوک را فعال کنی)."
        else
            WEBHOOK_PORT=8010
            echo "📦 نصب nginx و certbot..."
            sudo env DEBIAN_FRONTEND=noninteractive NEEDRESTART_MODE=a NEEDRESTART_SUSPEND=1 \
                apt-get install -y -qq nginx certbot python3-certbot-nginx > /dev/null

            echo "🌐 تنظیم nginx برای $WEBHOOK_DOMAIN..."
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
                echo "⛔️ کانفیگ nginx خطا دارد؛ بات با Polling راه‌اندازی می‌شود."
            else
                sudo systemctl reload nginx
                echo "🔐 دریافت گواهی SSL (Let's Encrypt)..."
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
                    echo "✅ حالت Webhook تنظیم شد: https://$WEBHOOK_DOMAIN"
                else
                    echo "⛔️ دریافت SSL ناموفق بود؛ بات با Polling راه‌اندازی می‌شود (بعداً از منوی manage.sh دوباره امتحان کن)."
                fi
            fi
        fi
    fi
    echo "✅ فایل .env ساخته شد."
else
    echo "✅ فایل .env از قبل موجود است، دست‌نخورده باقی می‌ماند."
fi

# ----------------------------------------------------------------------------
# ۵. نصب و راه‌اندازی خودکار موتور ترجمه محلی
#    کاربر نباید هیچ مدل Argos یا LibreTranslate را دستی نصب کند.
# ----------------------------------------------------------------------------
echo "🌍 نصب سبک موتور ترجمه محلی و مدل‌های زبان (بدون LibreTranslate سنگین)..."
# برای زبان‌های بیشتر: SHOPVPN_TRANSLATION_LANGS="tr,ar" و برای fallback سنگین
# LibreTranslate: SHOPVPN_INSTALL_LIBRETRANSLATE=1
if ! bash "$INSTALL_DIR/setup_local_translation.sh"; then
    echo "⚠️ نصب موتور ترجمه محلی کامل نشد؛ بات ادامه می‌دهد و در آپدیت بعدی دوباره تلاش می‌کند."
fi

# آزادسازی فضای هدررفته: کش‌های pip بعد از ساخت venv بی‌فایده‌اند.
venv/bin/python3 -m pip cache purge >/dev/null 2>&1 || true
rm -rf "$HOME/.cache/pip" 2>/dev/null || true
[ "$(id -u)" -eq 0 ] && rm -rf /root/.cache/pip 2>/dev/null || true
echo "💾 فضای مصرفی -> venv: $(du -sh "$INSTALL_DIR/venv" 2>/dev/null | cut -f1) | کل پروژه: $(du -sh "$INSTALL_DIR" 2>/dev/null | cut -f1)"

# ----------------------------------------------------------------------------
# ۶. ساخت systemd service برای اجرای دائمی و خودکار بعد از ری‌بوت سرور
# ----------------------------------------------------------------------------
echo "⚙️ تنظیم سرویس systemd برای اجرای همیشگی بات..."
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
sudo systemctl restart "$SERVICE_NAME"

sleep 2

echo ""
echo "──────────────────────────────────────────"
if sudo systemctl is-active --quiet "$SERVICE_NAME"; then
    echo "✅ بات با موفقیت نصب/آپدیت شد و در حال اجراست."
else
    echo "⚠️ بات اجرا نشد. برای دیدن جزئیات خطا:"
    echo "   sudo journalctl -u $SERVICE_NAME -n 50 --no-pager"
fi
echo ""
echo "دستورات مفید:"
echo "  وضعیت بات:    sudo systemctl status $SERVICE_NAME"
echo "  لاگ زنده:      sudo journalctl -u $SERVICE_NAME -f"
echo "  ری‌استارت:     sudo systemctl restart $SERVICE_NAME"
echo "  متوقف کردن:    sudo systemctl stop $SERVICE_NAME"
echo "──────────────────────────────────────────"
