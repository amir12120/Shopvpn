# -*- coding: utf-8 -*-
"""مسیریابی گزارش‌ها به گروه فوروم تاپیک‌دار؛ بدون گروه یا هنگام خطا، ارسال مستقیم به مدیران."""
from i18n import tr

import asyncio
import html
import logging

import aiohttp
from aiogram import BaseMiddleware
from aiogram.exceptions import TelegramAPIError, TelegramBadRequest, TelegramRetryAfter
from aiogram.types import CallbackQuery, Message

logger = logging.getLogger(__name__)

SETTING_CHAT_ID = "report_chat_id"
DEFAULT_TOPIC = "other"
TOPICS = {
    "purchase": "🛒 خرید",
    "service": "🛠 سرویس",
    "renewal": "🔄 تمدید",
    "test": "🧪 تست",
    "finance": "💰 مالی",
    "error": "🚨 خطا",
    "backup": "🗄 بکاپ",
    "nightly": "📊 گزارش شبانه",
    "signup": "🆕 ثبت‌نام",
    "referral": "🤝 رفرال",
    "prize": "🎁 جوایز",
    "security": "🛡 امنیت",
    "other": "📌 سایر",
}
MISSING_THREAD_MARKERS = ("thread not found", "topic_id_invalid", "topic_deleted")
RETRY_AFTER_CAP = 30

_topic_lock = asyncio.Lock()


class SetupError(Exception):
    """خطای راه‌اندازی گروه گزارش با پیام قابل نمایش به مدیر."""


async def _db(fn, *args, **kwargs):
    return await asyncio.to_thread(fn, *args, **kwargs)


def get_chat_id(db):
    raw = (db.get_setting(SETTING_CHAT_ID, "") or "").strip()
    try:
        return int(raw) if raw else None
    except ValueError:
        return None


def topic_display_name(db, chat_id: int, topic_key: str) -> str:
    """نام قابل‌نمایش تاپیک: نام سفارشی که مدیر تنظیم کرده (فاز ۱)، وگرنه
    نام پیش‌فرض ثابت پروژه."""
    labels = db.get_report_topic_labels(chat_id)
    return labels.get(topic_key) or TOPICS.get(topic_key, topic_key)


async def _create_topic(bot, db, chat_id: int, topic_key: str) -> int:
    name = await _db(topic_display_name, db, chat_id, topic_key)
    created = await bot.create_forum_topic(chat_id, name)
    await _db(db.set_report_topic, chat_id, topic_key, created.message_thread_id)
    return created.message_thread_id


async def rename_topic(bot, db, chat_id: int, topic_key: str, new_name: str) -> None:
    """نام تاپیک را هم در دیتابیس (برای ساخت‌های بعدی) و هم - در صورت وجود -
    روی خودِ تاپیک واقعی تلگرام (با edit_forum_topic) تغییر می‌دهد."""
    new_name = (new_name or "").strip()
    if not new_name:
        raise SetupError("نام تاپیک نمی‌تواند خالی باشد.")
    await _db(db.set_report_topic_label, chat_id, topic_key, new_name)
    thread_id = (await _db(db.get_report_topics, chat_id)).get(topic_key)
    if thread_id:
        try:
            await bot.edit_forum_topic(chat_id, thread_id, name=new_name)
        except TelegramAPIError as e:
            raise SetupError(f"نام در دیتابیس ذخیره شد ولی تغییر نام خودِ تاپیک در تلگرام ناموفق بود: {e}")


async def _thread_for(bot, db, chat_id: int, topic_key: str, refresh: bool = False) -> int:
    if not refresh:
        thread_id = (await _db(db.get_report_topics, chat_id)).get(topic_key)
        if thread_id:
            return thread_id
    async with _topic_lock:
        if not refresh:
            thread_id = (await _db(db.get_report_topics, chat_id)).get(topic_key)
            if thread_id:
                return thread_id
        return await _create_topic(bot, db, chat_id, topic_key)


async def _attempt(factory, chat_id: int, thread_id: int):
    try:
        return await factory(chat_id, thread_id)
    except TelegramRetryAfter as e:
        await asyncio.sleep(min(e.retry_after, RETRY_AFTER_CAP) + 1)
        return await factory(chat_id, thread_id)


