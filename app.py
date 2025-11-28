import os
import telebot
import google.generativeai as genai
from gtts import gTTS
from flask import Flask
from threading import Thread
import traceback

# ==========================================
# المفاتيح تقرأ من إعدادات Render (آمنة)
# ==========================================
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# إعداد Gemini (الموديل الأحدث والأسرع)
try:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-2.5-flash')
except Exception as e:
    print(f"❌ Error in Setup: {e}") 

# إعداد البوت
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# --- دوال الذكاء ---
def ask_gemini(text):
    if not GEMINI_API_KEY:
        return "يا زول مفتاح جوجل مافي!"
    
    try:
        # قمنا بحذف الـ Pollinations واستبدلناه بـ Gemini مباشرةً
        prompt = f"أنت مساعد سوداني خبير. تحدث باللهجة السودانية العامية. اشرح بوضوح وبساطة: {text}"
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        # طباعة الخطأ الكامل في السجلات
        print(f"❌ GOOGLE RUNTIME ERROR: {e}")
        traceback.print_exc()
        return f"🚫 حصلت مشكلة تقنية بسيطة، جرب مرة تانية."

def send_audio(chat_id, text):
    try:
        tts = gTTS(text=text, lang='ar')
        filename = f"voice_{chat_id}.mp3"
        tts.save(filename)
        with open(filename, 'rb') as audio:
            bot.send_audio(chat_id, audio, title="شرح صوتي 🎧")
        os.remove(filename)
    except:
        pass

# --- أوامر البوت ---
@bot.message_handler(commands=['start'])
def welcome(message):
    bot.reply_to(message, "مرحبتين! 👋 أنا شغال على Render الآن.")

@bot.message_handler(func=lambda m: True)
def chat(message):
    bot.send_chat_action(message.chat.id, 'typing')
    reply = ask_gemini(message.text)
    bot.reply_to(message, reply)

# --- تشغيل السيرفر ---
server = Flask(__name__)

@server.route("/")
def home():
    return "Bot is running on Render!"

def run_web():
    server.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

def run_bot():
    bot.infinity_polling()

if __name__ == "__main__":
    t = Thread(target=run_web)
    t.start()
    run_bot()
