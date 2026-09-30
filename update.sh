#!/bin/bash
# اسکریپت آپدیت بات (نسخه هماهنگ با سرویس systemd که install.sh می‌سازد)
# استفاده: ./update.sh "توضیح کوتاه تغییر"

set -e

cd "$(dirname "$0")"

COMMIT_MSG="${1:-آپدیت بدون توضیح}"
SERVICE_NAME="v2raybot"

echo "📦 ثبت تغییرات در گیت..."
git add .
git commit -m "$COMMIT_MSG" || echo "  (تغییری برای commit نبود)"
git push || echo "  ⚠️ push انجام نشد (شاید remote تنظیم نیست یا نیاز به توکن دارد)"

echo "🐍 آپدیت پکیج‌ها..."
# بدون نگه‌داشتن کش pip (صرفه‌جویی در فضای دیسک)
export PIP_NO_CACHE_DIR=1
source venv/bin/activate
pip install -q --no-cache-dir -r requirements.txt
deactivate
venv/bin/python3 -m pip cache purge >/dev/null 2>&1 || true
rm -rf "$HOME/.cache/pip" 2>/dev/null || true

echo "🌍 به‌روزرسانی خودکار موتور ترجمه و مدل‌های زبان..."
bash "$PWD/setup_local_translation.sh" || echo "  ⚠️ به‌روزرسانی موتور ترجمه کامل نشد؛ در اجرای بعدی دوباره تلاش می‌شود."

echo "🔄 ری‌استارت سرویس بات..."
sudo systemctl restart "$SERVICE_NAME"
sleep 2

echo "✅ انجام شد."
sudo systemctl status "$SERVICE_NAME" --no-pager -l | head -10

