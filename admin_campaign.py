# -*- coding: utf-8 -*-
"""ساخت پست و کمپین تبلیغاتی کانال با AI داخل پنل مدیریت بات (منوی «ابزار دیپ‌لینک و پست کانال»)."""

import asyncio
import html
import logging
import re

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

import ai_support
import campaign_ai
from i18n import tr
from states import AdminCampaign

_log = logging.getLogger("admin_campaign")
_BACK = "adm_deeplink_tools"
_CHANNEL_SETTING = "promo_channel_id"
_CHANNEL_RE = re.compile(r"^(-100\d{5,}|@[A-Za-z][A-Za-z0-9_]{3,})$")
_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")


def _kb(*rows) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=tr(text), callback_data=data) for text, data in row] for row in rows
    ])


def _cancel_kb() -> InlineKeyboardMarkup:
    return _kb([("❌ لغو", "adm_camp_cancel")])


def _variant_text(index: int, v: dict) -> str:
    param = campaign_ai.start_param_for(v["deeplink"]) or "بدون دیپ‌لینک"
    text = f"<b>━━ نسخه {index}: {html.escape(v['angle'])} ━━</b>\n\n{html.escape(v['caption'])}\n\n"
    text += f"🔘 دکمه: {html.escape(v['button_text'])}\n🔗 دیپ‌لینک: <code>{html.escape(param)}</code>"
    if v["note_for_admin"]:
        text += f"\n💡 {html.escape(v['note_for_admin'])}"
    return text


