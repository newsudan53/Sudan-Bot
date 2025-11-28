import logging
import gradio as gr
import threading
import os
import requests
import base64
from telegram import Update
from telebot import types
import telebot
import PyPDF2
from gtts import gTTS
import google.generativeai as genai
import traceback

# ==========================================
# المفاتيح (جاهزة للعمل على Render)
# ==========================================
TELEGRAM_TOKEN = "8550934452:AAGDUy_oCrSNz1xTNznYM399YrnHls5vIBY"
GEMINI_API_KEY = "AIzaSyAN5elXRHT5WDbbAuz2ASSKAV0bTl3tFpo"
# ==========================================

# إعداد Gemini (الموديل الأحدث والأسرع: 2.5 Flash)
try:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-2.5-flash')
except Exception as e:
    print(f"Error in Gemini Setup: {e}") 

# إعداد البوت
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# --- دوال الذكاء ---
def ask_gemini(text):
    if not GEMINI_API_KEY:
        return "يا زول مفتاح جوجل مافي! تأكد من الإعدادات."
    
    try:
        prompt = f"أنت مساعد سوداني ذكي ومفيد. تحدث باللهجة السودانية العامية. اشرح بوضوح وبساطة: {text}"
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        # طباعة الخطأ الكامل في السجلات (Logs) لكشف المشكلة
        print(f"❌ GOOGLE ERROR (Runtime): {e}")
        traceback.print_exc()
        return f"🚫 حصل خطأ من جوجل: {e}"

def ask_pollinations(text):
    # نستخدم Pollinations لتلخيص الملفات البسيطة لتقليل استهلاك Gemini
    try:
        prompt = f"لخص واشرح بلهجة سودانية: {text[:2000]}"
        response = requests.post("https://text.pollinations.ai/", json={"messages": [{"role": "user", "content": prompt}]})
        return response.text if response.status_code == 200 else "السيرفر مشغول."
    except:
        return "خطأ في الشبكة."

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
    bot.reply_to(message, "مرحبتين! 👋 أنا شغال بأحدث موديل (Gemini 2.5 Flash) 🚀\nرسل لي أي سؤال.")

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    bot.send_chat_action(message.chat.id, 'typing')
    status_msg = bot.reply_to(message, "جاري تحليل الصورة... 📸")
    try:
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        text = analyze_image_with_gemini(downloaded_file)
        bot.edit_message_text(f"👁️ **التحليل:**\n{text}", chat_id=message.chat.id, message_id=status_msg.message_id)
        send_audio(message.chat.id, text)
    except Exception as e:
        bot.reply_to(message, f"حصل خطأ في الصورة: {e}")

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
        txt = "".join([page.extract_text() for page in reader.pages[:3]]) # أول 3 صفحات
            
        summ = ask_pollinations(txt)
        
        bot.edit_message_text(f"📝 **الملخص:**\n{summ}", chat_id=message.chat.id, message_id=status_msg.message_id)
        send_audio(message.chat.id, summ)
        os.remove("temp.pdf")
    except Exception as e:
        bot.reply_to(message, f"خطأ: {e}")

@bot.message_handler(func=lambda message: True)
def chat(message):
    bot.send_chat_action(message.chat.id, 'typing')
    reply = ask_gemini(message.text)
    bot.reply_to(message, reply)

# --- تشغيل البوت مع Gradio ---
def run_telegram_bot():
    bot.infinity_polling()

if __name__ == "__main__":
    # تشغيل البوت في خيط منفصل
    t = threading.Thread(target=run_telegram_bot)
    t.start()
    
    # واجهة Gradio لإبقاء السيرفر حياً
    with gr.Blocks() as demo:
        gr.Markdown("# 🚀 Final Bot Deployed and Running!")
    demo.launch()
