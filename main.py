import telebot
import requests
import os
from telebot import types
from gtts import gTTS
import uuid

TOKEN = os.getenv("TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not TOKEN or not GROQ_API_KEY:
    print("TOKEN yoki GROQ_API_KEY yo‘q!")
    exit()

bot = telebot.TeleBot(TOKEN)

user_memory = {}


def ask_ai(message, text):
    user_id = message.chat.id

    if user_id not in user_memory:
        user_memory[user_id] = []

    user_memory[user_id].append(text)

    if len(user_memory[user_id]) > 5:
        user_memory[user_id].pop(0)

    url = "https://api.groq.com/openai/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "llama-3.1-8b-instant",
        "messages": [
            {
                "role": "system",
                "content": "Sen o‘zbek tilida aniq va tushunarli javob beradigan AI botsan."
            },
            {
                "role": "user",
                "content": "Oldingi suhbat: " + str(user_memory[user_id]) + "\n\nSavol: " + text
            }
        ],
        "temperature": 0.2
    }

    try:
        bot.send_chat_action(message.chat.id, "typing")

        res = requests.post(url, headers=headers, json=data, timeout=20)

        if res.status_code != 200:
            print("API ERROR:", res.text)
            return "AI xatolik 😔"

        return res.json()["choices"][0]["message"]["content"]

    except Exception as e:
        print("ERROR:", e)
        return "Ulanish xatoligi 😔"


def text_to_voice(text):
    try:
        filename = f"voice_{uuid.uuid4()}.mp3"
        tts = gTTS(text=text, lang="uz")
        tts.save(filename)
        return filename
    except Exception as e:
        print("VOICE ERROR:", e)
        return None


@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    markup.add(
        types.KeyboardButton("🤖 AI bilan gaplashish"),
        types.KeyboardButton("ℹ️ Yordam")
    )

    bot.send_message(
        message.chat.id,
        "Salom 🤖 Men Javohirning AI botiman!\nSavol ber yoki tugmani bosing.",
        reply_markup=markup
    )


@bot.message_handler(func=lambda message: message.text == "ℹ️ Yordam")
def help_cmd(message):
    bot.reply_to(message, "Menga istalgan savolni yozing 🤖 Men javob beraman.")


@bot.message_handler(func=lambda message: message.text == "🤖 AI bilan gaplashish")
def ai_mode(message):
    bot.reply_to(message, "Endi savol yozing 😎")


@bot.message_handler(func=lambda message: True)
def handle_text(message):
    reply = ask_ai(message, message.text)
    bot.reply_to(message, reply)


@bot.message_handler(content_types=['voice'])
def handle_voice(message):
    try:
        file_info = bot.get_file(message.voice.file_id)
        downloaded_file = bot.download_file(file_info.file_path)

        with open("voice.ogg", "wb") as f:
            f.write(downloaded_file)

        reply = ask_ai(message, "Foydalanuvchi ovoz yubordi")

        audio = text_to_voice(reply)

        if audio:
            bot.send_voice(message.chat.id, open(audio, "rb"))
        else:
            bot.reply_to(message, reply)

    except Exception as e:
        print("VOICE HANDLER ERROR:", e)
        bot.reply_to(message, "Voice xatolik 😔")


print("BOT STARTED 🚀")
bot.infinity_polling()
