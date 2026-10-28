#!/bin/bash
# اجراکننده‌ی آپدیت/برگشت — توسط بات (updater.py) جدا از پروسه‌ی بات اجرا می‌شود.
# استفاده: update_runner.sh update|rollback
# متغیرها: INSTALL_DIR SERVICE_NAME REPO_OWNER REPO_NAME REPO_BRANCH (و UPDATE_DETACHED=1)
#
# این فایل باید کنار updater.py در ریشه‌ی پروژه بماند؛ اگر در mergeهای upstream
# حذف شود، دکمه‌ی «آپدیت پروژه» در پنل مدیریت با پیام
# «فایل update_runner.sh کنار پروژه پیدا نشد» متوقف می‌شود.
set -u

MODE="${1:-update}"
INSTALL_DIR="${INSTALL_DIR:-$(cd "$(dirname "$0")" && pwd)}"
SERVICE_NAME="${SERVICE_NAME:-v2raybot}"
# این فورک فقط از مخزن خودش آپدیت می‌گیرد؛ هرگز پیش‌فرض upstream.
REPO_OWNER="${REPO_OWNER:-amir12120}"
REPO_NAME="${REPO_NAME:-Shopvpn}"
REPO_BRANCH="${REPO_BRANCH:-main}"
export GIT_TERMINAL_PROMPT=0

cd "$INSTALL_DIR" || exit 1
mkdir -p logs backups
exec >>"logs/update.log" 2>&1
echo "=================== $(date '+%F %T') mode=$MODE ==================="

RESULT="$INSTALL_DIR/update_result.txt"
PY="$INSTALL_DIR/venv/bin/python3"
[ -x "$PY" ] || PY="$(command -v python3)"
SUDO=""
[ "$(id -u)" != "0" ] && SUDO="sudo -n"
TS="$(date +%Y%m%d_%H%M%S)"
FROM_VERSION="$(tr -d '[:space:]' < VERSION 2>/dev/null || echo '?')"
SNAP="$INSTALL_DIR/backups/code_before_update_${TS}.tar.gz"
OLD_HEAD=""
[ -d .git ] && OLD_HEAD="$(git rev-parse HEAD 2>/dev/null || true)"

log() { echo "[$(date '+%T')] $*"; }

write_result() { # status reason
    printf 'status=%s\nreason=%s\nfrom=%s\nto=%s\n' "$1" "${2:-}" "$FROM_VERSION" \
        "$(tr -d '[:space:]' < VERSION 2>/dev/null || echo '?')" > "$RESULT"
}

main_nrestarts() {
    systemctl show -p NRestarts --value "$SERVICE_NAME" 2>/dev/null \
        | tr -d '[:space:]' || echo 0
}

# تعداد ری‌استارت خودکار قبل از آپدیت؛ برای تشخیص خرابی بعد از ری‌استارت.
# (مقدار مطلق NRestarts همیشه صفر نیست و مقایسه‌ی «> 0» باعث rollback اشتباه
# می‌شد؛ فقط افزایش آن بعد از این آپدیت نشانه‌ی خرابی است.)
NR_BEFORE="$(main_nrestarts)"
[ -n "$NR_BEFORE" ] || NR_BEFORE=0

extra_services() {
    for suffix in miniapp adminpanel api sub store; do
        if systemctl cat "${SERVICE_NAME}-${suffix}.service" >/dev/null 2>&1; then
            echo "${SERVICE_NAME}-${suffix}"
        fi
    done
}

restart_all() {
    for svc in $(extra_services); do
        log "restart $svc"
        $SUDO systemctl restart "$svc" || log "WARN: restart $svc failed"
    done
    log "restart $SERVICE_NAME (last)"
    $SUDO systemctl restart "$SERVICE_NAME" || return 1
    return 0
}

healthy() {
    # مثل manage.sh: سه بار پشت سر هم فعال بودن در بازه‌ی ۳۰ ثانیه.
    local stable=0 poll=0
    while [ "$poll" -lt 30 ]; do
        if $SUDO systemctl is-active --quiet "$SERVICE_NAME"; then
            stable=$((stable + 1))
            [ "$stable" -ge 3 ] && break
        else
            stable=0
        fi
        sleep 2
        poll=$((poll + 2))
    done
    [ "$stable" -ge 3 ] || return 1
    local after
    after="$(main_nrestarts)"
    [ -n "$after" ] || after="$NR_BEFORE"
    if [ "$after" -gt "$NR_BEFORE" ] 2>/dev/null; then
        log "service restarted automatically after update (NRestarts $NR_BEFORE -> $after)"
        return 1
    fi
    return 0
}

restore_snapshot() { # $1 = فایل tar.gz، $2 = کامیت متناظر (اختیاری)
    log "restoring code from $1 (head=${2:-?})"
    tar -xzf "$1" -C "$INSTALL_DIR" || return 1
    if [ -n "${2:-}" ] && [ -d .git ]; then
        # HEAD باید دقیقاً همان کامیت بکاپ باشد، وگرنه آپدیت بعدی دوباره کد
        # خراب را از origin می‌آورد و «برگشت» عملاً بی‌اثر می‌شود.
        git reset -q --mixed "$2" 2>/dev/null || true
    fi
    return 0
}

prune_backups() {
    ls -1t backups/code_before_update_*.tar.gz 2>/dev/null | tail -n +4 | xargs -r rm -f
    ls -1t backups/code_before_update_*.tar.gz.head 2>/dev/null | tail -n +4 | xargs -r rm -f
    ls -1t backups/db_before_update_*.db 2>/dev/null | tail -n +4 | xargs -r rm -f
}