async def send_to_group(bot, db, topic_key: str, factory):
    """factory(chat_id, thread_id) پیام را می‌فرستد؛ اگر گروه تنظیم نباشد یا خطا بدهد None برمی‌گرداند."""
    chat_id = get_chat_id(db)
    if chat_id is None:
        return None
    if topic_key not in TOPICS:
        topic_key = DEFAULT_TOPIC
    try:
        thread_id = await _thread_for(bot, db, chat_id, topic_key)
        try:
            return await _attempt(factory, chat_id, thread_id)
        except TelegramBadRequest as e:
            if not any(marker in str(e).lower() for marker in MISSING_THREAD_MARKERS):
                raise
            thread_id = await _thread_for(bot, db, chat_id, topic_key, refresh=True)
            return await _attempt(factory, chat_id, thread_id)
    except Exception as e:
        logger.warning("ارسال گزارش «%s» به گروه %s ناموفق بود (%s)؛ ارسال مستقیم به مدیران.", topic_key, chat_id, e)
        return None


async def send_text(bot, db, topic_key: str, text: str, reply_markup=None):
    return await send_to_group(
        bot, db, topic_key,
        lambda chat_id, thread_id: bot.send_message(
            chat_id, text, message_thread_id=thread_id, reply_markup=reply_markup,
        ),
    )


async def send_media(bot, db, topic_key: str, file_id: str, media_type: str, caption: str, reply_markup=None):
    """ارسال رسید/مدیای گزارش با رعایت سقف ۱۰۲۴ کاراکتری کپشن تلگرام.

    در صورت طولانی بودن کپشن، رسید با کپشن کوتاه و دکمه‌های همان گزارش ارسال
    می‌شود و متن کامل بلافاصله در پیام بعدی همان تاپیک قرار می‌گیرد. این کار
    باعث نمی‌شود خطای ``message caption is too long`` کل مسیر گزارش را متوقف کند.
    """
    max_caption = 1000

    async def _send_full_text(chat_id: int, thread_id: int):
        text = caption or ""
        for start in range(0, len(text), 4000):
            await bot.send_message(
                chat_id, text[start:start + 4000], message_thread_id=thread_id
            )

    def _factory(chat_id, thread_id):
        if len(caption or "") <= max_caption:
            if media_type == "document":
                return bot.send_document(chat_id, file_id, caption=caption, message_thread_id=thread_id, reply_markup=reply_markup)
            return bot.send_photo(chat_id, file_id, caption=caption, message_thread_id=thread_id, reply_markup=reply_markup)

        short_caption = (caption[:max_caption - 30].rstrip() +
                         "\n\n⚠️ ادامه جزئیات در پیام بعدی…")
        if media_type == "document":
            return bot.send_document(chat_id, file_id, caption=short_caption, message_thread_id=thread_id, reply_markup=reply_markup)
        return bot.send_photo(chat_id, file_id, caption=short_caption, message_thread_id=thread_id, reply_markup=reply_markup)

    sent = await send_to_group(bot, db, topic_key, _factory)
    if sent and len(caption or "") > max_caption:
        try:
            await _send_full_text(sent.chat.id, sent.message_thread_id or 0)
        except Exception:
            logger.exception("ارسال جزئیات کامل گزارش مدیا ناموفق بود؛ خود رسید ارسال شده است.")
    return sent


async def report(bot, db, topic_key: str, text: str, reply_markup=None, senior_only: bool = False) -> bool:
    """ارسال به تاپیک گروه گزارش و در غیاب آن پیام خصوصی به مدیران."""
    if await send_text(bot, db, topic_key, text, reply_markup):
        return True
    try:
        admin_ids = await _db(db.list_admins)
    except Exception:
        logger.exception("خواندن لیست ادمین‌ها برای ارسال گزارش ناموفق بود.")
        return False
    delivered = False
    for admin_id in admin_ids:
        if senior_only and not db.is_senior_admin(admin_id):
            continue
        try:
            await bot.send_message(admin_id, text, reply_markup=reply_markup)
            delivered = True
        except Exception:
            logger.warning("ارسال گزارش به ادمین %s ناموفق بود.", admin_id)
    return delivered


def build_block_toggle_text(user_row, tg_id: int, blocked: bool, actor_label: str) -> str:
    """متن کارت تاپیک «امنیت» برای بلاک/آنبلاک کاربر - مشترک بین بات، پنل وب
    و مینی‌اپ (سه مسیر مستقل تغییر وضعیت بلاک)."""
    name = html.escape((user_row["first_name"] if user_row else "") or "")
    username = (user_row["username"] if user_row else "") or ""
    handle = f" (@{html.escape(username)})" if username else ""
    icon = "🚫" if blocked else "✅"
    action = "بلاک شد" if blocked else "آنبلاک شد"
    return (
        f"{icon} کاربر {action}\n\n"
        f"👤 {name}{handle}\n"
        f"🆔 <code>{tg_id}</code>\n"
        f"👮 توسط: {html.escape(actor_label)}"
    )


