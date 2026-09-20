"""
بوت تلغرام لإرسال الأذكار تلقائيًا للمشتركين حسب جدول زمني محدد في config.json
"""

import json
import logging
import os
from datetime import time as dtime

import psycopg2
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")

BOT_TOKEN = os.environ.get("BOT_TOKEN")
DATABASE_URL = os.environ.get("DATABASE_URL")
ADMIN_CHAT_ID = 6644045109


def get_connection():
    return psycopg2.connect(DATABASE_URL, sslmode="require")


def init_db():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """CREATE TABLE IF NOT EXISTS subscribers (
                chat_id BIGINT PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
           )"""
    )
    conn.commit()
    cur.close()
    conn.close()


def add_subscriber(chat_id: int, username: str = None, first_name: str = None):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO subscribers (chat_id, username, first_name)
           VALUES (%s, %s, %s)
           ON CONFLICT (chat_id) DO UPDATE SET
               username = EXCLUDED.username,
               first_name = EXCLUDED.first_name""",
        (chat_id, username, first_name),
    )
    conn.commit()
    cur.close()
    conn.close()


def remove_subscriber(chat_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM subscribers WHERE chat_id = %s", (chat_id,))
    conn.commit()
    cur.close()
    conn.close()


def get_all_subscribers():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT chat_id FROM subscribers")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [r[0] for r in rows]


def subscriber_count():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM subscribers")
    count = cur.fetchone()[0]
    cur.close()
    conn.close()
    return count


def get_subscribers_details():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT chat_id, username, first_name FROM subscribers ORDER BY joined_at"
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def build_welcome_text() -> str:
    return (
        "مرحبًا بك عزيزي المستخدم!\n"
        "شكرًا لك على استخدام بوت الأذكار.\n"
        "يقوم البوت بإرسال؛ أدعية، أذكار، أحاديث، مقتطفات ومواعظ دينية.\n\n"
        "- في حال كان لديك استفسار، رأي، اقتراح تواصل معنا: (@Yassseeeer)، "
        "من أجل ضمان الحصول على الرد في أسرع وقت ممكن.\n\n"
        "نحن نسعد باستقبال آرائكم ومقترحاتكم، ونقدر الأشخاص الجيدين مثلك، "
        "الذين يسعون من أجل تطوير وتحسين جودة البوت.\n\n"
        "- في حال وجدت شيئًا مخالفًا، الرجاء إعلامنا به على الفور 📬.\n\n"
        "- صدقة جارية لي ولكل مسلم 🌸🌿،\n"
        "- لا تنسونا من صالح دعائكم فضلاً.\n\n"
        "- رابط البوت:\n"
        "https://t.me/Yasser25525yasserbot"
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    add_subscriber(user.id, username=user.username, first_name=user.first_name)
    await update.message.reply_text(build_welcome_text(), parse_mode=ParseMode.HTML)


async def any_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    add_subscriber(user.id, username=user.username, first_name=user.first_name)
    await update.message.reply_text(build_welcome_text(), parse_mode=ParseMode.HTML)


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    remove_subscriber(chat_id)
    await update.message.reply_text("❌ تم إلغاء اشتراكك. نسأل الله أن يحفظك.")


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    config = load_config()
    admin_id = config.get("admin_chat_id") or ADMIN_CHAT_ID
    if admin_id and update.effective_chat.id != admin_id:
        return
    await update.message.reply_text(f"👥 عدد المشتركين: {subscriber_count()}")


async def users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    config = load_config()
    admin_id = config.get("admin_chat_id") or ADMIN_CHAT_ID
    if admin_id and update.effective_chat.id != admin_id:
        return

    rows = get_subscribers_details()
    if not rows:
        await update.message.reply_text("لا يوجد مشتركون حتى الآن.")
        return

    lines = [f"👥 <b>قائمة المشتركين ({len(rows)}):</b>\n"]
    for i, (chat_id, username, first_name) in enumerate(rows, start=1):
        name = first_name or "بدون اسم"
        handle = f"@{username}" if username else "بدون معرّف"
        lines.append(f"{i}. {name} — {handle} — <code>{chat_id}</code>")

    text = "\n".join(lines)
    for chunk_start in range(0, len(text), 4000):
        await update.message.reply_text(
            text[chunk_start : chunk_start + 4000], parse_mode=ParseMode.HTML
        )


async def test_send(update: Update, context: ContextTypes.DEFAULT_TYPE):
    config = load_config()
    if not config["schedule"]:
        await update.message.reply_text("لا يوجد أذكار في الجدول بعد.")
        return
    entry = config["schedule"][0]
    await send_entry(context, entry, chat_ids=[update.effective_chat.id])


async def send_entry(context: ContextTypes.DEFAULT_TYPE, entry: dict, chat_ids=None):
    if chat_ids is None:
        chat_ids = get_all_subscribers()

    image_path = os.path.join(BASE_DIR, entry["image"]) if entry.get("image") else None
    has_image = image_path and os.path.exists(image_path)

    for chat_id in chat_ids:
        try:
            if has_image:
                with open(image_path, "rb") as img:
                    await context.bot.send_photo(chat_id=chat_id, photo=img)
            await context.bot.send_message(
                chat_id=chat_id,
                text=entry["text"],
                parse_mode=ParseMode.HTML,
            )
        except Exception as e:
            logger.warning(f"فشل الإرسال إلى {chat_id}: {e}")


async def scheduled_job(context: ContextTypes.DEFAULT_TYPE):
    entry = context.job.data
    logger.info(f"إرسال جدولة: {entry['id']}")
    await send_entry(context, entry)


def setup_jobs(application: Application, config: dict):
    from zoneinfo import ZoneInfo

    tz = ZoneInfo(config.get("timezone", "Asia/Riyadh"))
    for entry in config["schedule"]:
        hour, minute = map(int, entry["time"].split(":"))
        application.job_queue.run_daily(
            scheduled_job,
            time=dtime(hour=hour, minute=minute, tzinfo=tz),
            data=entry,
            name=entry["id"],
        )
        logger.info(f"تمت جدولة '{entry['id']}' الساعة {entry['time']} ({tz})")


def build_application() -> Application:
    if not BOT_TOKEN:
        raise RuntimeError("يجب ضبط متغير البيئة BOT_TOKEN بتوكن البوت من BotFather")

    init_db()
    config = load_config()

    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("stats", stats))
    application.add_handler(CommandHandler("users", users))
    application.add_handler(CommandHandler("test", test_send))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, any_message)
    )

    setup_jobs(application, config)
    return application


if __name__ == "__main__":
    app = build_application()
    logger.info("البوت يعمل الآن (polling)...")
    app.run_polling()