do_rollback_after_failure() { # $1 reason
    log "ROLLBACK: $1"
    if ! restore_snapshot "$SNAP" "$OLD_HEAD"; then
        write_result failed "$1 (و برگشت خودکار هم ناموفق بود؛ بکاپ: $SNAP)"
        exit 1
    fi
    "$PY" -m pip install -r requirements.txt --quiet 2>&1 | tail -n 3 \
        || log "WARN: pip install during rollback failed"
    restart_all
    if healthy; then
        write_result rolled_back "$1"
    else
        write_result failed "$1 (بعد از برگشت، سرویس پایدار بالا نیامد)"
    fi
    exit 1
}

# ----------------------------------------------------------------------------
if [ "$MODE" = "rollback" ]; then
    LAST="$(ls -1t backups/code_before_update_*.tar.gz 2>/dev/null | head -n 1)"
    [ -n "$LAST" ] || { write_result failed "نسخه‌ی پشتیبان پیدا نشد"; exit 1; }
    LAST_HEAD="$(cat "$LAST.head" 2>/dev/null || true)"
    restore_snapshot "$LAST" "$LAST_HEAD" \
        || { write_result failed "بازیابی بکاپ ناموفق بود"; exit 1; }
    "$PY" -m pip install -r requirements.txt --quiet 2>&1 | tail -n 3 \
        || log "WARN: pip install during rollback failed"
    restart_all
    if healthy; then
        write_result rollback_ok ""
    else
        write_result failed "بعد از برگشت سرویس پایدار بالا نیامد"
    fi
    exit 0
fi

# ---------------------------- update ----------------------------------------
log "from version $FROM_VERSION"

log "backup: code snapshot"
tar -czf "$SNAP" --exclude=./venv --exclude=./.git --exclude=./backups --exclude=./logs \
    --exclude=./reseller_dbs --exclude='./*.db' --exclude='./*.db-*' --exclude=./.env \
    --exclude='__pycache__' -C "$INSTALL_DIR" . \
    || { write_result failed "گرفتن بکاپ کد ناموفق بود"; exit 1; }
# کامیت متناظر با همین بکاپ را کنار آن نگه می‌داریم تا «برگشت» HEAD را هم
# به همان نسخه برگرداند، نه به کامیت خراب فعلی.
printf '%s\n' "$OLD_HEAD" > "$SNAP.head"

log "backup: database"
"$PY" - "$INSTALL_DIR" "$TS" <<'PYEOF' || log "WARN: db backup failed"
import os, sqlite3, sys
base, ts = sys.argv[1], sys.argv[2]
src = os.path.join(base, "bot_database.db")
if os.path.exists(src):
    dst = os.path.join(base, "backups", f"db_before_update_{ts}.db")
    a = sqlite3.connect(src); b = sqlite3.connect(dst)
    with b: a.backup(b)
    a.close(); b.close()
    print("db backup ->", dst)
PYEOF

log "fetch code"
fetched=0
if [ -d .git ]; then
    # reset --hard عمداً: دکمه‌ی آپدیت باید کد سرور را دقیقاً با GitHub یکی کند؛
    # تغییرات محلی سرور (که با روش آرشیو هم بازنویسی می‌شد) نگه داشته نمی‌شوند.
    # دیتابیس، .env و پوشه‌های venv/backups خارج از گیت هستند و دست نمی‌خورند.
    if git fetch --quiet origin "$REPO_BRANCH" \
        && git reset --hard --quiet "origin/$REPO_BRANCH"; then
        fetched=1
        log "git HEAD -> $(git rev-parse --short HEAD 2>/dev/null)"
    else
        log "git fetch/reset failed -> archive fallback"
    fi
fi
if [ "$fetched" = "0" ]; then
    tmp_tar="$(mktemp)"
    if ! curl -fsSL --max-time 180 \
        "https://codeload.github.com/${REPO_OWNER}/${REPO_NAME}/tar.gz/refs/heads/${REPO_BRANCH}" \
        -o "$tmp_tar"; then
        rm -f "$tmp_tar"
        write_result failed "دانلود نسخه‌ی جدید از GitHub ناموفق بود"
        exit 1
    fi
    if ! tar -xzf "$tmp_tar" -C "$INSTALL_DIR" --strip-components=1 \
        --exclude='.env' --exclude='*.db' --exclude='*.db-*' --exclude='venv' \
        --exclude='.git' --exclude='backups'; then
        rm -f "$tmp_tar"
        do_rollback_after_failure "بازکردن آرشیو نسخه‌ی جدید ناموفق بود"
    fi
    rm -f "$tmp_tar"
fi
NEW_VERSION="$(tr -d '[:space:]' < VERSION 2>/dev/null || echo '?')"
log "new version $NEW_VERSION"

log "pip install"
"$PY" -m pip install -r requirements.txt --quiet \
    || do_rollback_after_failure "نصب پکیج‌های جدید ناموفق بود"

log "syntax check"
"$PY" -m compileall -q -f -x '(venv|backups|logs|reseller_dbs)' . >/dev/null \
    || do_rollback_after_failure "کد نسخه‌ی جدید خطای نحوی داشت"

prune_backups
if ! restart_all; then
    do_rollback_after_failure "ری‌استارت سرویس اصلی ناموفق بود"
fi
if healthy; then
    log "OK: $FROM_VERSION -> $NEW_VERSION"
    write_result ok ""
else
    do_rollback_after_failure "سرویس بعد از آپدیت پایدار بالا نیامد"
fi
