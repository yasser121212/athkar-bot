"""
نقطة الدخول عند النشر على Render.
Render يتطلب من خدمات الويب المجانية الاستماع على منفذ (PORT)، لذلك نشغّل
خادم Flask بسيط بجانب البوت الذي يعمل بنظام polling في خيط منفصل.
"""

import asyncio
import os
import threading

from flask import Flask
from bot import build_application

app = Flask(__name__)


@app.route("/")
def home():
    return "✅ بوت الأذكار يعمل الآن."


def run_bot():
    # بايثون لا ينشئ حلقة أحداث (event loop) تلقائيًا داخل الخيوط الفرعية،
    # لذلك ننشئها يدويًا هنا قبل تشغيل البوت.
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    application = build_application()
    # stop_signals=None ضروري لأن هذا يعمل داخل خيط فرعي وليس الخيط الرئيسي،
    # ومعالجة إشارات النظام (signals) لا تعمل إلا في الخيط الرئيسي.
    application.run_polling(close_loop=False, stop_signals=None)


if __name__ == "__main__":
    # تشغيل البوت في خيط منفصل بالخلفية
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()

    # تشغيل خادم الويب (مطلوب من Render لربط المنفذ)
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
