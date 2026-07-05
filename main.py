import telebot
import requests
import os

TOKEN = os.getenv("TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not TOKEN or not GROQ_API_KEY:
    print("TOKEN yoki GROQ_API_KEY yo‘q!")
    exit()

bot = telebot.TeleBot(TOKEN)

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

@bot.message_handler(func=lambda message: True)
def handle(message):
    reply = ask_ai(message.text)
    bot.reply_to(message, reply)

print("BOT STARTED")
bot.infinity_polling()
