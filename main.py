import telebot
import requests
import os
from telebot import types

TOKEN = os.getenv("TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
OCR_API_KEY = os.getenv("OCR_API_KEY")

if not TOKEN or not GROQ_API_KEY:
    print("TOKEN yoki GROQ_API_KEY yo‘q!")
    exit()

bot = telebot.TeleBot(TOKEN)

user_memory = {}

# ---------------- AI ----------------
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
                "content": "Sen o‘zbek tilida aniq, tushunarli va foydali javob beradigan Ilmiy assistent AI assistantsan va har bir berayotgan javobin anniqlikda ozbek zo'zlari bo'lishi kerak chalkashliklar xatolar qilmaysan va har bir suxbatda o'zingni suxbatlashish xususiyatingni yuksaltirib yangi so'zlar va gaplar o'rganasan."
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
        return "Miyyam ishlamay qoldi 😔"

# ---------------- OCR ----------------
def ocr_space_image(image_path):
    url = "https://api.ocr.space/parse/image"

    try:
        with open(image_path, "rb") as f:
            response = requests.post(
                url,
                files={"file": f},
                data={"apikey": OCR_API_KEY, "language": "uzb"}
            )

        result = response.json()

        return result["ParsedResults"][0]["ParsedText"]

    except Exception as e:
        print("OCR ERROR:", e)
        return ""

# ---------------- START MENU (UI DESIGN) ----------------
@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    markup.add(
        types.KeyboardButton("🤖 keling biroz suxbatlashamiz"),
        types.KeyboardButton("📷 Rasm yuborish")
    )
    markup.add(
        types.KeyboardButton("ℹ️ Yordam"),
        types.KeyboardButton("⚙️ Sozlamalar")
    )

    bot.send_message(
        message.chat.id,
        "👋 <b>Salom!</b>\nMen <b>Zakirovning JR Assistent botiman 🤖</b>\n\nQuyidan tanla:",
        reply_markup=markup,
        parse_mode="HTML"
    )

# ---------------- HELP ----------------
@bot.message_handler(func=lambda m: m.text == "ℹ️ Yordam")
def help_cmd(message):
    bot.send_message(
        message.chat.id,
        "📌 Menga savol yozing yoki rasm yuboring 📷\nMen javob beraman 🤖"
    )

# ---------------- AI MODE ----------------
@bot.message_handler(func=lambda m: m.text == "🤖 AI chat")
def ai_mode(message):
    bot.send_message(message.chat.id, "✍️ Endi savol yozing 😎")

# ---------------- IMAGE MODE INFO ----------------
@bot.message_handler(func=lambda m: m.text == "📷 Rasm yuborish")
def photo_info(message):
    bot.send_message(message.chat.id, "📸 Menga rasm yuboring, men uni o‘qib beraman 🤖")

# ---------------- TEXT ----------------
@bot.message_handler(func=lambda m: True)
def handle(message):
    reply = ask_ai(message, message.text)
    bot.send_message(message.chat.id, f"✨ {reply}")

# ---------------- IMAGE / VISION ----------------
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    try:
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)

        image_path = "image.jpg"
        with open(image_path, "wb") as f:
            f.write(downloaded_file)

        bot.send_message(message.chat.id, "📷 Rasm olindi... tahlil qilinyapti")

        text = ocr_space_image(image_path)

        if not text.strip():
            bot.send_message(message.chat.id, "😕 Rasmni o'qishga aqlim yetmadi uzir")
            return

        bot.send_message(message.chat.id, f"📄 O‘qilgan matn:\n{text}")

        reply = ask_ai(
            message,
            "Bu matnni tushuntir yoki masala bo‘lsa yech:\n" + text
        )

        bot.send_message(message.chat.id, f"🧠 {reply}")

    except Exception as e:
        print("VISION ERROR:", e)
        bot.send_message(message.chat.id, "Rasmni tahlil qilib bo‘lmadi 😔")

print("BOT STARTED 🚀")
bot.infinity_polling()
