import os
import threading
import glob
from flask import Flask
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import yt_dlp

# تشغيل خادم ويب داخلي لمنع خطأ 15 دقيقة على Render
web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "Downloader Bot is Running 24/7!"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    web_app.run(host="0.0.0.0", port=port)

# جلب التوكن بأمان من متغيرات البيئة
BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

WELCOME_MSG = (
    "تم انشاء هذا البوت من قبل ابو الجود 🌟\n\n"
    "اهلا وسهلا بك يا غالي ارسل اي رابط لتنزيله مباشرة\n"
    "(استخدمه بما يرضي الله عز وجل)"
)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, WELCOME_MSG)

@bot.message_handler(func=lambda msg: msg.text and msg.text.startswith("http"))
def handle_download(message):
    url = message.text.strip()
    status_msg = bot.reply_to(message, "⏳ جاري المعالجة اذكر الله...")

    ydl_opts = {
        'format': 'best[ext=mp4]/best',
        'outtmpl': f'downloads/{message.chat.id}_%(id)s.%(ext)s',
        'max_filesize': 48 * 1024 * 1024, # حد أقصى 48MB لحجم تيليجرام
        'quiet': True,
        'no_warnings': True,
    }

    os.makedirs("downloads", exist_ok=True)
    video_path = None

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            video_path = ydl.prepare_filename(info)

        if video_path and os.path.exists(video_path):
            with open(video_path, 'rb') as video_file:
                bot.send_video(
                    chat_id=message.chat.id,
                    video=video_file,
                    caption="✅ تم التحميل بنجاح بواسطة بوت ابو الجود",
                    reply_to_message_id=message.message_id
                )
            bot.delete_message(chat_id=message.chat.id, message_id=status_msg.message_id)
        else:
            bot.edit_message_text("❌ تعذر العثور على الملف المحمل.", chat_id=message.chat.id, message_id=status_msg.message_id)

    except yt_dlp.utils.DownloadError as e:
        bot.edit_message_text("❌ تعذر تحميل هذا الرابط، أو أن حجم الفيديو يتجاوز حد تيليجرام (50MB).", chat_id=message.chat.id, message_id=status_msg.message_id)
    except Exception as e:
        bot.edit_message_text(f"❌ حدث خطأ غير متوقع أثناء التحميل.", chat_id=message.chat.id, message_id=status_msg.message_id)
    finally:
        # تنظيف الملفات المؤقتة لتوفير مساحة السيرفر
        if video_path and os.path.exists(video_path):
            try:
                os.remove(video_path)
            except Exception:
                pass

if __name__ == "__main__":
    threading.Thread(target=run_web, daemon=True).start()
    print("Downloader Bot Started Successfully...")
    bot.infinity_polling(skip_pending=True)
