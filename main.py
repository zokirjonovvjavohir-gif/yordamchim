import telebot
import requests
import os

TOKEN = os.getenv("TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

print("TOKEN:", TOKEN)
print("GROQ:", GROQ_API_KEY)

if not TOKEN:
    print("TOKEN YO‘Q!")
    exit()

bot = telebot.TeleBot(TOKEN)

def ask_ai(text):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
    ""model": "llama-3.1-8b-instant"
    "messages": [
        {
            "role": "system",
            "content": "Sen o‘zbek tilida aniq, tushunarli va qisqa javob beradigan yordamchi botsan."
        },
        {
            "role": "user",
            "content": text
        }
    ]
}
    res = requests.post(url, headers=headers, json=data)

    print(res.status_code)
    print(res.text)

    if res.status_code != 200:
        return "AI xatolik (API ishlamadi)"

    return res.json()["choices"][0]["message"]["content"]

@bot.message_handler(func=lambda message: True)
def handle(message):
    try:
        reply = ask_ai(message.text)
        bot.reply_to(message, reply)
    except:
        bot.reply_to(message, "Xatolik 😕")

print("BOT STARTED")
bot.polling(none_stop=True)
