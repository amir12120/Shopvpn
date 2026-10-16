# -*- coding: utf-8 -*-
"""منوی ادمین «تشخیص نشت کانفیگ» و دکمه‌های هشدار نشت.

دکمه‌های lk:rot / lk:warn / lk:ign روی پیام هشدار (در تاپیک «🚨 نشت کانفیگ») کار می‌کنند؛
منوی اصلی از صفحه‌ی یوزربات (adm_userbot) باز می‌شود.
"""

import asyncio
import html
import logging

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

import leak_index
import leak_scanner as ls
import userbot
from i18n import tr

logger = logging.getLogger(__name__)

SCAN_MINUTES_CHOICES = [5, 15, 30, 60]
MAX_PER_MIN_CHOICES = [3, 6, 10, 20]
WARN_THRESHOLD_CHOICES = [1, 2, 3, 5]
STATUS_LABELS = {"new": "🆕 جدید", "rotated": "🔄 چرخانده شد", "ignored": "🙈 نادیده", "warned": "⚠️ اخطار"}


_running_refreshes = set()


class LeakAdmin(StatesGroup):
    waiting_channel = State()
    waiting_keywords = State()


def _kb(rows):
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _onoff(value: bool) -> str:
    return "🟢" if value else "🔴"


def _cycle(choices, current):
    for item in choices:
        if item > current:
            return item
    return choices[0]


