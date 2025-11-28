import os
import telebot
import google.generativeai as genai
from flask import Flask
from threading import Thread
import traceback # مكتبة لكشف تفاصيل الخطأ

# قراءة المفاتيح
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# إعداد Gemini
try:
    genai.configure(api_key=GEMINI_API_KEY)
    # سنستخدم موديل pro لأنه أكثر استقراراً من flash
    model = genai.GenerativeModel('gemini-pro')
except Exception as e:
    print(f"❌ Error in Setup: {e}")

bot = telebot.TeleBot(TELEGRAM_TOKEN)

# --- دوال الذكاء ---
def ask_gemini(text):
    # طباعة المفتاح (أول 5 حروف فقط) للتأكد أنه موجود
    if not GEMINI_API_KEY:
        print("❌ CRITICAL ERROR: API Key is missing or None!")
        return "يا زول مفتاح جوجل مافي! تأكد من الإعدادات."
    
    print(f"🔑 Key loaded (first 5 chars): {GEMINI_API_KEY[:5]}...")
    
    try:
        print(f"📡 Sending to Google: {text}")
        response = model.generate_content(f"أنت معلم سوداني. اشرح بلهجة سودانية: {text}")
        print("✅ Google Responded successfully!")
        return response.text
    except Exception as e:
        # طباعة الخطأ الكامل في الشاشة السوداء
        print(f"❌ GOOGLE ERROR: {e}")
        # إرجاع الخطأ لك في الشات عشان تشوفه
        return f"🚫 حصل خطأ من جوجل:\n{e}"

# --- أوامر البوت ---
@bot.message_handler(commands=['start'])
def welcome(message):
    bot.reply_to(message, "مرحبتين! 👋\nأنا شغال بنسخة كشف الأخطاء 🕵️‍♂️\nرسل لي أي كلمة.")

@bot.message_handler(func=lambda m: True)
def chat(message):
    bot.send_chat_action(message.chat.id, 'typing')
    reply = ask_gemini(message.text)
    bot.reply_to(message, reply)

# --- سيرفر Render ---
server = Flask(__name__)

@server.route("/")
def home():
    return "Bot is running!"

def run_web():
    server.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

def run_bot():
    bot.infinity_polling()

if __name__ == "__main__":
    t = Thread(target=run_web)
    t.start()
    run_bot()