def register(router: Router, db, senior_admin_only, deny_mid):

    async def _post_markup(bot: Bot, data: dict) -> InlineKeyboardMarkup:
        me = await bot.get_me()
        param = campaign_ai.start_param_for(data["variant"]["deeplink"])
        url = f"https://t.me/{me.username}?start={param}" if param else f"https://t.me/{me.username}"
        return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=data["variant"]["button_text"], url=url)]])

    async def _send_post(bot: Bot, chat_id, data: dict):
        caption = html.escape(data["variant"]["caption"])
        markup = await _post_markup(bot, data)
        if data.get("photo_id"):
            await bot.send_photo(chat_id=chat_id, photo=data["photo_id"], caption=caption, reply_markup=markup)
        else:
            await bot.send_message(chat_id=chat_id, text=caption, reply_markup=markup)

    async def _generate_and_show(target: Message, state: FSMContext, goal: str):
        status = await target.answer("⏳ در حال تولید نسخه‌ها با AI از روی محصولات و کدهای تخفیف واقعی...")
        try:
            variants, _facts = await campaign_ai.generate_campaigns(db, goal)
        except Exception as exc:
            _log.warning("تولید کمپین ناموفق بود: %s", exc)
            await status.edit_text(
                "❌ تولید با AI انجام نشد: " + html.escape(str(exc)),
                reply_markup=_kb([("🔄 تلاش دوباره", "adm_camp_regen")], [("⬅️ بازگشت", _BACK)]),
            )
            await state.update_data(goal=goal)
            await state.set_state(AdminCampaign.choosing)
            return
        await state.update_data(goal=goal, variants=variants)
        await state.set_state(AdminCampaign.choosing)
        try:
            await status.delete()
        except Exception:
            pass
        for i, v in enumerate(variants, 1):
            await target.answer(_variant_text(i, v))
        pick_row = [(f"✅ نسخه {i}", f"adm_camp_pick:{i - 1}") for i in range(1, len(variants) + 1)]
        await target.answer(
            "کدام نسخه منتشر شود؟",
            reply_markup=_kb(pick_row, [("🔄 تولید دوباره", "adm_camp_regen"), ("✏️ تغییر هدف", "adm_camp_goal")], [("❌ لغو", "adm_camp_cancel")]),
        )

    async def _ask_goal(call_or_msg, state: FSMContext):
        await state.set_state(AdminCampaign.waiting_goal)
        text = ("🤖 هدف کمپین را بنویس (مثلاً «فروش ویژه آخر هفته» یا «معرفی کانفیگ تست»).\n"
                "AI فقط از محصولات، قیمت‌ها و کدهای تخفیف واقعی فروشگاه استفاده می‌کند.")
        markup = _kb([("▶️ بدون هدف خاص", "adm_camp_nogoal")], [("❌ لغو", "adm_camp_cancel")])
        if isinstance(call_or_msg, CallbackQuery):
            await call_or_msg.message.answer(text, reply_markup=markup)
            await call_or_msg.answer()
        else:
            await call_or_msg.answer(text, reply_markup=markup)

    @router.callback_query(F.data == "adm_camp_start")
    async def cb_start(call: CallbackQuery, state: FSMContext):
        if not senior_admin_only(call.from_user.id):
            return await deny_mid(call)
        if not ai_support.is_configured(db):
            await call.answer("دستیار هوشمند تنظیم نشده؛ ابتدا کلید API را از بخش دستیار هوشمند وارد کن.", show_alert=True)
            return
        await state.clear()
        await _ask_goal(call, state)

    @router.callback_query(F.data == "adm_camp_goal")
    async def cb_goal(call: CallbackQuery, state: FSMContext):
        if not senior_admin_only(call.from_user.id):
            return await deny_mid(call)
        await _ask_goal(call, state)

    @router.callback_query(F.data == "adm_camp_nogoal")
    async def cb_nogoal(call: CallbackQuery, state: FSMContext):
        if not senior_admin_only(call.from_user.id):
            return await deny_mid(call)
        await call.answer()
        await _generate_and_show(call.message, state, "")

    @router.message(AdminCampaign.waiting_goal, F.text)
    async def msg_goal(message: Message, state: FSMContext):
        if not senior_admin_only(message.from_user.id):
            await state.clear()
            return
        await _generate_and_show(message, state, (message.text or "").strip())

    @router.callback_query(F.data == "adm_camp_regen")
    async def cb_regen(call: CallbackQuery, state: FSMContext):
        if not senior_admin_only(call.from_user.id):
            return await deny_mid(call)
        data = await state.get_data()
        await call.answer()
        await _generate_and_show(call.message, state, data.get("goal", ""))

    @router.callback_query(F.data.startswith("adm_camp_pick:"))
    async def cb_pick(call: CallbackQuery, state: FSMContext):
        if not senior_admin_only(call.from_user.id):
            return await deny_mid(call)
        data = await state.get_data()
        variants = data.get("variants") or []
        try:
            variant = variants[int(call.data.split(":", 1)[1])]
        except (ValueError, IndexError):
            await call.answer("این نسخه دیگر معتبر نیست؛ دوباره تولید کن.", show_alert=True)
            return
        await state.update_data(variant=variant, photo_id=None)
        await state.set_state(AdminCampaign.waiting_photo)
        await call.message.answer(
            "🖼 عکس پست را بفرست، یا اگر پست بدون عکس می‌خواهی دکمه‌ی زیر را بزن.",
            reply_markup=_kb([("📝 بدون عکس", "adm_camp_nophoto")], [("❌ لغو", "adm_camp_cancel")]),
        )
        await call.answer()

    async def _after_photo(target: Message, state: FSMContext, bot: Bot):
        channel = await asyncio.to_thread(db.get_setting, _CHANNEL_SETTING, "")
        if channel:
            await state.update_data(channel_id=channel)
            await _show_preview(target, state, bot)
        else:
            await _ask_channel(target, state)

    @router.message(AdminCampaign.waiting_photo, F.photo)
    async def msg_photo(message: Message, state: FSMContext, bot: Bot):
        if not senior_admin_only(message.from_user.id):
            await state.clear()
            return
        await state.update_data(photo_id=message.photo[-1].file_id)
        await _after_photo(message, state, bot)

    @router.callback_query(F.data == "adm_camp_nophoto")
    async def cb_nophoto(call: CallbackQuery, state: FSMContext, bot: Bot):
        if not senior_admin_only(call.from_user.id):
            return await deny_mid(call)
        await state.update_data(photo_id=None)
        await call.answer()
        await _after_photo(call.message, state, bot)

    async def _ask_channel(target: Message, state: FSMContext):
        await state.set_state(AdminCampaign.waiting_channel)
        await target.answer(
            "📢 آیدی کانال را بفرست (مثل <code>-1001234567890</code> یا <code>@channel_username</code>) "
            "یا یک پست از همان کانال را فوروارد کن.\nبات باید در کانال ادمین با دسترسی ارسال پیام باشد.",
            reply_markup=_cancel_kb(),
        )

    @router.callback_query(F.data == "adm_camp_channel")
    async def cb_channel(call: CallbackQuery, state: FSMContext):
        if not senior_admin_only(call.from_user.id):
            return await deny_mid(call)
        await call.answer()
        await _ask_channel(call.message, state)

    @router.message(AdminCampaign.waiting_channel)
    async def msg_channel(message: Message, state: FSMContext, bot: Bot):
        if not senior_admin_only(message.from_user.id):
            await state.clear()
            return
        origin = getattr(message, "forward_origin", None)
        channel = None
        if origin is not None and getattr(origin, "chat", None) is not None:
            channel = str(origin.chat.id)
        else:
            raw = (message.text or "").strip().translate(_DIGITS)
            if _CHANNEL_RE.match(raw):
                channel = raw
        if not channel:
            await message.answer("آیدی نامعتبر بود. آیدی عددی (شروع با -100) یا @username بفرست یا یک پست کانال را فوروارد کن.", reply_markup=_cancel_kb())
            return
        try:
            chat = await bot.get_chat(channel)
            if chat.type != "channel":
                raise ValueError("این چت کانال نیست.")
        except Exception as exc:
            await message.answer("❌ کانال پیدا نشد یا بات به آن دسترسی ندارد: " + html.escape(str(exc)), reply_markup=_cancel_kb())
            return
        await asyncio.to_thread(db.set_setting, _CHANNEL_SETTING, str(chat.id))
        await state.update_data(channel_id=str(chat.id))
        await _show_preview(message, state, bot)

    async def _show_preview(target: Message, state: FSMContext, bot: Bot):
        data = await state.get_data()
        await state.set_state(AdminCampaign.confirming)
        await target.answer("👀 پیش‌نمایش پست (دقیقاً همین به کانال می‌رود):")
        try:
            await _send_post(bot, target.chat.id, data)
        except Exception as exc:
            await target.answer("❌ ساخت پیش‌نمایش ناموفق بود: " + html.escape(str(exc)), reply_markup=_kb([("⬅️ بازگشت", _BACK)]))
            await state.clear()
            return
        await target.answer(
            "این پست به کانال ارسال شود؟",
            reply_markup=_kb(
                [("📣 ارسال به کانال", "adm_camp_send")],
                [("📢 تغییر کانال", "adm_camp_channel"), ("🔄 نسخه‌ی دیگر", "adm_camp_regen")],
                [("❌ لغو", "adm_camp_cancel")],
            ),
        )

    @router.callback_query(F.data == "adm_camp_send")
    async def cb_send(call: CallbackQuery, state: FSMContext, bot: Bot):
        if not senior_admin_only(call.from_user.id):
            return await deny_mid(call)
        data = await state.get_data()
        if not data.get("variant") or not data.get("channel_id"):
            await call.answer("اطلاعات پست کامل نیست؛ از اول شروع کن.", show_alert=True)
            return
        await state.clear()
        try:
            await _send_post(bot, data["channel_id"], data)
        except Exception as exc:
            await call.message.answer(
                "❌ ارسال به کانال ناموفق بود: " + html.escape(str(exc)) + "\n(احتمالاً بات ادمین کانال نیست یا دسترسی ارسال پیام ندارد)",
                reply_markup=_kb([("⬅️ بازگشت", _BACK)]),
            )
            await call.answer()
            return
        param = campaign_ai.start_param_for(data["variant"]["deeplink"]) or "-"
        await asyncio.to_thread(
            db.log_admin_action, call.from_user.id, "ai_channel_post", f"پست کانال با AI ارسال شد | دیپ‌لینک: {param}",
        )
        await call.message.answer("✅ پست در کانال ارسال شد.", reply_markup=_kb([("⬅️ بازگشت", _BACK)]))
        await call.answer()

    @router.callback_query(F.data == "adm_camp_cancel")
    async def cb_cancel(call: CallbackQuery, state: FSMContext):
        if not senior_admin_only(call.from_user.id):
            return await deny_mid(call)
        await state.clear()
        await call.message.answer("لغو شد.", reply_markup=_kb([("⬅️ بازگشت", _BACK)]))
        await call.answer()
