import os
import telebot
import google.generativeai as genai
from gtts import gTTS
from flask import Flask
from threading import Thread

# قراءة المفاتيح من إعدادات السيرفر (Render)
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# إعداد Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# إعداد البوت
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# --- دوال الذكاء ---
def ask_gemini(text):
    try:
        response = model.generate_content(f"أنت معلم سوداني. اشرح بلهجة سودانية بسيطة: {text}")
        return response.text
    except:
        return "الشبكة تعبانة شوية، جرب تاني."

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
    bot.reply_to(message, "مرحبتين! 👋\nأنا شغال من سيرفر Render القوي! 🚀\nرسل لي أي سؤال.")

@bot.message_handler(func=lambda m: True)
def chat(message):
    # إشعار "جاري الكتابة"
    bot.send_chat_action(message.chat.id, 'typing')
    
    reply = ask_gemini(message.text)
    bot.reply_to(message, reply)
    
    # ميزة الصوت (اختياري - مفعلة)
    # send_audio(message.chat.id, reply)

# --- سيرفر وهمي لـ Render ---
server = Flask(__name__)

@server.route("/")
def home():
    return "Bot is running on Render!"

def run_web():
    # Render بيدينا بورت خاص، لازم نستخدمه
    server.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

def run_bot():
    bot.infinity_polling()

if __name__ == "__main__":
    # تشغيل السيرفر والبوت معاً
    t = Thread(target=run_web)
    t.start()
    run_bot()
