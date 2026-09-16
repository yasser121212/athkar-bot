"""
بوت تلغرام لإرسال الأذكار تلقائيًا للمشتركين حسب جدول زمني محدد في config.json
"""

import json
import logging
import os
import sqlite3
from datetime import time as dtime

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
DB_PATH = os.path.join(BASE_DIR, "subscribers.db")
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")

BOT_TOKEN = os.environ.get("BOT_TOKEN")


# ---------- قاعدة البيانات ----------
def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """CREATE TABLE IF NOT EXISTS subscribers (
                chat_id INTEGER PRIMARY KEY,
                joined_at TEXT DEFAULT CURRENT_TIMESTAMP
           )"""
    )
    conn.commit()
    conn.close()


def add_subscriber(chat_id: int):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT OR IGNORE INTO subscribers (chat_id) VALUES (?)", (chat_id,)
    )
    conn.commit()
    conn.close()


def remove_subscriber(chat_id: int):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM subscribers WHERE chat_id = ?", (chat_id,))
    conn.commit()
    conn.close()


def get_all_subscribers():
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("SELECT chat_id FROM subscribers").fetchall()
    conn.close()
    return [r[0] for r in rows]


def subscriber_count():
    conn = sqlite3.connect(DB_PATH)
    count = conn.execute("SELECT COUNT(*) FROM subscribers").fetchone()[0]
    conn.close()
    return count


# ---------- الإعدادات ----------
def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


# ---------- أوامر البوت ----------
def build_welcome_text() -> str:
    return (
        "🕌 <b>مرحبًا بك في بوت الأذكار</b>\n\n"
        "تم تفعيل اشتراكك بنجاح ✅\n"
        "سيصلك تذكير تلقائي بأذكار الصباح والمساء في مواعيدها بإذن الله.\n\n"
        "━━━━━━━━━━━━━━\n\n"
        "📌 <b>الأوامر المتاحة لك:</b>\n"
        "• /test — معاينة أول ذكر في الجدول فورًا\n\n"
        "💬 لأي استفسار أو اقتراح تواصل معنا: @Yassseeeer\n\n"
        "🤍 لا تنسونا من صالح دعائكم"
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    add_subscriber(chat_id)
    await update.message.reply_text(build_welcome_text(), parse_mode=ParseMode.HTML)


async def any_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """يرد بنفس رسالة الترحيب على أي رسالة نصية عادية (غير أمر) يرسلها المستخدم."""
    chat_id = update.effective_chat.id
    add_subscriber(chat_id)
    await update.message.reply_text(build_welcome_text(), parse_mode=ParseMode.HTML)


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    remove_subscriber(chat_id)
    await update.message.reply_text("❌ تم إلغاء اشتراكك. نسأل الله أن يحفظك.")


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    config = load_config()
    admin_id = config.get("admin_chat_id")
    if admin_id
