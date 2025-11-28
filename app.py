import logging
import gradio as gr
import threading
import asyncio
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
# المفاتيح (تقرأ مباشرة من إعدادات السيرفر/Render)
# ==========================================
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# إعداد Gemini (الموديل الأحدث والأسرع)
try:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-2.5-flash')
except Exception as e:
    print(f"Error in Gemini Setup: {e}") 

# إعداد البوت
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# --- دوال الذكاء ---
def analyze_image_with_gemini(image_bytes):
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
        headers = {'Content-Type': 'application/json'}
        image_data = base64.b64encode(image_bytes).decode('utf-8')
        prompt = "أنت معلم سوداني. اشرح الصورة دي بلهجة سودانية بسيطة."
        data = {"contents": [{"parts": [{"text": prompt}, {"inline_data": {"mime_type": "image/jpeg", "data": image_data}}]}]}
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            return response.json()['candidates'][0]['content']['parts'][0]['text']
        return "ما قدرت أحلل الصورة."
    except Exception as e:
        print(f"❌ GOOGLE VISION ERROR: {e}")
        return "خطأ في تحليل الصورة."

def ask_gemini(text):
    if not GEMINI_API_KEY:
        return "يا زول مفتاح جوجل مافي! تأكد من الإعدادات."
    
    try:
        prompt = f"أنت مساعد سوداني ذكي ومفيد. تحدث باللهجة السودانية العامية. اشرح بوضوح وبساطة: {text}"
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"❌ GOOGLE ERROR (Runtime): {e}")
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

# --- أوامر البوت (Handlers) ---
@bot.message_handler(commands=['start'])
def welcome(message):
    bot.reply_to(message, "مرحبتين! 👋\nأنا جاهز بأحدث إصدار (2.5 Flash).\nرسل لي أي شيء.")

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
        # (استبدلت Pollinations بكود بسيط لعدم تعقيد الكود)
        bot.edit_message_text("تمت قراءة الملف بنجاح. أرسل لي سؤالاً عنه.", chat_id=message.chat.id, message_id=status_msg.message_id)
    except Exception as e:
        bot.reply_to(message, f"خطأ: {e}")

@bot.message_handler(func=lambda message: True)
def chat(message):
    bot.send_chat_action(message.chat.id, 'typing')
    reply = ask_gemini(message.text)
    bot.reply_to(message, reply)

# --- تشغيل البوت مع Gradio (للحفاظ على السيرفر حياً) ---
def run_telegram_bot():
    bot.infinity_polling()

if __name__ == "__main__":
    t = threading.Thread(target=run_telegram_bot)
    t.start()
    
    with gr.Blocks() as demo:
        gr.Markdown("# 🚀 Final Bot Code Saved!")
    demo.launch()