def create_leak_router(db) -> Router:
    router = Router()

    async def _deny(call: CallbackQuery):
        await call.answer(tr("⛔️ این بخش فقط برای مدیران کامل در دسترس است."), show_alert=True)

    async def _show(call: CallbackQuery, text: str, markup):
        if call.message is None:
            return
        try:
            await call.message.edit_text(text, reply_markup=markup)
            return
        except TelegramBadRequest as exc:
            if "message is not modified" in str(exc).lower():
                return
        except Exception:
            pass
        try:
            await call.message.delete()
        except Exception:
            pass
        try:
            await call.message.answer(text, reply_markup=markup)
        except Exception:
            pass

    async def _log(admin_id: int, action: str, detail: str):
        await asyncio.to_thread(db.log_admin_action, admin_id, action, detail)

    def _flag(key: str) -> bool:
        return ls.flag(db, key)

    def _int(key: str, default: int) -> int:
        return ls.int_setting(db, key, default)

    # ------------------------------------------------------------ main screen
    async def _main_text() -> str:
        stats = await asyncio.to_thread(db.get_credential_index_stats)
        by_status = await asyncio.to_thread(db.count_leak_events_by_status)
        channels = await asyncio.to_thread(db.list_leak_channels)
        active_channels = sum(1 for c in channels if c["active"])
        if ls.get_client():
            me = userbot.STATE.get("me") or {}
            client_state = tr("🟢 متصل") + (f" — @{html.escape(me['username'])}" if me.get("username") else "")
        else:
            client_state = tr("🔴 قطع (یوزربات متصل نیست)")
        events_line = " | ".join(
            f"{tr(label)}: {by_status.get(key, 0)}" for key, label in STATUS_LABELS.items()
        )
        return (
            f"{tr('🚨 تشخیص نشت کانفیگ')}\n\n"
            f"{tr('یوزربات')}: {client_state}\n"
            f"{tr('کانال‌های زیر نظر')}: {active_channels}/{len(channels)}\n"
            f"{tr('ایندکس')}: {stats['configs']} {tr('سرویس')} / {stats['hashes']} {tr('هش')}"
            + (f" — {tr('آخرین به‌روزرسانی')}: {html.escape(str(stats['last_update']))}" if stats["last_update"] else "")
            + "\n"
            f"{tr('رویدادها')}: {events_line}\n\n"
            f"{tr('اسکنر از اکانت یوزربات استفاده می‌کند. سقف درخواست دارد، هنگام FloodWait متوقف می‌شود و پاسخ به مشتری در اولویت است.')}"
        )

    async def _show_main(call: CallbackQuery):
        text = await _main_text()
        keywords = ls.keywords(db)
        rows = [
            [InlineKeyboardButton(text=f"{_onoff(_flag(ls.KEY_ENABLED))} {tr('اسکنر نشت')}", callback_data="adm_leak_t:" + ls.KEY_ENABLED)],
            [InlineKeyboardButton(text=f"{_onoff(_flag(ls.KEY_AUTO_REVOKE))} {tr('ابطال خودکار لینک (پیش‌فرض خاموش)')}", callback_data="adm_leak_t:" + ls.KEY_AUTO_REVOKE)],
            [InlineKeyboardButton(text=f"⏱ {tr('فاصله‌ی اسکن')}: {_int(ls.KEY_SCAN_MINUTES, 15)} {tr('دقیقه')}", callback_data="adm_leak_cycle:" + ls.KEY_SCAN_MINUTES)],
            [InlineKeyboardButton(text=f"🚦 {tr('سقف درخواست در دقیقه')}: {_int(ls.KEY_MAX_PER_MIN, 6)}", callback_data="adm_leak_cycle:" + ls.KEY_MAX_PER_MIN)],
            [InlineKeyboardButton(text=f"⚠️ {tr('سقف اخطار تا مسدودسازی')}: {_int(ls.KEY_WARN_THRESHOLD, 3)}", callback_data="adm_leak_cycle:" + ls.KEY_WARN_THRESHOLD)],
            [InlineKeyboardButton(text=f"🔑 {tr('کلیدواژه‌های جستجوی سراسری')} ({len(keywords)})", callback_data="adm_leak_kw")],
            [InlineKeyboardButton(text=tr("📢 کانال‌های زیر نظر"), callback_data="adm_leak_ch")],
            [InlineKeyboardButton(text=tr("🧾 آخرین رویدادها"), callback_data="adm_leak_ev")],
            [InlineKeyboardButton(text=tr("🔄 به‌روزرسانی فوری ایندکس"), callback_data="adm_leak_idx")],
            [InlineKeyboardButton(text=tr("⬅️ بازگشت"), callback_data="adm_cat:access")],
        ]
        await _show(call, text, _kb(rows))

    @router.callback_query(F.data == "adm_leak")
    async def cb_main(call: CallbackQuery, state: FSMContext):
        if not db.is_full_admin(call.from_user.id):
            return await _deny(call)
        await state.clear()
        await _show_main(call)
        await call.answer()

    @router.callback_query(F.data.startswith("adm_leak_t:"))
    async def cb_toggle(call: CallbackQuery):
        if not db.is_full_admin(call.from_user.id):
            return await _deny(call)
        key = call.data.split(":", 1)[1]
        if key not in (ls.KEY_ENABLED, ls.KEY_AUTO_REVOKE):
            return await call.answer()
        new_value = "0" if _flag(key) else "1"
        await asyncio.to_thread(db.set_setting, key, new_value)
        await _log(call.from_user.id, "leak_toggle", f"{key}={new_value}")
        await _show_main(call)
        await call.answer()

    @router.callback_query(F.data.startswith("adm_leak_cycle:"))
    async def cb_cycle(call: CallbackQuery):
        if not db.is_full_admin(call.from_user.id):
            return await _deny(call)
        key = call.data.split(":", 1)[1]
        choices = {
            ls.KEY_SCAN_MINUTES: SCAN_MINUTES_CHOICES,
            ls.KEY_MAX_PER_MIN: MAX_PER_MIN_CHOICES,
            ls.KEY_WARN_THRESHOLD: WARN_THRESHOLD_CHOICES,
        }.get(key)
        if choices is None:
            return await call.answer()
        new_value = _cycle(choices, _int(key, choices[0]))
        await asyncio.to_thread(db.set_setting, key, str(new_value))
        await _log(call.from_user.id, "leak_setting", f"{key}={new_value}")
        await _show_main(call)
        await call.answer()

    @router.callback_query(F.data == "adm_leak_idx")
    async def cb_index(call: CallbackQuery):
        if not db.is_full_admin(call.from_user.id):
            return await _deny(call)
        task = asyncio.create_task(leak_index.refresh_all(db))
        _running_refreshes.add(task)
        task.add_done_callback(_running_refreshes.discard)
        await _log(call.from_user.id, "leak_index_refresh", "manual")
        await call.answer(tr("به‌روزرسانی ایندکس شروع شد."), show_alert=True)

    # ------------------------------------------------------------ keywords
    @router.callback_query(F.data == "adm_leak_kw")
    async def cb_keywords(call: CallbackQuery, state: FSMContext):
        if not db.is_full_admin(call.from_user.id):
            return await _deny(call)
        await state.set_state(LeakAdmin.waiting_keywords)
        current = ", ".join(ls.keywords(db)) or tr("(خالی)")
        await _show(call, tr("کلیدواژه‌ها را با کاما جدا کنید (مثلاً: vless, vmess, trojan).") + f"\n{tr('فعلی')}: {html.escape(current)}\n\n" + tr("برای خالی‌کردن، «-» بفرستید."),
                    _kb([[InlineKeyboardButton(text=tr("⬅️ انصراف"), callback_data="adm_leak")]]))
        await call.answer()

    @router.message(StateFilter(LeakAdmin.waiting_keywords))
    async def msg_keywords(message: Message, state: FSMContext):
        if not db.is_full_admin(message.from_user.id):
            await state.clear()
            return
        raw = (message.text or "").strip()
        value = "" if raw in ("-", "") else ",".join(k.strip() for k in raw.split(",") if k.strip())[:500]
        await asyncio.to_thread(db.set_setting, ls.KEY_KEYWORDS, value)
        await _log(message.from_user.id, "leak_keywords", value)
        await state.clear()
        await message.answer(tr("✅ کلیدواژه‌ها ذخیره شد.") + "\n" + (html.escape(value) or tr("(خالی)")))

    # ------------------------------------------------------------ channels
    async def _show_channels(call: CallbackQuery):
        channels = await asyncio.to_thread(db.list_leak_channels)
        lines = [tr("📢 کانال‌های زیر نظر اسکنر"), ""]
        rows = []
        if not channels:
            lines.append(tr("هنوز کانالی اضافه نشده است."))
        for ch in channels:
            name = ch["title"] or str(ch["channel_id"])
            lines.append(f"{_onoff(ch['active'])} {html.escape(name)}")
            rows.append([
                InlineKeyboardButton(text=f"{_onoff(ch['active'])} {name[:30]}", callback_data=f"adm_leak_chT:{ch['channel_id']}"),
                InlineKeyboardButton(text="🗑", callback_data=f"adm_leak_chD:{ch['channel_id']}"),
            ])
        rows.append([InlineKeyboardButton(text=tr("➕ افزودن کانال"), callback_data="adm_leak_chA")])
        rows.append([InlineKeyboardButton(text=tr("⬅️ بازگشت"), callback_data="adm_leak")])
        await _show(call, "\n".join(lines), _kb(rows))

    @router.callback_query(F.data == "adm_leak_ch")
    async def cb_channels(call: CallbackQuery, state: FSMContext):
        if not db.is_full_admin(call.from_user.id):
            return await _deny(call)
        await state.clear()
        await _show_channels(call)
        await call.answer()

    @router.callback_query(F.data == "adm_leak_chA")
    async def cb_channel_add(call: CallbackQuery, state: FSMContext):
        if not db.is_full_admin(call.from_user.id):
            return await _deny(call)
        await state.set_state(LeakAdmin.waiting_channel)
        await _show(call, tr("@username یا لینک t.me یا شناسه‌ی عددی کانال را بفرستید.\nاکانت یوزربات باید عضو کانال باشد (یا کانال عمومی باشد)."),
                    _kb([[InlineKeyboardButton(text=tr("⬅️ انصراف"), callback_data="adm_leak_ch")]]))
        await call.answer()

    @router.message(StateFilter(LeakAdmin.waiting_channel))
    async def msg_channel(message: Message, state: FSMContext):
        if not db.is_full_admin(message.from_user.id):
            await state.clear()
            return
        client = ls.get_client()
        if client is None:
            await message.answer(tr("⛔️ یوزربات متصل نیست؛ ابتدا از منوی سرور وارد اکانت تلگرام شوید."))
            return
        try:
            title = await ls.add_channel(client, db, message.text or "")
        except ValueError as exc:
            await message.answer(tr("⛔️") + f" {exc}")
            return
        except Exception as exc:
            logger.warning("leak: add channel failed", exc_info=True)
            await message.answer(tr("⛔️ کانال پیدا نشد یا یوزربات دسترسی ندارد.") + f"\n{html.escape(str(exc)[:200])}")
            return
        await _log(message.from_user.id, "leak_channel_add", title)
        await state.clear()
        await message.answer(tr("✅ کانال اضافه شد:") + f" {html.escape(title)}")

    @router.callback_query(F.data.startswith("adm_leak_chT:"))
    async def cb_channel_toggle(call: CallbackQuery):
        if not db.is_full_admin(call.from_user.id):
            return await _deny(call)
        channel_id = int(call.data.split(":", 1)[1])
        ch = await asyncio.to_thread(db.get_leak_channel, channel_id)
        if ch:
            await asyncio.to_thread(db.set_leak_channel_active, channel_id, not ch["active"])
        await _show_channels(call)
        await call.answer()

    @router.callback_query(F.data.startswith("adm_leak_chD:"))
    async def cb_channel_delete(call: CallbackQuery):
        if not db.is_full_admin(call.from_user.id):
            return await _deny(call)
        channel_id = int(call.data.split(":", 1)[1])
        await asyncio.to_thread(db.remove_leak_channel, channel_id)
        await _log(call.from_user.id, "leak_channel_remove", str(channel_id))
        await _show_channels(call)
        await call.answer(tr("حذف شد."))

    # ------------------------------------------------------------ events
    @router.callback_query(F.data == "adm_leak_ev")
    async def cb_events(call: CallbackQuery):
        if not db.is_full_admin(call.from_user.id):
            return await _deny(call)
        events = await asyncio.to_thread(db.list_leak_events, 10)
        lines = [tr("🧾 آخرین رویدادهای نشت"), ""]
        if not events:
            lines.append(tr("تاکنون نشتی ثبت نشده است."))
        for ev in events:
            lines.append(
                f"#{ev['id']} | {STATUS_LABELS.get(ev['status'], ev['status'])} | "
                f"{tr('کاربر')} <code>{ev['user_id']}</code> | {html.escape(ev['channel_title'] or '-')}\n"
                f"{html.escape(ev['post_link'])}"
            )
        await _show(call, "\n".join(lines), _kb([[InlineKeyboardButton(text=tr("⬅️ بازگشت"), callback_data="adm_leak")]]))
        await call.answer()

    # ------------------------------------------------------------ alert buttons (lk:*)
    async def _finish_alert(call: CallbackQuery, status_line: str, keep_buttons: bool = False):
        """پیام هشدار را با نتیجه‌ی اقدام به‌روز می‌کند. مگر keep_buttons، دکمه‌ها برداشته می‌شوند."""
        if call.message is None:
            return
        try:
            base = call.message.html_text or ""
            markup = call.message.reply_markup if keep_buttons else None
            await call.message.edit_text(f"{base}\n\n{status_line}", parse_mode="HTML", reply_markup=markup)
        except Exception:
            logger.debug("could not update leak alert message", exc_info=True)

    async def _event_id(call: CallbackQuery):
        try:
            return int(call.data.split(":", 2)[2])
        except (IndexError, ValueError):
            return None

    @router.callback_query(F.data.startswith("lk:rot:"))
    async def cb_rotate(call: CallbackQuery):
        if not db.is_full_admin(call.from_user.id):
            return await _deny(call)
        event_id = await _event_id(call)
        if event_id is None:
            return await call.answer()
        await call.answer(tr("در حال چرخاندن لینک..."))
        ok, msg = await ls.rotate_event(db, call.bot, event_id, actor=f"ادمین {call.from_user.id}")
        await _log(call.from_user.id, "leak_rotate", f"event={event_id} ok={ok}")
        mark = "✅" if ok else "⛔️"
        await _finish_alert(call, f"{mark} {html.escape(msg)}")

    @router.callback_query(F.data.startswith("lk:warn:"))
    async def cb_warn(call: CallbackQuery):
        if not db.is_full_admin(call.from_user.id):
            return await _deny(call)
        event_id = await _event_id(call)
        if event_id is None:
            return await call.answer()
        ok, msg = await ls.warn_event(db, call.bot, event_id)
        await _log(call.from_user.id, "leak_warn", f"event={event_id} ok={ok}")
        await call.answer(tr(msg) if ok else msg, show_alert=not ok)
        if ok:
            await _finish_alert(call, f"⚠️ {html.escape(msg)}", keep_buttons=True)

    @router.callback_query(F.data.startswith("lk:ign:"))
    async def cb_ignore(call: CallbackQuery):
        if not db.is_full_admin(call.from_user.id):
            return await _deny(call)
        event_id = await _event_id(call)
        if event_id is None:
            return await call.answer()
        await asyncio.to_thread(db.set_leak_event_status, event_id, "ignored")
        await _log(call.from_user.id, "leak_ignore", f"event={event_id}")
        await call.answer(tr("نادیده گرفته شد."))
        await _finish_alert(call, tr("🙈 نادیده گرفته شد."))

    return router
