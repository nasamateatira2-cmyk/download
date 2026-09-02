import os
import threading
import glob
from flask import Flask
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import yt_dlp

# خادم ويب لإبقاء الخدمة نشطة على Render
web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "Downloader Bot is Running 24/7!"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    web_app.run(host="0.0.0.0", port=port)

# جلب التوكن بأمان
BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

WELCOME_MSG = (
    "تم انشاء هذا البوت من قبل ابو الجود 🌟\n\n"
    "أهلاً وسهلاً بك يا غالي! أرسل أي رابط وسأعطيك خيار تحميله كفيديو أو ملف صوتي مباشرة.\n"
    "(استخدمه بما يرضي الله عز وجل)"
)

# حفظ الروابط مؤقتاً لتحديد نوع التحميل عبر الأزرار
user_urls = {}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, WELCOME_MSG)

@bot.message_handler(func=lambda msg: msg.text and msg.text.startswith("http"))
def handle_url(message):
    url = message.text.strip()
    user_urls[message.chat.id] = url

    keyboard = InlineKeyboardMarkup(row_width=2)
    btn_video = InlineKeyboardButton("🎬 تحميل فيديو (MP4)", callback_data="download_video")
    btn_audio = InlineKeyboardButton("🎵 تحميل صوت (MP3)", callback_data="download_audio")
    keyboard.add(btn_video, btn_audio)

    bot.reply_to(message, "اختر الصيغة المطلوبة للتحميل:", reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data in ["download_video", "download_audio"])
def process_callback(call):
    chat_id = call.message.chat.id
    url = user_urls.get(chat_id)

    if not url:
        bot.answer_callback_query(call.id, "انتهت صلاحية الطلب، أرسل الرابط مرة أخرى.")
        return

    bot.answer_callback_query(call.id)
    choice = call.data
    media_type = "فيديو" if choice == "download_video" else "صوت"
    
    bot.edit_message_text(
        f"⏳ جاري تجهيز الـ {media_type}، اذكر الله...",
        chat_id=chat_id,
        message_id=call.message.message_id
    )

    os.makedirs("downloads", exist_ok=True)
    out_template = f"downloads/{chat_id}_%(id)s.%(ext)s"

    if choice == "download_video":
        ydl_opts = {
            'format': 'best[ext=mp4]/best',
            'outtmpl': out_template,
            'max_filesize': 48 * 1024 * 1024,
            'quiet': True,
            'no_warnings': True,
        }
    else:
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': out_template,
            'max_filesize': 48 * 1024 * 1024,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': True,
            'no_warnings': True,
        }

    file_path = None
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)
            if choice == "download_audio":
                # تعديل الامتداد إلى mp3 إذا تم التحويل
                base, _ = os.path.splitext(file_path)
                file_path = f"{base}.mp3"

        if file_path and os.path.exists(file_path):
            with open(file_path, 'rb') as f:
                if choice == "download_video":
                    bot.send_video(
                        chat_id=chat_id,
                        video=f,
                        caption="✅ تم التحميل بنجاح بواسطة بوت ابو الجود",
                        reply_to_message_id=call.message.message_id
                    )
                else:
                    bot.send_audio(
                        chat_id=chat_id,
                        audio=f,
                        caption="✅ تم استخراج الصوت بنجاح بواسطة بوت ابو الجود",
                        reply_to_message_id=call.message.message_id
                    )
            bot.delete_message(chat_id=chat_id, message_id=call.message.message_id)
        else:
            bot.edit_message_text("❌ تعذر العثور على الملف المحمل.", chat_id=chat_id, message_id=call.message.message_id)

    except yt_dlp.utils.DownloadError:
        bot.edit_message_text("❌ تعذر التحميل: قد يكون الرابط خاصاً، محظوراً، أو حجمه أكبر من 50MB.", chat_id=chat_id, message_id=call.message.message_id)
    except Exception as e:
        bot.edit_message_text("❌ حدث خطأ أثناء المعالجة.", chat_id=chat_id, message_id=call.message.message_id)
        print(f"Error: {e}")
    finally:
        # حذف الملفات المتبقية لتفريغ السيرفر
        matching_files = glob.glob(f"downloads/{chat_id}_*")
        for f in matching_files:
            try:
                os.remove(f)
            except Exception:
                pass

if __name__ == "__main__":
    threading.Thread(target=run_web, daemon=True).start()
    print("Downloader Bot Started Successfully...")
    bot.infinity_polling(skip_pending=True)