async def notify_test_config(bot, db, user_id: int, name: str, username, detail_html: str) -> None:
    """اعلان تحویل کانفیگ تست به تاپیک «تست»؛ بدون گروه گزارش چیزی ارسال نمی‌شود."""
    handle = f" (@{html.escape(username)})" if username else ""
    text = (
        "🧪 کانفیگ تست تحویل داده شد\n\n"
        f"👤 <a href=\"tg://user?id={user_id}\">{html.escape(name or '')}</a>{handle}\n"
        f"🆔 <code>{user_id}</code>\n"
        f"{detail_html}"
    )
    try:
        await send_text(bot, db, "test", text)
    except Exception:
        logger.warning("ارسال اعلان کانفیگ تست ناموفق بود.", exc_info=True)


def build_prize_text(source_label: str, user_id: int, name: str, username, detail: str, html_mode: bool = True) -> str:
    """متن کارت تاپیک «جوایز» برای هر جایزه‌ای که به کاربر داده می‌شود (گردونه، قرعه‌کشی، هدیه‌ی عضویت)."""
    handle = f" (@{username})" if username else ""
    if html_mode:
        who = f'<a href="tg://user?id={user_id}">{html.escape(name or str(user_id))}</a>{html.escape(handle)}'
        return f"🎁 {html.escape(source_label)}\n\n👤 {who}\n🆔 <code>{user_id}</code>\n{detail}"
    return f"🎁 {source_label}\n\n👤 {name or user_id}{handle}\n🆔 {user_id}\n{detail}"


async def notify_prize(bot, db, source_label: str, user_id: int, name: str, username, detail_html: str) -> None:
    """گزارش جایزه به تاپیک «جوایز»؛ بدون گروه گزارش چیزی ارسال نمی‌شود."""
    try:
        await send_text(bot, db, "prize", build_prize_text(source_label, user_id, name, username, detail_html))
    except Exception:
        logger.warning("ارسال گزارش جایزه ناموفق بود.", exc_info=True)


async def notify_prize_raw(bot_token: str, db, source_label: str, user_id: int, name: str, username, detail_text: str) -> None:
    """مثل notify_prize برای مسیرهایی که فقط توکن بات دارند (متن ساده، بدون HTML)."""
    try:
        await send_raw_to_group(bot_token, db, "prize", build_prize_text(source_label, user_id, name, username, detail_text, html_mode=False))
    except Exception:
        logger.warning("ارسال گزارش جایزه (raw) ناموفق بود.", exc_info=True)


async def setup_group(bot, db, chat_id: int) -> int:
    """گروه را اعتبارسنجی می‌کند، تاپیک‌های ناموجود را می‌سازد و ذخیره می‌کند؛ تعداد تاپیک‌های جدید را برمی‌گرداند."""
    try:
        chat = await bot.get_chat(chat_id)
    except TelegramAPIError:
        raise SetupError("چت پیدا نشد. بات را به گروه اضافه کن و آیدی عددی درست را بفرست.")
    if chat.type != "supergroup":
        raise SetupError("این چت سوپرگروه نیست. یک سوپرگروه بساز یا گروه را به سوپرگروه تبدیل کن.")
    if not getattr(chat, "is_forum", False):
        raise SetupError("حالت «تاپیک‌ها» (Topics) در تنظیمات گروه روشن نیست.")

    existing = await _db(db.get_report_topics, chat_id)
    created = 0
    for topic_key in TOPICS:
        if topic_key in existing:
            continue
        try:
            async with _topic_lock:
                await _create_topic(bot, db, chat_id, topic_key)
        except TelegramBadRequest as e:
            if "rights" in str(e).lower():
                raise SetupError("بات دسترسی ساخت تاپیک ندارد. بات را ادمین گروه کن و گزینه‌ی Manage Topics را روشن کن.")
            raise SetupError(f"ساخت تاپیک ناموفق بود: {e}")
        except TelegramAPIError as e:
            raise SetupError(f"ساخت تاپیک ناموفق بود: {e}")
        created += 1

    previous = db.get_setting(SETTING_CHAT_ID, "") or ""
    await _db(db.set_setting, SETTING_CHAT_ID, str(chat_id))
    sent = await send_text(bot, db, DEFAULT_TOPIC, "✅ گروه گزارش فعال شد. از این پس گزارش‌ها در تاپیک مربوط به خودشان ارسال می‌شوند.")
    if sent is None:
        await _db(db.set_setting, SETTING_CHAT_ID, previous)
        raise SetupError("ارسال پیام در گروه ناموفق بود. مطمئن شو بات ادمین گروه است و اجازه‌ی ارسال پیام دارد.")
    return created


