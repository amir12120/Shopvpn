# -*- coding: utf-8 -*-
"""
منطق مشترکِ اجرای واقعیِ «تمدید سرویس» از حساب کاربری، برای استفاده در همه‌ی
مسیرهای تایید پرداخت (تایید دستی کارت‌به‌کارت در پنل ادمین، تایید خودکار
کیف‌پول، و وب‌هوک/چک‌وضعیتِ کریپتو-آبان‌گیت‌وی-درگاه‌سفارشی که از طریق
abangateway_payment.finalize_paid_order صدا زده می‌شود).

سفارش تمدید مثل سفارش «کانفیگ شخصی» از همان جدول orders با product_id=0
استفاده می‌کند (is_renewal=1)، جزئیات لازم در ستون‌های renewal_* ذخیره شده.
"""

from panel_providers import get_provider, PanelError
from user_limit import provider_kwargs
import renewal_log


class RenewalError(Exception):
    """خطای قابل‌نمایش به کاربر/ادمین در فرایند تمدید سرویس."""
    pass


async def execute_renewal(db, order) -> str:
    """تمدید واقعی را روی پنل/بوکینگ محلی اعمال می‌کند و متن نتیجه را برمی‌گرداند.
    در صورت شکست RenewalError صادر می‌شود (مبلغ را خودِ فراخوان باید مدیریت کند)."""
    kind = order["renewal_target_kind"]
    target_id = order["renewal_target_id"]
    mode = order["renewal_mode"]
    add_volume = order["renewal_add_volume_gb"] or 0
    add_days = order["renewal_add_days"] or 0

    if kind == "custom":
        cc = db.get_custom_config_owned(target_id, order["user_id"])
        if not cc:
            raise RenewalError("این سرویس دیگر یافت نشد (شاید قبلاً حذف شده).")
        server = db.get_panel_server(cc["panel_server_id"])
        if not server or not server["is_active"]:
            raise RenewalError("سرور پنل مربوط به این سرویس یافت نشد یا غیرفعال است.")
        set_volume_gb = None
        renewal_users = order["renewal_user_limit"] if "renewal_user_limit" in order.keys() else None
        if mode == "users":
            if not renewal_users:
                raise RenewalError("تعداد کاربر درخواستی نامعتبر است.")
            try:
                provider = get_provider(server)
                if not getattr(provider, "supports_user_limit", False):
                    raise RenewalError("پنل این سرویس از محدودیت کاربر پشتیبانی نمی‌کند.")
                await provider.update_user(cc["username"], **provider_kwargs(provider, renewal_users))
            except PanelError as e:
                raise RenewalError(str(e)) from e
            db.set_custom_config_user_limit(cc["id"], renewal_users)
            renewal_log.notify(db, order, cc["display_name"] or cc["username"])
            return f"✅ تعداد کاربر همزمان سرویس شما به {renewal_users} افزایش یافت."
        try:
            provider = get_provider(server)
            before = await renewal_log.service_snapshot(db, cc, provider)
            # تمدید کامل: مصرف ریست نمی‌شود؛ حجم بسته‌ی جدید مستقیماً روی سقف قبلی جمع می‌شود
            # (در نتیجه حجم باقیمانده + بسته‌ی جدید)، دقیقاً مثل زمان که روی زمان باقیمانده جمع می‌شود.
            # فرمول قبلی (سقف = باقیمانده + بسته، سپس ریست مصرف) به موفق‌شدن مرحله‌ی ریست وابسته بود؛
            # اگر ریست اعمال نمی‌شد، باقیمانده‌ی نهایی می‌شد «دو برابرِ باقیمانده‌ی قبلی» و بسته‌ی جدید گم می‌شد.
            # فقط وقتی سقف فعلی مشخص و محدود نباشد (سرویس نامحدود/وضعیت نامعلوم)، رفتار قبلی حفظ می‌شود.
            reset_usage = (mode == "full")
            preserve_remaining = (mode == "full")
            if mode == "full" and add_volume and before.get("total_bytes"):
                reset_usage = False
                preserve_remaining = False
            # پلن با حجم ۰ یعنی «نامحدود»: در تمدید کامل/حجم باید سقف حجم سرویس هم نامحدود شود
            # (قبلاً add_volume=0 فقط «بدون تغییر حجم» تلقی می‌شد و فقط زمان اضافه می‌شد).
            unlimited_volume = mode in ("full", "volume") and not add_volume
            if unlimited_volume:
                preserve_remaining = False
            await provider.update_user(
                cc["username"], add_volume_gb=add_volume, add_days=add_days, reset_usage=reset_usage,
                preserve_remaining=preserve_remaining, unlimited_volume=unlimited_volume,
                **provider_kwargs(provider, renewal_users),
            )
            if unlimited_volume:
                set_volume_gb = 0
            elif mode == "full" and add_volume:
                # سقف واقعیِ بعد از preserve_remaining را از خود پنل می‌خوانیم تا رکورد‍​‌‌​​​‌‌​‌‌​​‌​‌​‌‌​‌‌​​​‌‌​​‌​‌​‌‌​‌‌‌​​‌‌​‌‌‌‌​‌‌‌​​‌​‍
                # محلی دقیقاً هم‌سو با پنل بماند (نه با محاسبه‌ی جداگانه و احتمالاً ناهم‌خوان).‍​‌‌​​​‌‌​‌‌​​‌​‌​‌‌​‌‌​​​‌‌​​‌​‌​‌‌​‌‌‌​​‌‌​‌‌‌‌​‌‌‌​​‌​‍
                usage = await provider.get_user_usage(cc["username"])
                set_volume_gb = usage["data_limit_bytes"] / (1024 ** 3)
        except PanelError as e:
            raise RenewalError(str(e)) from e
        db.apply_custom_config_renewal(
            cc["id"], add_volume, add_days, full_reset=(mode == "full"), set_volume_gb=set_volume_gb,
        )
        if renewal_users and getattr(provider, "supports_user_limit", False):
            db.set_custom_config_user_limit(cc["id"], renewal_users)
        updated = db.get_custom_config_owned(cc["id"], order["user_id"]) or cc
        renewal_log.notify(db, order, cc["display_name"] or cc["username"], before, updated, provider)
        return "✅ سرویس شما با موفقیت تمدید شد."

    if kind == "config":
        new_expiry = db.extend_pool_config_expiry(target_id, order["user_id"], add_days)
        if not new_expiry:
            raise RenewalError("این سرویس دیگر یافت نشد (شاید قبلاً حذف شده).")
        renewal_log.notify(db, order, "کانفیگ بانک")
        return "✅ سرویس شما با موفقیت تمدید شد."

    raise RenewalError("نوع سرویس برای تمدید نامعتبر است.")
