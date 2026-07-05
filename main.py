import telebot
import requests
import os
from telebot import types

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    btn1 = types.KeyboardButton("🤖 AI bilan gaplashish")
    btn2 = types.KeyboardButton("ℹ️ Yordam")

    markup.add(btn1, btn2)

    bot.send_message(
        message.chat.id,
        "Salom 🤖 Men AI botman!\nSavol ber yoki tugmani bosing.",
        reply_markup=markup
    )
TOKEN = os.getenv("TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not TOKEN or not GROQ_API_KEY:
    print("TOKEN yoki GROQ_API_KEY yo‘q!")
    exit()

bot = telebot.TeleBot(TOKEN)
@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    btn1 = types.KeyboardButton("🤖 AI bilan gaplashish")
    btn2 = types.KeyboardButton("ℹ️ Yordam")

    markup.add(btn1, btn2)

    bot.send_message(
        message.chat.id,
        "Salom 🤖 Men AI botman!\nSavol ber yoki tugmani bosing.",
        reply_markup=markup
    )
def ask_ai(text):
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
                "content": "Sen o‘zbek tilida aniq va tushunarli javob beradigan yordamchi botsan."
            },
            {
                "role": "user",
                "content": text
            }
        ],
        "temperature": 0.3
    }

    try:
        res = requests.post(url, headers=headers, json=data, timeout=20)

        if res.status_code != 200:
            print("API ERROR:", res.text)
            return "AI xatolik 😔"

        return res.json()["choices"][0]["message"]["content"]

    except Exception as e:
        print("REQUEST ERROR:", e)
        return "Ulanish xatoligi 😔"

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Salom 🤖 Men AI botman! Menga savol ber")
@bot.message_handler(func=lambda message: message.text == "ℹ️ Yordam")
def help_cmd(message):
    bot.reply_to(message, "Menga istalgan savolni yozing 🤖 Men javob beraman.")
@bot.message_handler(func=lambda message: True)
def handle(message):
    reply = ask_ai(message.text)
    bot.reply_to(message, reply)
@bot.message_handler(func=lambda message: message.text == "🤖 AI bilan gaplashish")
def ai_mode(message):
    bot.reply_to(message, "Endi savol yozing 😎")
print("BOT STARTED")
bot.infinity_polling()
print("BOT STARTED")
bot.infinity_polling()
