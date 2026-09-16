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
ADMIN_CHAT_ID = 6644045109  # رقمك الشخصي في تلغرام، يُستخدم لحصر أمر /stats عليك فقط


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
    count = conn.execute("SELECT COUNT(*) FROM