async def clear_group(db) -> None:
    await _db(db.set_setting, SETTING_CHAT_ID, "")
    await _db(db.clear_report_topics)


async def _raw_create_topic(bot_token: str, chat_id: int, topic_key: str):
    url = f"https://api.telegram.org/bot{bot_token}/createForumTopic"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url, json={"chat_id": chat_id, "name": TOPICS[topic_key]},
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                data = await resp.json()
                if resp.status == 200 and data.get("ok"):
                    return data["result"]["message_thread_id"]
    except Exception:
        logger.warning("ساخت تاپیک «%s» با HTTP خام ناموفق بود.", topic_key, exc_info=True)
    return None


async def _raw_send_message(bot_token: str, chat_id: int, text: str, thread_id: int = None) -> bool:
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    if thread_id:
        payload["message_thread_id"] = thread_id
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                return resp.status == 200
    except Exception:
        logger.warning("ارسال پیام HTTP خام به تلگرام ناموفق بود.", exc_info=True)
        return False


async def send_raw_to_group(bot_token: str, db, topic_key: str, text: str) -> bool:
    """فقط تلاش برای ارسال به تاپیک گروه گزارش با HTTP خام؛ اگر گروه تنظیم
    نباشد یا ارسال ناموفق باشد False برمی‌گرداند (بدون فالبک به پیام خصوصی -
    آن تصمیم به عهده‌ی فراخوان است)."""
    if not bot_token:
        return False
    chat_id = get_chat_id(db)
    if chat_id is None:
        return False
    key = topic_key if topic_key in TOPICS else DEFAULT_TOPIC
    topics = await _db(db.get_report_topics, chat_id)
    thread_id = topics.get(key)
    if not thread_id:
        thread_id = await _raw_create_topic(bot_token, chat_id, key)
        if thread_id:
            await _db(db.set_report_topic, chat_id, key, thread_id)
    if not thread_id:
        return False
    return await _raw_send_message(bot_token, chat_id, text, thread_id)


async def report_raw(bot_token: str, db, topic_key: str, text: str, senior_only: bool = True) -> bool:
    """مثل ``report()`` بالا، ولی برای پردازه‌هایی (مثل پنل وب مستقل) که شیء
    Bot از aiogram در اختیار ندارند و فقط توکن بات را دارند - با HTTP خام به
    Telegram Bot API وصل می‌شود. اول تلاش می‌کند در تاپیک مربوطه‌ی گروه گزارش
    پست کند؛ اگر گروه تنظیم نبود یا ارسال ناموفق بود، به پیام خصوصی ادمین‌های
    ارشد برمی‌گردد."""
    if await send_raw_to_group(bot_token, db, topic_key, text):
        return True
    try:
        admin_ids = await _db(db.list_admins)
    except Exception:
        logger.exception("خواندن لیست ادمین‌ها برای ارسال گزارش خام ناموفق بود.")
        return False
    delivered = False
    for admin_id in admin_ids:
        if senior_only and not db.is_senior_admin(admin_id):
            continue
        if await _raw_send_message(bot_token, admin_id, text):
            delivered = True
    return delivered


class ReportGroupGuardMiddleware(BaseMiddleware):
    """پیام‌های داخل گروه گزارش را نادیده می‌گیرد و دکمه‌های آن را فقط برای مدیران فعال نگه می‌دارد."""

    def __init__(self, db):
        super().__init__()
        self.db = db

    async def __call__(self, handler, event, data: dict):
        chat_id = get_chat_id(self.db)
        if chat_id is None:
            return await handler(event, data)
        if isinstance(event, Message):
            if event.chat.id == chat_id:
                return None
        elif isinstance(event, CallbackQuery):
            message = event.message
            user = event.from_user
            if message is not None and message.chat.id == chat_id and (user is None or not self.db.is_admin(user.id)):
                try:
                    await event.answer(tr("⛔️ این دکمه‌ها فقط برای مدیران فعال است."), show_alert=True)
                except Exception:
                    logger.warning("پاسخ به دکمه‌ی غیرمجاز در گروه گزارش ناموفق بود.", exc_info=True)
                return None
        return await handler(event, data)
