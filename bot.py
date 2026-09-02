import os
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import yt_dlp

BOT_TOKEN = "7692511945:AAHYBk6k-Ww7OlUoCW0iY9t95d_Z9xO4p4U"

bot = telebot.TeleBot(BOT_TOKEN)

user_links = {}

@bot.message_handler(commands=['start'])
def welcome(message):
    welcome_text = (
        "تم إنشاء هذا البوت من قبل أبو الجود ✨\n\n"
        "أهلاً وسهلاً بك يا غالي! أرسل لي أي رابط لتنزيله مباشرة.\n"
        "(استخدمه بما يرضي الله عز وجل)"
    )
    bot.reply_to(message, welcome_text)

@bot.message_handler(func=lambda msg: msg.text and msg.text.startswith("http"))
def ask_download_type(message):
    url = message.text.strip()
    user_links[message.chat.id] = url
    
    markup = InlineKeyboardMarkup()
    btn_video = InlineKeyboardButton("🎬 تحميل فيديو (MP4)", callback_data="download_video")
    btn_audio = InlineKeyboardButton("🎵 تحميل صوت فقط (MP3)", callback_data="download_audio")
    markup.row(btn_video, btn_audio)
    
    bot.reply_to(message, "اختر طريقة التحميل المطلوبة:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def process_download(call):
    chat_id = call.message.chat.id
    url = user_links.get(chat_id)
    
    if not url:
        bot.answer_callback_query(call.id, "انتهت صلاحية الطلب، أرسل الرابط مرة أخرى.")
        return

    bot.answer_callback_query(call.id)
    bot.edit_message_text("⏳ جاري المعالجة... اذكر الله", chat_id=chat_id, message_id=call.message.message_id)

    if call.data == "download_video":
        ydl_opts = {
            'format': 'best[ext=mp4][filesize<48M]/best[filesize<48M]/best',
            'outtmpl': f'downloads/{chat_id}_video.%(ext)s',
            'quiet': True,
            'no_warnings': True
        }
    else:
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': f'downloads/{chat_id}_audio.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': True,
            'no_warnings': True
        }

    try:
        os.makedirs('downloads', exist_ok=True)
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            if call.data == "download_audio":
                filename = os.path.splitext(filename)[0] + ".mp3"

        if os.path.exists(filename):
            with open(filename, 'rb') as media_file:
                if call.data == "download_video":
                    bot.send_video(chat_id, media_file, caption="تم التحميل بنجاح ✅\n(استخدمه بما يرضي الله عز وجل)")
                else:
                    bot.send_audio(chat_id, media_file, caption="تم استخراج الصوت بنجاح 🎵\n(استخدمه بما يرضي الله عز وجل)")
            
            os.remove(filename)
            bot.delete_message(chat_id=chat_id, message_id=call.message.message_id)
    except Exception as e:
        bot.send_message(chat_id, f"عذراً، حدث خطأ أثناء التحميل: {str(e)[:100]}")

bot.infinity_polling()
