import telebot
import requests
import os
from telebot import types
from openai import OpenAI

# ---------------- ENV KEYS ----------------
TOKEN = os.getenv("TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
OCR_API_KEY = os.getenv("OCR_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not TOKEN or not GROQ_API_KEY:
    print("TOKEN yoki GROQ_API_KEY yo‘q!")
    exit()

bot = telebot.TeleBot(TOKEN)
client = OpenAI(api_key=OPENAI_API_KEY)

user_memory = {}

# ---------------- AI CHAT (GROQ) ----------------
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
                "content": "Sen o‘zbek tilida aniq va foydali javob berasan."
            },
            {
                "role": "user",
                "content": str(user_memory[user_id]) + "\nSavol: " + text
            }
        ],
        "temperature": 0.2
    }

    try:
        bot.send_chat_action(message.chat.id, "typing")
        res = requests.post(url, headers=headers, json=data, timeout=20)

        if res.status_code != 200:
            return "AI xatolik 😔"

        return res.json()["choices"][0]["message"]["content"]

    except Exception as e:
        print(e)
        return "Ulanish xatoligi 😔"


# ---------------- OCR ----------------
def ocr_space_image(image_path):
    url = "https://api.ocr.space/parse/image"

    try:
        with open(image_path, "rb") as f:
            response = requests.post(
                url,
                files={"file": f},
                data={"apikey": OCR_API_KEY, "language": "eng"}
            )

        result = response.json()
        return result["ParsedResults"][0]["ParsedText"]

    except Exception as e:
        print("OCR ERROR:", e)
        return ""


# ---------------- OPENAI IMAGE EDIT ----------------
def edit_image_openai(image_path, prompt):
    try:
        with open(image_path, "rb") as img:
            result = client.images.edits.create(
                model="gpt-image-1",
                image=img,
                prompt=prompt,
                size="1024x1024"
            )

        return result.data[0].url

    except Exception as e:
        print("OPENAI IMAGE ERROR:", e)
        return None


# ---------------- START ----------------
@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    markup.add(
        types.KeyboardButton("🤖 AI chat"),
        types.KeyboardButton("📷 Rasm yuborish")
    )
    markup.add(
        types.KeyboardButton("ℹ️ Yordam")
    )

    bot.send_message(
        message.chat.id,
        "👋 Salom!\nMen AI botman 🤖\nTanlang:",
        reply_markup=markup
    )


# ---------------- HELP ----------------
@bot.message_handler(func=lambda m: m.text == "ℹ️ Yordam")
def help_cmd(message):
    bot.send_message(
        message.chat.id,
        "📌 AI chat yoki rasm yuboring 📷\nMen uni tahlil qilib yoki o‘zgartirib beraman 🤖"
    )


# ---------------- AI MODE ----------------
@bot.message_handler(func=lambda m: m.text == "🤖 AI chat")
def ai_mode(message):
    bot.send_message(message.chat.id, "✍️ Savol yozing")


# ---------------- TEXT HANDLER ----------------
@bot.message_handler(func=lambda m: True)
def handle_text(message):
    reply = ask_ai(message, message.text)
    bot.send_message(message.chat.id, reply)


# ---------------- IMAGE HANDLER ----------------
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    try:
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)

        image_path = "image.jpg"
        with open(image_path, "wb") as f:
            f.write(downloaded_file)

        bot.send_message(message.chat.id, "📷 Rasm qabul qilindi...")

        prompt = message.caption if message.caption else "Rasmni chiroyli va zamonaviy qilib qayta ishlash"

        # OCR + AI EDIT
        text = ocr_space_image(image_path)

        if text.strip():
            bot.send_message(message.chat.id, f"📄 Matn: {text}")

        edited_url = edit_image_openai(image_path, prompt)

        if not edited_url:
            bot.send_message(message.chat.id, "❌ Rasmni o‘zgartirib bo‘lmadi")
            return

        bot.send_photo(message.chat.id, edited_url, caption="✨ AI tahrir qildi")

    except Exception as e:
        print("ERROR:", e)
        bot.send_message(message.chat.id, "Xatolik 😔")


print("BOT STARTED 🚀")
bot.infinity_polling()
