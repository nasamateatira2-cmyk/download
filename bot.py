import os
import telebot
import yt_dlp

BOT_TOKEN = "7692511945:AAHYBk6k-Ww70lUoQSOVbs-I-s-zzsvbtro"

bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start'])
def welcome(message):
    bot.reply_to(message, " أهلاً بك يا غالي! أرسل لي أي رابط فيديو لتحميله مباشرة أستخدمه في ما يرضي الله.")

@bot.message_handler(func=lambda msg: msg.text and msg.text.startswith("http"))
def handle_video(message):
    url = message.text.strip()
    status_msg = bot.reply_to(message, "⏳ جاري جلب الفيديو والمعالجة...")

    ydl_opts = {
        'format': 'best[ext=mp4][filesize<50M]/bestvideo[ext=mp4][filesize<40M]+bestaudio[ext=m4a]/best',
        'outtmpl': 'downloads/%(id)s.%(ext)s',
        'quiet': True,
        'no_warnings': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)

            with open(file_path, 'rb') as video_file:
                bot.send_video(message.chat.id, video_file, caption="تم التحميل بنجاح ✅")

            if os.path.exists(file_path):
                os.remove(file_path)

            bot.delete_message(message.chat.id, status_msg.message_id)

    except Exception:
        bot.edit_message_text("❌ تعذر التحميل: تأكد من صحة الرابط أو قد يكون حجم الفيديو أكبر من 50 ميغابايت.", 
                              message.chat.id, status_msg.message_id)

bot.infinity_polling()

