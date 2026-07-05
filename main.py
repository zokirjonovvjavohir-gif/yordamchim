import telebot
import requests
import os
from telebot import types

TOKEN = os.getenv("TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not TOKEN or not GROQ_API_KEY:
    print("TOKEN yoki GROQ_API_KEY yo‘q!")
    exit()

bot = telebot.TeleBot(TOKEN)

# MEMORY (eslab qolish)
user_memory = {}


def ask_ai(message, text):
    user_id = message.chat.id

    # memory yaratish
    if user_id not in user_memory:
        user_memory[user_id] = []

    user_memory[user_id].append(text)

    # faqat oxirgi 5 ta gapni saqlaydi
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
                "content": "Sen o‘zbek tilida aniq, qisqa va tushunarli javob beradigan AI assistantsan."
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
        print("REQUEST ERROR:", e)
        return "Ulanish xatoligi 😔"


# START MENU
@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    markup.add(
        types.KeyboardButton("🤖 AI bilan gaplashish"),
        types.KeyboardButton("ℹ️ Yordam")
    )

    bot.send_message(
        message.chat.id,
        "Salom 🤖 Men Javoxirning AI botiman!\nSavol ber yoki tugmani bosing.",
        reply_markup=markup
    )


# HELP
@bot.message_handler(func=lambda message: message.text == "ℹ️ Yordam")
def help_cmd(message):
    bot.reply_to(message, "Menga istalgan savolni yozing 🤖 Men javob beraman.")


# AI MODE
@bot.message_handler(func=lambda message: message.text == "🤖 AI bilan gaplashish")
def ai_mode(message):
    bot.reply_to(message, "Endi savol yozing 😎")


# NORMAL CHAT
@bot.message_handler(func=lambda message: True)
def handle(message):
    reply = ask_ai(message, message.text)
    bot.reply_to(message, reply)


print("BOT STARTED 🚀")
bot.infinity_polling()
