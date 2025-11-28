import os
import telebot
from gtts import gTTS
from flask import Flask
from threading import Thread
import PyPDF2
import requests

# ==========================================
# ملاحظة: مفتاح Gemini محذوف نهائياً من الكود
# ==========================================
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
# نحتاج هذا ليتعرف Render على البوت
# GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY") 

# إعداد البوت
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# --- دالة الذكاء المفتوح (التي لا تحتاج مفتاح) ---
def get_ai_response(text):
    try:
        # استخدام Pollinations AI لجميع الردود
        prompt = f"أنت مساعد سوداني خبير. تحدث باللهجة السودانية العامية. اشرح بوضوح وبساطة: {text}"
        response = requests.post("https://text.pollinations.ai/", json={"messages": [{"role": "user", "content": prompt}]})
        
        # إذا نجحت الخدمة
        if response.status_code == 200:
            return response.text
        else:
            return "عفواً، الخدمة المفتوحة مشغولة حالياً."
    except Exception as e:
        return f"خطأ في الاتصال: {e}"


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

# --- أوامر البوت (Handlers) ---
@bot.message_handler(commands=['start'])
def welcome(message):
    bot.reply_to(message, "مرحبتين! 👋 أنا الآن شغال بنظام 'الذكاء المفتوح' (Open AI) ومستعد للإجابة على كل أسئلتك.")

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    # إيقاف تحليل الصور لأنها تحتاج مفتاح جوجل المرفوض
    bot.reply_to(message, "🚫 خاصية تحليل الصور معطلة حالياً بسبب حظر جوجل للمفاتيح. أرسل سؤالاً نصياً بدلاً من ذلك.")

@bot.message_handler(content_types=['document'])
def handle_docs(message):
    if message.document.mime_type != 'application/pdf':
        bot.reply_to(message, "ملفات PDF بس يا غالي.")
        return
        
    bot.send_chat_action(message.chat.id, 'typing')
    status_msg = bot.reply_to(message, "جاري قراءة الملف... ⏳")
    try:
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        with open("temp.pdf", 'wb') as new_file:
            new_file.write(downloaded_file)
            
        reader = PyPDF2.PdfReader("temp.pdf")
        txt = "".join([page.extract_text() for page in reader.pages[:3]])
        summ = get_ai_response(txt)
        
        bot.edit_message_text(f"📝 **الملخص:**\n{summ}", chat_id=message.chat.id, message_id=status_msg.message_id)
        send_audio(message.chat.id, summ)
        os.remove("temp.pdf")
    except Exception as e:
        bot.reply_to(message, f"خطأ: {e}")

@bot.message_handler(func=lambda message: True)
def chat(message):
    # الآن كل الرسائل النصية تذهب للذكاء المفتوح
    bot.send_chat_action(message.chat.id, 'typing')
    reply = get_ai_response(message.text)
    bot.reply_to(message, reply)

# --- تشغيل السيرفر ---
server = Flask(__name__)

@server.route("/")
def home():
    return "Bot is running on Open AI System!"

def run_web():
    server.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

def run_bot():
    bot.infinity_polling()

if __name__ == "__main__":
    t = Thread(target=run_web)
    t.start()
    run_bot()
