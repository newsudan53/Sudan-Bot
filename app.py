import os
import json
import logging
from flask import Flask, request, abort
import telebot
import google.generativeai as genai
from gtts import gTTS
import PyPDF2

# ==========================================
# مفاتيحك (تقرأ من إعدادات Render)
# ==========================================
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# إعداد البوت
bot = telebot.TeleBot(TELEGRAM_TOKEN, parse_mode='html')
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

# إعداد سيرفر Flask
server = Flask(__name__)

# --- دوال الذكاء ---
def ask_gemini(text):
    try:
        response = model.generate_content(f"أنت مساعد سوداني خبير. أجب بلهجة سودانية: {text}")
        return response.text
    except Exception as e:
        return f"🚫 عذراً، خطأ في جوجل (تأكد من مفتاح Gemini)."

# --- الرد على الأوامر ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "مرحبتين! 👋\nأنا شغال الآن بنظام الـ Webhooks الآمن. أرسل لي أي سؤال.")

@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.send_chat_action(message.chat.id, 'typing')
    reply = ask_gemini(message.text)
    bot.reply_to(message, reply)

# --- نقطة دخول الـ Webhook (الأهم) ---
@server.route('/' + TELEGRAM_TOKEN, methods=['POST'])
def get_message():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return '!', 200
    else:
        abort(403)

# --- تشغيل الخادم ---
if __name__ == "__main__":
    # هذا الأمر سيقوم بضبط الـ Webhook وإطلاق الخادم معًا
    WEBHOOK_URL = os.environ.get('RENDER_EXTERNAL_URL') + TELEGRAM_TOKEN
    
    # Render يضع عنوان URL الخاص بنا في متغير البيئة هذا
    if 'RENDER_EXTERNAL_URL' in os.environ:
        bot.set_webhook(url=os.environ.get('RENDER_EXTERNAL_URL') + TELEGRAM_TOKEN)
        server.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
    else:
        # إذا كنت على جهازك المحلي، يشتغل Polling (للتجربة فقط)
        bot.remove_webhook()
        bot.polling()
