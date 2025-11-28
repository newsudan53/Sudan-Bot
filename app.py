import os
import telebot
import google.generativeai as genai
from flask import Flask
from threading import Thread
import traceback

# قراءة المفاتيح
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# إعداد Gemini (تم التحديث إلى 1.5 Flash الأحدث والأسرع)
try:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    print(f"❌ Error in Setup: {e}")

bot = telebot.TeleBot(TELEGRAM_TOKEN)

# --- دوال الذكاء ---
def ask_gemini(text):
    if not GEMINI_API_KEY:
        return "يا زول مفتاح جوجل مافي! تأكد من الإعدادات."
    
    try:
        # إضافة تعليمات لتقمص الشخصية بشكل أفضل
        prompt = f"أنت مساعد سوداني ذكي ومفيد. تحدث باللهجة السودانية العامية. اشرح بوضوح وبساطة: {text}"
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"❌ GOOGLE ERROR: {e}")
        traceback.print_exc()
        return "حصلت مشكلة تقنية بسيطة، جرب مرة تانية."

# --- أوامر البوت ---
@bot.message_handler(commands=['start'])
def welcome(message):
    bot.reply_to(message, "مرحبتين حبابك! 👋\nأنا شغال بأحدث موديل (Gemini 1.5 Flash) 🚀\nرسل لي أي سؤال.")

@bot.message_handler(func=lambda m: True)
def chat(message):
    bot.send_chat_action(message.chat.id, 'typing')
    reply = ask_gemini(message.text)
    bot.reply_to(message, reply)

# --- سيرفر Render ---
server = Flask(__name__)

@server.route("/")
def home():
    return "Bot is running with Gemini 1.5 Flash!"

def run_web():
    server.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

def run_bot():
    bot.infinity_polling()

if __name__ == "__main__":
    t = Thread(target=run_web)
    t.start()
    run_bot()
